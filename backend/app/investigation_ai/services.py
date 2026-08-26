"""Service layer for AI Video & Image Investigation Support."""
import hashlib
import os
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppHTTPException
from app.models.rbac import User
from app.services import audit
from app.investigation_ai.models import (
    InvestigationMedia,
    InvestigationAnalysisJob,
    DetectionResult,
    InvestigationEvent,
    InvestigationCrimeDecision,
)
from app.core import security
from app.investigation_ai.schemas import BoundingBox, DetectionResponse, InvestigationMediaResponse, CrimeDecisionResponse


def to_media_response(media: InvestigationMedia, user: Optional[User] = None) -> InvestigationMediaResponse:
    res = InvestigationMediaResponse.model_validate(media)
    user_id = user.user_id if user else (media.uploaded_by_user_id or 1)
    token, _ = security.create_media_access_token(subject=user_id, media_id=media.media_id)
    res.media_url = f"{settings.API_V1_PREFIX}/investigation/media/{media.media_id}/file?media_token={token}"
    return res


def verify_media_access(
    db: Session,
    media_id: int,
    media_token: Optional[str] = None,
    authorization_header: Optional[str] = None,
) -> User:
    media = get_media_by_id(db, media_id)
    user: Optional[User] = None

    # 1. Try single-purpose media_token
    if media_token:
        try:
            payload = security.decode_token(media_token, expected_type=security.MEDIA_ACCESS_TOKEN_TYPE)
            token_media_id = payload.get("media_id")
            if token_media_id != media_id:
                raise AppHTTPException(
                    status_code=403,
                    code="media_token_mismatch",
                    detail="Media access token is not valid for this specific media item.",
                )
            user_id = int(payload.get("sub", 0))
            if user_id > 0:
                user = db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
        except AppHTTPException:
            raise
        except Exception:
            # media_token invalid — fall through to other auth methods
            pass

    # 2. Try Bearer header
    if not user and authorization_header and authorization_header.startswith("Bearer "):
        bearer_token = authorization_header.split(" ")[1]
        # Try internal JWT
        try:
            payload = security.decode_token(bearer_token, expected_type=security.ACCESS_TOKEN_TYPE)
            user_id = int(payload.get("sub", 0))
            if user_id > 0:
                user = db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
        except Exception:
            pass
        # Try Clerk JWT (RS256)
        if not user:
            try:
                import httpx
                from jose import jwt as jose_jwt
                resp = httpx.get("https://api.clerk.dev/v1/jwks", timeout=5)
                if resp.status_code == 200:
                    jwks_data = resp.json()
                    unverified_header = jose_jwt.get_unverified_header(bearer_token)
                    kid = unverified_header.get("kid")
                    key = next((k for k in jwks_data.get("keys", []) if k.get("kid") == kid), None)
                    if key:
                        claims = jose_jwt.decode(bearer_token, {"keys": [key]}, algorithms=["RS256"], options={"verify_aud": False})
                        if claims.get("sub"):
                            user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
            except Exception:
                pass

    # 3. Fallback to dev admin
    if not user:
        dev_user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if dev_user:
            user = dev_user
        else:
            raise AppHTTPException(
                status_code=401,
                code="authentication_required",
                detail="Valid media_token or Authorization Bearer token is required.",
            )

    # 4. RBAC & District Scoping Check
    if not user.is_superuser and user.district_id and media.district_id and media.district_id != user.district_id:
        raise AppHTTPException(
            status_code=403,
            code="district_access_forbidden",
            detail="Access forbidden: Evidence media belongs to a different district.",
        )

    return user




def _ensure_storage_dirs():
    os.makedirs(settings.INVESTIGATION_UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.INVESTIGATION_PROCESSED_DIR, exist_ok=True)


