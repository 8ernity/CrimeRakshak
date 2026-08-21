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
)
from app.investigation_ai.schemas import BoundingBox, DetectionResponse


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


def link_media_to_fir(
    db: Session,
    media_id: int,
    fir_id: str,
    user: User,
    ip_address: Optional[str] = None,
) -> InvestigationMedia:
    media = get_media_by_id(db, media_id)
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

        formatted_detections = get_media_detections(db, media.media_id)
        return {
            "media": media,
            "job": job,
            "image_width": results.get("image_width", 0),
            "image_height": results.get("image_height", 0),
            "total_detected_objects": results.get("total_objects", 0),
            "detections": formatted_detections,
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        media.status = "failed"
        db.commit()
        raise AppHTTPException(
            status_code=500,
            code="image_processing_failed",
            detail=f"Image analysis failed: {str(e)}",
        )


def analyze_video_media(
    db: Session,
    media_id: int,
    user: User,
    sample_rate_fps: Optional[int] = None,
    conf_threshold: Optional[float] = None,
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
    job = create_analysis_job(db=db, media_id=media.media_id, user=user, job_type="video_detection", ip_address=ip_address)

    try:
        from app.investigation_ai.processors.video_processor import VideoProcessor
        processor = VideoProcessor(conf_threshold=conf_threshold)
        
        def update_job_progress(curr_frame: int, tot_frames: int, pct: float):
            job.progress_pct = pct
            db.commit()

        results = processor.process_video(
            video_path=media.file_path,
            sample_rate_fps=rate_fps,
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
                tracking_id=None,
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

        formatted_detections = get_media_detections(db, media.media_id)
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
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        media.status = "failed"
        db.commit()
        raise AppHTTPException(
            status_code=500,
            code="video_processing_failed",
            detail=f"Video analysis failed: {str(e)}",
        )