def _compute_sha256(file_obj) -> str:
    hasher = hashlib.sha256()
    file_obj.seek(0)
    while chunk := file_obj.read(8192):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def _get_media_metadata(file_path: str, ext: str) -> Tuple[str, Optional[float], Optional[float], Optional[int]]:
    """Determine file_type ("image" or "video") and extract basic duration/fps/frames metadata."""
    ext = ext.lower()
    if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        return "image", None, None, None

    if ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        duration_sec, fps, total_frames = None, None, None
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                if fps > 0 and total_frames > 0:
                    duration_sec = total_frames / fps
                cap.release()
        except Exception:
            pass
        return "video", duration_sec, fps, total_frames

    raise AppHTTPException(
        status_code=400,
        code="unsupported_file_type",
        detail=f"File extension '{ext}' is not supported for investigation analysis.",
    )


def save_uploaded_media(
    db: Session,
    file: UploadFile,
    user: User,
    district_id: Optional[int] = None,
    fir_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> InvestigationMedia:
    _ensure_storage_dirs()

    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = set(settings.ALLOWED_IMAGE_EXTENSIONS + settings.ALLOWED_VIDEO_EXTENSIONS)
    if ext not in allowed_exts:
        raise AppHTTPException(
            status_code=400,
            code="invalid_extension",
            detail=f"Unsupported file format '{ext}'. Allowed: {sorted(list(allowed_exts))}",
        )

    file_hash = _compute_sha256(file.file)
    
    # Save file securely to storage directory
    safe_filename = f"{file_hash[:16]}_{os.path.basename(file.filename)}"
    dest_path = os.path.join(settings.INVESTIGATION_UPLOAD_DIR, safe_filename)

    file.file.seek(0)
    content = file.file.read()
    size_bytes = len(content)

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise AppHTTPException(
            status_code=400,
            code="file_too_large",
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    file_type, duration_seconds, fps, total_frames = _get_media_metadata(dest_path, ext)

    media = InvestigationMedia(
        file_name=file.filename,
        file_path=dest_path,
        file_type=file_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=size_bytes,
        sha256_hash=file_hash,
        duration_seconds=duration_seconds,
        fps=fps,
        total_frames=total_frames,
        district_id=district_id or user.district_id,
        fir_id=fir_id,
        uploaded_by_user_id=user.user_id,
        status="uploaded",
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    audit.record(
        db,
        action="investigation.upload",
        user_id=user.user_id,
        resource=f"media:{media.media_id}",
        ip_address=ip_address,
        detail={
            "file_name": file.filename,
            "sha256": file_hash,
            "size_bytes": size_bytes,
            "file_type": file_type,
        },
    )
    return media


def list_media(
    db: Session,
    district_id: Optional[int] = None,
    fir_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[InvestigationMedia], int]:
    stmt = select(InvestigationMedia)
    if district_id:
        stmt = stmt.where(InvestigationMedia.district_id == district_id)
    if fir_id:
        stmt = stmt.where(InvestigationMedia.fir_id == fir_id)

    total = len(db.execute(stmt).scalars().all())
    items = db.execute(stmt.order_by(InvestigationMedia.upload_timestamp.desc()).offset(offset).limit(limit)).scalars().all()
    return items, total


def get_media_by_id(db: Session, media_id: int) -> InvestigationMedia:
    media = db.execute(select(InvestigationMedia).where(InvestigationMedia.media_id == media_id)).scalar_one_or_none()
    if not media:
        raise AppHTTPException(status_code=404, code="not_found", detail=f"Investigation media '{media_id}' not found.")
    return media


def create_analysis_job(
    db: Session,
    media_id: int,
    user: User,
    job_type: str = "full_analysis",
    ip_address: Optional[str] = None,
) -> InvestigationAnalysisJob:
    media = get_media_by_id(db, media_id)
    
    job = InvestigationAnalysisJob(
        media_id=media.media_id,
        job_type=job_type,
        status="queued",
        progress_pct=0.0,
        started_at=datetime.utcnow(),
    )
    db.add(job)
    media.status = "processing"
    db.commit()
    db.refresh(job)

    audit.record(
        db,
        action="investigation.process_start",
        user_id=user.user_id,
        resource=f"job:{job.job_id}",
        ip_address=ip_address,
        detail={"media_id": media.media_id, "job_type": job_type},
    )
    return job


def get_job_by_id(db: Session, job_id: int) -> InvestigationAnalysisJob:
    job = db.execute(select(InvestigationAnalysisJob).where(InvestigationAnalysisJob.job_id == job_id)).scalar_one_or_none()
    if not job:
        raise AppHTTPException(status_code=404, code="not_found", detail=f"Analysis job '{job_id}' not found.")
    return job


def get_media_detections(db: Session, media_id: int) -> List[DetectionResponse]:
    media = get_media_by_id(db, media_id)
    raw_detections = db.execute(
        select(DetectionResult).where(DetectionResult.media_id == media.media_id).order_by(DetectionResult.frame_number.asc())
    ).scalars().all()

    result = []
    for d in raw_detections:
        result.append(
            DetectionResponse(
                detection_id=d.detection_id,
                job_id=d.job_id,
                media_id=d.media_id,
                frame_number=d.frame_number,
                timestamp_seconds=d.timestamp_seconds,
                object_class=d.object_class,
                tracking_id=d.tracking_id,
                confidence=d.confidence,
                bbox=BoundingBox(
                    xmin=d.bbox_xmin,
                    ymin=d.bbox_ymin,
                    xmax=d.bbox_xmax,
                    ymax=d.bbox_ymax,
                ),
                crop_image_path=d.crop_image_path,
            )
        )
    return result


def get_media_events(db: Session, media_id: int) -> List[InvestigationEvent]:
    media = get_media_by_id(db, media_id)
    return db.execute(
        select(InvestigationEvent).where(InvestigationEvent.media_id == media.media_id).order_by(InvestigationEvent.start_timestamp_seconds.asc())
    ).scalars().all()


def extract_events_for_media(
    db: Session,
    media_id: int,
    user: User,
    job_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> List[InvestigationEvent]:
    media = get_media_by_id(db, media_id)

    # Fetch detections for media
    raw_detections = db.execute(
        select(DetectionResult).where(DetectionResult.media_id == media.media_id).order_by(DetectionResult.frame_number.asc())
    ).scalars().all()

    detections_dict = []
    for d in raw_detections:
        detections_dict.append({
            "detection_id": d.detection_id,
            "frame_number": d.frame_number,
            "timestamp_seconds": d.timestamp_seconds,
            "object_class": d.object_class,
            "tracking_id": d.tracking_id,
            "confidence": d.confidence,
            "bbox": {
                "xmin": d.bbox_xmin,
                "ymin": d.bbox_ymin,
                "xmax": d.bbox_xmax,
                "ymax": d.bbox_ymax,
            },
        })

    from app.investigation_ai.processors.event_extractor import EventExtractor
    extractor = EventExtractor()
    extracted_events = extractor.extract_events(detections_dict, media_id=media.media_id, total_frames=media.total_frames)

    # Delete previous events for clean re-extraction if job_id specified
    if job_id:
        target_job_id = job_id
    else:
        latest_job = db.execute(
            select(InvestigationAnalysisJob).where(InvestigationAnalysisJob.media_id == media.media_id).order_by(InvestigationAnalysisJob.created_at.desc())
        ).scalars().first()
        target_job_id = latest_job.job_id if latest_job else 0

    event_models = []
    for ev in extracted_events:
        event_rec = InvestigationEvent(
            job_id=target_job_id,
            media_id=media.media_id,
            event_type=ev["event_type"],
            description=ev["description"],
            start_timestamp_seconds=ev["timestamp_seconds"],
            end_timestamp_seconds=ev["timestamp_seconds"],
            frame_start=ev["frame_number"],
            frame_end=ev["frame_number"],
            tracking_id=ev.get("tracking_id"),
            confidence=ev.get("confidence"),
            linked_fir_id=media.fir_id,
        )
        db.add(event_rec)
        event_models.append(event_rec)

    db.commit()
    audit.record(
        db,
        action="investigation.extract_events",
        user_id=user.user_id,
        resource=f"media:{media.media_id}",
        ip_address=ip_address,
        detail={"extracted_count": len(event_models)},
    )

    # Automatically run CrimeDecisionEngine after event extraction
    try:
        evaluate_and_save_crime_decision(db=db, media_id=media.media_id, user=user, job_id=target_job_id)
    except Exception as dec_err:
        logger.warning(f"Automatic crime decision evaluation failed for media {media.media_id}: {dec_err}")

    return event_models


def evaluate_and_save_crime_decision(
    db: Session,
    media_id: int,
    user: User,
    job_id: Optional[int] = None,
) -> InvestigationCrimeDecision:
    """Run CrimeDecisionEngine over media's detections & events and persist decision."""
    import json
    from app.investigation_ai.processors.crime_decision_engine import CrimeDecisionEngine

    media = get_media_by_id(db, media_id)
    detections = get_media_detections(db, media_id)
    events = get_media_events(db, media_id)

    dets_dict = []
    for d in detections:
        if hasattr(d, "bbox"):
            b = d.bbox
            b_dict = {
                "xmin": b.xmin if hasattr(b, "xmin") else b.get("xmin", 0.0),
                "ymin": b.ymin if hasattr(b, "ymin") else b.get("ymin", 0.0),
                "xmax": b.xmax if hasattr(b, "xmax") else b.get("xmax", 0.0),
                "ymax": b.ymax if hasattr(b, "ymax") else b.get("ymax", 0.0),
            }
            dets_dict.append({
                "frame_number": getattr(d, "frame_number", 0),
                "timestamp_seconds": getattr(d, "timestamp_seconds", 0.0),
                "object_class": getattr(d, "object_class", ""),
                "tracking_id": getattr(d, "tracking_id", None),
                "confidence": getattr(d, "confidence", 0.0),
                "bbox": b_dict,
            })
        else:
            dets_dict.append({
                "frame_number": d.get("frame_number", 0),
                "timestamp_seconds": d.get("timestamp_seconds", 0.0),
                "object_class": d.get("object_class", ""),
                "tracking_id": d.get("tracking_id"),
                "confidence": d.get("confidence", 0.0),
                "bbox": d.get("bbox", {}),
            })

    evts_dict = []
    for e in events:
        if hasattr(e, "event_type"):
            evts_dict.append({
                "event_type": getattr(e, "event_type", ""),
                "description": getattr(e, "description", ""),
                "timestamp_seconds": getattr(e, "start_timestamp_seconds", getattr(e, "timestamp_seconds", 0.0)),
                "frame_number": getattr(e, "frame_start", getattr(e, "frame_number", 0)),
                "tracking_id": getattr(e, "tracking_id", None),
                "confidence": getattr(e, "confidence", 0.0),
            })
        else:
            evts_dict.append({
                "event_type": e.get("event_type", ""),
                "description": e.get("description", ""),
                "timestamp_seconds": e.get("start_timestamp_seconds", e.get("timestamp_seconds", 0.0)),
                "frame_number": e.get("frame_start", e.get("frame_number", 0)),
                "tracking_id": e.get("tracking_id"),
                "confidence": e.get("confidence", 0.0),
            })

    engine = CrimeDecisionEngine()
    is_video = (media.file_type == "video")
    decision_res = engine.evaluate_decision(
        detections=dets_dict,
        events=evts_dict,
        is_video=is_video,
        media_id=media.media_id,
    )

    # Delete previous decision if existing
    existing = db.execute(
        select(InvestigationCrimeDecision).where(InvestigationCrimeDecision.media_id == media_id)
    ).scalars().first()
    if existing:
        db.delete(existing)
        db.commit()

    decision_rec = InvestigationCrimeDecision(
        media_id=media_id,
        job_id=job_id,
        decision=decision_res["decision"],
        confidence=decision_res["confidence"],
        evidence_score=decision_res["evidence_score"],
        reasons=decision_res["rationale"],
        evidence_events=json.dumps(decision_res["primary_triggers"]),
        timestamps=json.dumps(decision_res["timestamps"]),
        track_ids=json.dumps(decision_res["track_ids"]),
        safeguards_triggered=json.dumps(decision_res["safeguards_triggered"]),
        is_video=is_video,
    )
    db.add(decision_rec)
    db.commit()
    db.refresh(decision_rec)
    return decision_rec


def get_crime_decision(
    db: Session,
    media_id: int,
    user: User,
) -> CrimeDecisionResponse:
    """Retrieve existing Crime Decision for media, or evaluate if not present."""
    import json
    media = get_media_by_id(db, media_id)
    decision_orm = db.execute(
        select(InvestigationCrimeDecision).where(InvestigationCrimeDecision.media_id == media_id)
    ).scalars().first()

    if not decision_orm:
        decision_orm = evaluate_and_save_crime_decision(db, media_id, user)

    def parse_json(val: Optional[str]):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    return CrimeDecisionResponse(
        media_id=decision_orm.media_id,
        decision=decision_orm.decision,
        status=decision_orm.decision,  # Alias
        confidence=decision_orm.confidence,
        evidence_score=decision_orm.evidence_score,
        reasons=decision_orm.reasons,
        evidence_events=parse_json(decision_orm.evidence_events),
        timestamps=parse_json(decision_orm.timestamps),
        track_ids=parse_json(decision_orm.track_ids),
        safeguards_triggered=parse_json(decision_orm.safeguards_triggered),
        is_video=decision_orm.is_video,
        created_at=decision_orm.created_at,
    )


def get_crime_video_detection(
    db: Session,
    media_id: int,
    user: User,
) -> dict:
    """Run CrimeDetectionAnalyzer over media's existing detections & events."""
    from app.investigation_ai.processors.crime_detection_analyzer import CrimeDetectionAnalyzer

    media = get_media_by_id(db, media_id)
    detections_raw = get_media_detections(db, media_id)
    events_raw = get_media_events(db, media_id)

    dets_dict = []
    for d in detections_raw:
        dets_dict.append({
            "frame_number": getattr(d, "frame_number", 0),
            "timestamp_seconds": getattr(d, "timestamp_seconds", 0.0),
            "object_class": getattr(d, "object_class", ""),
            "tracking_id": getattr(d, "tracking_id", None),
            "confidence": getattr(d, "confidence", 0.0),
            "posture": getattr(d, "posture", None),
        })

    evts_dict = []
    for e in events_raw:
        evts_dict.append({
            "event_type": getattr(e, "event_type", ""),
            "description": getattr(e, "description", ""),
            "timestamp_seconds": getattr(e, "start_timestamp_seconds", getattr(e, "timestamp_seconds", 0.0)),
            "start_timestamp_seconds": getattr(e, "start_timestamp_seconds", 0.0),
            "end_timestamp_seconds": getattr(e, "end_timestamp_seconds", 0.0),
            "tracking_id": getattr(e, "tracking_id", None),
            "confidence": getattr(e, "confidence", 0.0),
        })

    analyzer = CrimeDetectionAnalyzer()
    return analyzer.analyze_video_evidence(
        detections=dets_dict,
        events=evts_dict,
        is_video=(media.file_type == "video"),
        media_id=media.media_id,
    )



def link_media_to_fir(
    db: Session,
    media_id: int,
    fir_id: Optional[str],
    user: User,
    ip_address: Optional[str] = None,
) -> InvestigationMedia:
    media = get_media_by_id(db, media_id)
    if not user.is_superuser and user.district_id and media.district_id and media.district_id != user.district_id:
        raise AppHTTPException(
            status_code=403,
            code="district_access_forbidden",
            detail="Access forbidden: Cannot link media belonging to a different district.",
        )
    media.fir_id = fir_id
    db.commit()
    db.refresh(media)

    audit.record(
        db,
        action="investigation.link_fir",
        user_id=user.user_id,
        resource=f"media:{media.media_id}",
        ip_address=ip_address,
        detail={"fir_id": fir_id},
    )
    return media


def get_case_media(
    db: Session,
    fir_id: str,
    user: User,
) -> dict:
    stmt = select(InvestigationMedia).where(InvestigationMedia.fir_id == fir_id)
    if not user.is_superuser and user.district_id:
        stmt = stmt.where(InvestigationMedia.district_id == user.district_id)

    media_list = db.execute(stmt.order_by(InvestigationMedia.upload_timestamp.desc())).scalars().all()
    media_ids = [m.media_id for m in media_list]

    total_dets = 0
    total_evts = 0
    if media_ids:
        total_dets = len(
            db.execute(select(DetectionResult).where(DetectionResult.media_id.in_(media_ids))).scalars().all()
        )
        total_evts = len(
            db.execute(select(InvestigationEvent).where(InvestigationEvent.media_id.in_(media_ids))).scalars().all()
        )

    formatted_media = [to_media_response(m, user) for m in media_list]
    effective_district = user.district_id if not user.is_superuser else (media_list[0].district_id if media_list else None)

    return {
        "fir_id": fir_id,
        "district_id": effective_district,
        "total_media": len(formatted_media),
        "media_items": formatted_media,
        "total_detections": total_dets,
        "total_events": total_evts,
    }



def analyze_image_media(
    db: Session,
    media_id: int,
    user: User,
    conf_threshold: Optional[float] = None,
    ip_address: Optional[str] = None,
) -> dict:
    media = get_media_by_id(db, media_id)
    if media.file_type != "image":
        raise AppHTTPException(
            status_code=400,
            code="invalid_media_type",
            detail=f"Media ID '{media_id}' is a {media.file_type}, not an image. Use video processing endpoint for videos.",
        )

    job = create_analysis_job(db=db, media_id=media.media_id, user=user, job_type="image_detection", ip_address=ip_address)

    try:
        from app.investigation_ai.processors.image_processor import ImageProcessor
        processor = ImageProcessor(conf_threshold=conf_threshold)
        results = processor.process_image(media.file_path)

        detections_orm = []
        for det in results.get("detections", []):
            bbox = det["bbox"]
            detection_rec = DetectionResult(
                job_id=job.job_id,
                media_id=media.media_id,
                frame_number=0,
                timestamp_seconds=0.0,
                object_class=det["object_class"],
                tracking_id=None,
                confidence=det["confidence"],
                bbox_xmin=bbox["xmin"],
                bbox_ymin=bbox["ymin"],
                bbox_xmax=bbox["xmax"],
                bbox_ymax=bbox["ymax"],
            )
            db.add(detection_rec)
            detections_orm.append(detection_rec)

        job.status = "completed"
        job.progress_pct = 100.0
        job.completed_at = datetime.utcnow()
        media.status = "processed"
        db.commit()
        db.refresh(job)
        db.refresh(media)

        audit.record(
            db,
            action="investigation.image_analysis",
            user_id=user.user_id,
            resource=f"media:{media.media_id}",
            ip_address=ip_address,
            detail={
                "job_id": job.job_id,
                "total_objects": results.get("total_objects", 0),
                "conf_threshold": conf_threshold or settings.CONFIDENCE_THRESHOLD,
            },
        )

        # Trigger automatic event extraction & crime decision evaluation
        try:
            extract_events_for_media(db=db, media_id=media.media_id, user=user, job_id=job.job_id, ip_address=ip_address)
        except Exception as ev_err:
            logger.warning(f"Automatic event extraction failed for media {media.media_id}: {ev_err}")

        formatted_detections = get_media_detections(db, media.media_id)
        decision_resp = None
        try:
            decision_resp = get_crime_decision(db=db, media_id=media.media_id, user=user)
        except Exception as dec_err:
            logger.warning(f"Failed to fetch crime decision for image media {media.media_id}: {dec_err}")

        return {
            "media": media,
            "job": job,
            "image_width": results.get("image_width", 0),
            "image_height": results.get("image_height", 0),
            "total_detected_objects": results.get("total_objects", 0),
            "detections": formatted_detections,
            "crime_decision": decision_resp,
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        media.status = "failed"
        db.commit()
        db.refresh(job)
        db.refresh(media)
        return {
            "media": media,
            "job": job,
            "image_width": 0,
            "image_height": 0,
            "total_detected_objects": 0,
            "detections": [],
        }


def analyze_video_media(
    db: Session,
    media_id: int,
    user: User,
    sample_rate_fps: Optional[int] = None,
    conf_threshold: Optional[float] = None,
    tracker_type: Optional[str] = "bytetrack",
    ip_address: Optional[str] = None,
) -> dict:
    media = get_media_by_id(db, media_id)
    if media.file_type != "video":
        raise AppHTTPException(
            status_code=400,
            code="invalid_media_type",
            detail=f"Media ID '{media_id}' is a {media.file_type}, not a video. Use image processing endpoint for images.",
        )

    rate_fps = sample_rate_fps if sample_rate_fps is not None and sample_rate_fps > 0 else settings.FRAME_SAMPLE_RATE
    selected_tracker = tracker_type if tracker_type else "bytetrack"
    job = create_analysis_job(db=db, media_id=media.media_id, user=user, job_type="video_tracking", ip_address=ip_address)

    try:
        from app.investigation_ai.processors.video_processor import VideoProcessor
        processor = VideoProcessor(conf_threshold=conf_threshold)
        
        def update_job_progress(curr_frame: int, tot_frames: int, pct: float):
            job.progress_pct = pct
            db.commit()

        results = processor.process_video(
            video_path=media.file_path,
            sample_rate_fps=rate_fps,
            tracker_type=selected_tracker,
            progress_callback=update_job_progress,
        )

        detections_orm = []
        for det in results.get("detections", []):
            bbox = det["bbox"]
            detection_rec = DetectionResult(
                job_id=job.job_id,
                media_id=media.media_id,
                frame_number=det["frame_number"],
                timestamp_seconds=det["timestamp_seconds"],
                object_class=det["object_class"],
                tracking_id=det.get("tracking_id"),
                confidence=det["confidence"],
                bbox_xmin=bbox["xmin"],
                bbox_ymin=bbox["ymin"],
                bbox_xmax=bbox["xmax"],
                bbox_ymax=bbox["ymax"],
            )
            db.add(detection_rec)
            detections_orm.append(detection_rec)

        # Update media metadata
        media.fps = results.get("fps")
        media.total_frames = results.get("total_frames")
        media.duration_seconds = results.get("duration_seconds")
        media.status = "processed"

        job.status = "completed"
        job.progress_pct = 100.0
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        db.refresh(media)

        audit.record(
            db,
            action="investigation.video_analysis",
            user_id=user.user_id,
            resource=f"media:{media.media_id}",
            ip_address=ip_address,
            detail={
                "job_id": job.job_id,
                "sample_rate_fps": rate_fps,
                "total_objects": results.get("total_detected_objects", 0),
                "sampled_frames_count": results.get("sampled_frames_count", 0),
                "conf_threshold": conf_threshold or settings.CONFIDENCE_THRESHOLD,
            },
        )

        # Trigger automatic event extraction
        try:
            extract_events_for_media(db=db, media_id=media.media_id, user=user, job_id=job.job_id, ip_address=ip_address)
        except Exception as ev_err:
            logger.warning(f"Automatic event extraction failed for media {media.media_id}: {ev_err}")

        formatted_detections = get_media_detections(db, media.media_id)
        decision_resp = None
        try:
            decision_resp = get_crime_decision(db=db, media_id=media.media_id, user=user)
        except Exception as dec_err:
            logger.warning(f"Failed to fetch crime decision for video media {media.media_id}: {dec_err}")

        video_meta = {
            "fps": results.get("fps", 0.0),
            "total_frames": results.get("total_frames", 0),
            "duration_seconds": results.get("duration_seconds", 0.0),
            "width": results.get("width", 0),
            "height": results.get("height", 0),
            "sample_rate_fps": rate_fps,
            "sampled_frames_count": results.get("sampled_frames_count", 0),
        }

        return {
            "media": media,
            "job": job,
            "video_metadata": video_meta,
            "total_detected_objects": results.get("total_detected_objects", 0),
            "detections": formatted_detections,
            "crime_decision": decision_resp,
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        media.status = "failed"
        db.commit()
        db.refresh(job)
        db.refresh(media)
        video_meta = {
            "fps": 0.0,
            "total_frames": 0,
            "duration_seconds": 0.0,
            "width": 0,
            "height": 0,
            "sample_rate_fps": rate_fps,
            "sampled_frames_count": 0,
        }
        return {
            "media": media,
            "job": job,
            "video_metadata": video_meta,
            "total_detected_objects": 0,
            "detections": [],
        }


def get_investigation_summary(
    db: Session,
    media_id: int,
    user: User,
    force_refresh: bool = False,
    ip_address: Optional[str] = None,
):
    """Retrieve existing or generate fresh LLM Investigation Summary for media."""
    import json
    from app.investigation_ai.summary_generator import get_or_create_investigation_summary
    from app.investigation_ai.schemas import SummaryResponse

    media = get_media_by_id(db, media_id)
    summary_orm = get_or_create_investigation_summary(
        db=db, media=media, user=user, force_refresh=force_refresh
    )

    def parse_json_list(val: Optional[str]) -> List[str]:
        if not val:
            return []
        try:
            res = json.loads(val)
            return res if isinstance(res, list) else [str(res)]
        except Exception:
            return [val]

    audit.record(
        db,
        action="investigation.summary_generated",
        user_id=user.user_id,
        resource=f"media:{media.media_id}",
        ip_address=ip_address,
        detail={"summary_id": summary_orm.summary_id, "provider": summary_orm.provider_used},
    )

    return SummaryResponse(
        summary_id=summary_orm.summary_id,
        media_id=summary_orm.media_id,
        job_id=summary_orm.job_id,
        summary_text=summary_orm.summary_text,
        observed_events=parse_json_list(summary_orm.observed_events),
        relevant_timestamps=parse_json_list(summary_orm.relevant_timestamps),
        detected_objects_summary=parse_json_list(summary_orm.detected_objects_summary),
        evidence_references=parse_json_list(summary_orm.evidence_references),
        uncertainty_limitations=parse_json_list(summary_orm.uncertainty_limitations),
        provider_used=summary_orm.provider_used,
        created_at=summary_orm.created_at,
    )


def get_ai_investigation_report(
    db: Session,
    media_id: int,
    user: User,
    force_refresh: bool = False,
    ip_address: Optional[str] = None,
) -> dict:
    """Generate or retrieve an AI Investigation Report for evidence media.

    Orchestrates:
      1. Structured evidence gathering (reuses summary_generator.build_structured_evidence)
      2. Crime detection analysis (reuses CrimeDetectionAnalyzer)
      3. Key frame extraction + multimodal LLM report generation
    """
    from app.investigation_ai.summary_generator import build_structured_evidence
    from app.investigation_ai.processors.crime_detection_analyzer import CrimeDetectionAnalyzer
    from app.investigation_ai.processors.report_generator import generate_ai_investigation_report

    media = get_media_by_id(db, media_id)
    is_video = media.file_type == "video"

    # 1. Build structured evidence (same as summary generator)
    structured_evidence = build_structured_evidence(db, media, user)

    # 2. Run crime detection analyzer
    dets_raw = get_media_detections(db, media_id)
    evts_raw = get_media_events(db, media_id)

    dets_dict = []
    for d in dets_raw:
        dets_dict.append({
            "frame_number": getattr(d, "frame_number", 0),
            "timestamp_seconds": getattr(d, "timestamp_seconds", 0.0),
            "object_class": getattr(d, "object_class", ""),
            "tracking_id": getattr(d, "tracking_id", None),
            "confidence": getattr(d, "confidence", 0.0),
            "posture": getattr(d, "posture", None),
        })

    evts_dict = []
    for e in evts_raw:
        evts_dict.append({
            "event_type": getattr(e, "event_type", ""),
            "description": getattr(e, "description", ""),
            "timestamp_seconds": getattr(e, "start_timestamp_seconds", getattr(e, "timestamp_seconds", 0.0)),
            "start_timestamp_seconds": getattr(e, "start_timestamp_seconds", 0.0),
            "end_timestamp_seconds": getattr(e, "end_timestamp_seconds", 0.0),
            "tracking_id": getattr(e, "tracking_id", None),
            "confidence": getattr(e, "confidence", 0.0),
        })

    analyzer = CrimeDetectionAnalyzer()
    crime_detection = analyzer.analyze_video_evidence(
        detections=dets_dict,
        events=evts_dict,
        is_video=is_video,
        media_id=media.media_id,
    )

    # 3. Generate AI Investigation Report
    report = generate_ai_investigation_report(
        structured_evidence=structured_evidence,
        crime_detection=crime_detection,
        media_file_path=media.file_path if hasattr(media, "file_path") else None,
        is_video=is_video,
        media_id=media.media_id,
    )

    report["media_id"] = media.media_id
    return report
