"""API Router for AI Video & Image Investigation Support."""
import os
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_client_ip, get_current_active_user, require_permissions
from app.core.exceptions import AppHTTPException
from app.models.rbac import User
from app.investigation_ai import services
from app.investigation_ai.schemas import (
    AIInvestigationReportResponse,
    AnalysisJobResponse,
    CaseMediaSummaryResponse,
    CrimeDecisionResponse,
    CrimeVideoDetectionResponse,
    DetectionListResponse,
    EventListResponse,
    GenerateSummaryRequest,
    ImageAnalysisResponse,
    InvestigationMediaListResponse,
    InvestigationMediaResponse,
    LinkFIRRequest,
    ProcessMediaRequest,
    SummaryResponse,
    VideoAnalysisResponse,
    VideoMetadata,
)

router = APIRouter(prefix="/investigation", tags=["investigation-ai"])


@router.post(
    "/upload",
    response_model=InvestigationMediaResponse,
    summary="Upload crime scene video or image media for investigation",
)
def upload_investigation_media(
    request: Request,
    file: UploadFile = File(...),
    district_id: Optional[int] = Form(None),
    fir_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InvestigationMediaResponse:
    media = services.save_uploaded_media(
        db=db,
        file=file,
        user=current_user,
        district_id=district_id,
        fir_id=fir_id,
        ip_address=get_client_ip(request),
    )
    return services.to_media_response(media, current_user)


@router.get(
    "/media",
    response_model=InvestigationMediaListResponse,
    summary="List uploaded investigation media items",
)
def list_investigation_media(
    district_id: Optional[int] = Query(None),
    fir_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InvestigationMediaListResponse:
    # Filter by user's assigned district if specified and user is not superuser
    effective_district = district_id
    if not current_user.is_superuser and current_user.district_id:
        effective_district = current_user.district_id

    items, total = services.list_media(
        db=db,
        district_id=effective_district,
        fir_id=fir_id,
        limit=limit,
        offset=offset,
    )
    return InvestigationMediaListResponse(
        items=[services.to_media_response(m, current_user) for m in items],
        total=total,
    )


@router.get(
    "/media/{media_id}",
    response_model=InvestigationMediaResponse,
    summary="Get single investigation media record details",
)
def get_investigation_media_details(
    media_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InvestigationMediaResponse:
    media = services.get_media_by_id(db, media_id)
    return services.to_media_response(media, current_user)


@router.get(
    "/media/{media_id}/file",
    summary="Stream or download investigation evidence media file",
)
def get_investigation_media_file(
    media_id: int,
    request: Request,
    media_token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    auth_header = request.headers.get("Authorization")
    user = services.verify_media_access(
        db=db,
        media_id=media_id,
        media_token=media_token,
        authorization_header=auth_header,
    )
    media = services.get_media_by_id(db, media_id)
    if not os.path.exists(media.file_path):
        raise AppHTTPException(
            status_code=404,
            code="file_not_found",
            detail=f"Media file for ID '{media_id}' not found on storage server.",
        )

    headers = {"Accept-Ranges": "bytes"}
    return FileResponse(
        path=media.file_path,
        media_type=media.mime_type,
        filename=media.file_name,
        headers=headers,
    )


def _run_analysis_background(media_id: int, job_id: int, user_id: int, file_type: str, sample_rate_fps: int, ip_address: str, job_type: str):
    """Run analysis in background, updating the pre-created job (job_id) directly."""
    db = SessionLocal()
    try:
        from app.investigation_ai.models import InvestigationAnalysisJob, InvestigationMedia
        from datetime import datetime

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return

        # Fetch the pre-created job and mark it as processing
        job = db.query(InvestigationAnalysisJob).filter(
            InvestigationAnalysisJob.job_id == job_id
        ).first()
        if not job:
            return
        job.status = "processing"
        db.commit()

        if file_type == "image":
            # Run detection directly instead of calling analyze_image_media
            # (which creates its own duplicate job)
            from app.investigation_ai.processors.image_processor import ImageProcessor
            media = services.get_media_by_id(db, media_id)
            processor = ImageProcessor()
            results = processor.process_image(media.file_path)

            for det in results.get("detections", []):
                bbox = det["bbox"]
                from app.investigation_ai.models import DetectionResult
                detection_rec = DetectionResult(
                    job_id=job.job_id,
                    media_id=media.media_id,
                    frame_number=0,
                    timestamp_seconds=0.0,
                    object_class=det["object_class"],
                    tracking_id=det.get("tracking_id"),
                    confidence=det["confidence"],
                    posture=det.get("posture"),
                    bbox_xmin=bbox["xmin"],
                    bbox_ymin=bbox["ymin"],
                    bbox_xmax=bbox["xmax"],
                    bbox_ymax=bbox["ymax"],
                )
                db.add(detection_rec)

            job.status = "completed"
            job.progress_pct = 100.0
            job.completed_at = datetime.utcnow()
            media.status = "processed"
            db.commit()

            # Trigger automatic event extraction & crime decision
            try:
                services.extract_events_for_media(db=db, media_id=media.media_id, user=user, job_id=job.job_id, ip_address=ip_address)
            except Exception as ev_err:
                print(f"Automatic event extraction failed for media {media.media_id}: {ev_err}")

        elif file_type == "video":
            services.analyze_video_media(
                db=db,
                media_id=media_id,
                user=user,
                sample_rate_fps=sample_rate_fps,
                ip_address=ip_address,
            )
            # Also mark the pre-created job as completed since analyze_video_media
            # creates its own job too
            db.refresh(job)
            if job.status == "processing":
                job.status = "completed"
                job.progress_pct = 100.0
                job.completed_at = datetime.utcnow()
                db.commit()

    except Exception as e:
        print(f"Background analysis failed: {e}")
        import traceback
        traceback.print_exc()
        from app.investigation_ai.models import InvestigationAnalysisJob, InvestigationMedia
        from sqlalchemy import update
        db.execute(
            update(InvestigationAnalysisJob)
            .where(InvestigationAnalysisJob.media_id == media_id)
            .where(InvestigationAnalysisJob.status.in_(["queued", "processing"]))
            .values(status="failed", error_message=str(e))
        )
        db.execute(
            update(InvestigationMedia)
            .where(InvestigationMedia.media_id == media_id)
            .where(InvestigationMedia.status.in_(["queued", "processing"]))
            .values(status="failed")
        )
        db.commit()
    finally:
        db.close()


@router.post(
    "/media/{media_id}/process",
    response_model=AnalysisJobResponse,
    summary="Trigger computer vision analysis job on uploaded media",
)
def process_investigation_media(
    media_id: int,
    payload: ProcessMediaRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    media = services.get_media_by_id(db, media_id)
    ip_address = get_client_ip(request)
    
    # We create the job initially so we can return its ID immediately
    job = services.create_analysis_job(
        db=db,
        media_id=media_id,
        user=current_user,
        job_type=payload.job_type,
        ip_address=ip_address,
    )
    
    background_tasks.add_task(
        _run_analysis_background,
        media_id=media_id,
        job_id=job.job_id,
        user_id=current_user.user_id,
        file_type=media.file_type,
        sample_rate_fps=payload.sample_rate_fps,
        ip_address=ip_address,
        job_type=payload.job_type
    )
    
    return AnalysisJobResponse.model_validate(job)



@router.get(
    "/jobs/{job_id}",
    response_model=AnalysisJobResponse,
    summary="Check status of investigation processing job",
)
def get_analysis_job_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    job = services.get_job_by_id(db, job_id)
    return AnalysisJobResponse.model_validate(job)


@router.get(
    "/media/{media_id}/detections",
    response_model=DetectionListResponse,
    summary="Get detected persons, vehicles, and objects for media item",
)
def get_investigation_detections(
    media_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DetectionListResponse:
    detections = services.get_media_detections(db, media_id)
    return DetectionListResponse(
        media_id=media_id,
        detections=detections,
        total_detections=len(detections),
    )


@router.get(
    "/media/{media_id}/events",
    response_model=EventListResponse,
    summary="Get timeline of extracted investigation events",
)
def get_investigation_events(
    media_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EventListResponse:
    events = services.get_media_events(db, media_id)
    return EventListResponse(
        media_id=media_id,
        events=[m for m in events],  # Pydantic automatic conversion via model_validate inside EventResponse
        total_events=len(events),
    )


@router.post(
    "/media/{media_id}/extract-events",
    response_model=EventListResponse,
    summary="Trigger event extraction layer on media detection results",
)
def extract_investigation_events(
    media_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EventListResponse:
    events = services.extract_events_for_media(
        db=db,
        media_id=media_id,
        user=current_user,
        ip_address=get_client_ip(request),
    )
    return EventListResponse(
        media_id=media_id,
        events=[m for m in events],
        total_events=len(events),
    )


@router.get(
    "/media/{media_id}/decision",
    response_model=CrimeDecisionResponse,
    summary="Get Crime Decision Layer output (potential_crime, non_crime, uncertain)",
)
def get_investigation_crime_decision(
    media_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CrimeDecisionResponse:
    return services.get_crime_decision(db=db, media_id=media_id, user=current_user)


@router.post(
    "/media/{media_id}/link-fir",
    response_model=InvestigationMediaResponse,
    summary="Link investigation media item to a specific FIR case number",
)
def link_media_to_fir_case(
    media_id: int,
    payload: LinkFIRRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InvestigationMediaResponse:
    media = services.link_media_to_fir(
        db=db,
        media_id=media_id,
        fir_id=payload.fir_id,
        user=current_user,
        ip_address=get_client_ip(request),
    )
    return services.to_media_response(media, current_user)


@router.get(
    "/cases/{fir_id}/media",
    response_model=CaseMediaSummaryResponse,
    summary="Get all investigation evidence media and summary stats for a Case/FIR number",
)
def get_case_investigation_media(
    fir_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseMediaSummaryResponse:
    res = services.get_case_media(db=db, fir_id=fir_id, user=current_user)
    return CaseMediaSummaryResponse.model_validate(res)



@router.post(
    "/analyze-image",
    response_model=ImageAnalysisResponse,
    summary="Upload and perform immediate YOLO object detection on a crime scene image",
)
def upload_and_analyze_image(
    request: Request,
    file: UploadFile = File(...),
    district_id: Optional[int] = Form(None),
    fir_id: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ImageAnalysisResponse:
    media = services.save_uploaded_media(
        db=db,
        file=file,
        user=current_user,
        district_id=district_id,
        fir_id=fir_id,
        ip_address=get_client_ip(request),
    )
    analysis_res = services.analyze_image_media(
        db=db,
        media_id=media.media_id,
        user=current_user,
        conf_threshold=confidence_threshold,
        ip_address=get_client_ip(request),
    )
    return ImageAnalysisResponse(
        media=services.to_media_response(analysis_res["media"]),
        job=AnalysisJobResponse.model_validate(analysis_res["job"]),
        image_width=analysis_res["image_width"],
        image_height=analysis_res["image_height"],
        total_detected_objects=analysis_res["total_detected_objects"],
        detections=analysis_res["detections"],
    )


@router.post(
    "/media/{media_id}/analyze-image",
    response_model=ImageAnalysisResponse,
    summary="Run YOLO object detection on an already uploaded media item",
)
def analyze_existing_image_media(
    media_id: int,
    request: Request,
    confidence_threshold: Optional[float] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ImageAnalysisResponse:
    analysis_res = services.analyze_image_media(
        db=db,
        media_id=media_id,
        user=current_user,
        conf_threshold=confidence_threshold,
        ip_address=get_client_ip(request),
    )
    return ImageAnalysisResponse(
        media=services.to_media_response(analysis_res["media"]),
        job=AnalysisJobResponse.model_validate(analysis_res["job"]),
        image_width=analysis_res["image_width"],
        image_height=analysis_res["image_height"],
        total_detected_objects=analysis_res["total_detected_objects"],
        detections=analysis_res["detections"],
    )


@router.post(
    "/analyze-video",
    response_model=VideoAnalysisResponse,
    summary="Upload and perform frame sampling YOLO object tracking on a crime incident video",
)
def upload_and_analyze_video(
    request: Request,
    file: UploadFile = File(...),
    district_id: Optional[int] = Form(None),
    fir_id: Optional[str] = Form(None),
    sample_rate_fps: Optional[int] = Form(None),
    confidence_threshold: Optional[float] = Form(None),
    tracker_type: Optional[str] = Form("bytetrack"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VideoAnalysisResponse:
    media = services.save_uploaded_media(
        db=db,
        file=file,
        user=current_user,
        district_id=district_id,
        fir_id=fir_id,
        ip_address=get_client_ip(request),
    )
    analysis_res = services.analyze_video_media(
        db=db,
        media_id=media.media_id,
        user=current_user,
        sample_rate_fps=sample_rate_fps,
        conf_threshold=confidence_threshold,
        tracker_type=tracker_type,
        ip_address=get_client_ip(request),
    )
    return VideoAnalysisResponse(
        media=services.to_media_response(analysis_res["media"]),
        job=AnalysisJobResponse.model_validate(analysis_res["job"]),
        video_metadata=VideoMetadata.model_validate(analysis_res["video_metadata"]),
        total_detected_objects=analysis_res["total_detected_objects"],
        detections=analysis_res["detections"],
    )


@router.post(
    "/media/{media_id}/analyze-video",
    response_model=VideoAnalysisResponse,
    summary="Run frame sampling YOLO object tracking on an already uploaded video media item",
)
def analyze_existing_video_media(
    media_id: int,
    request: Request,
    sample_rate_fps: Optional[int] = Query(None),
    confidence_threshold: Optional[float] = Query(None),
    tracker_type: Optional[str] = Query("bytetrack"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VideoAnalysisResponse:
    analysis_res = services.analyze_video_media(
        db=db,
        media_id=media_id,
        user=current_user,
        sample_rate_fps=sample_rate_fps,
        conf_threshold=confidence_threshold,
        tracker_type=tracker_type,
        ip_address=get_client_ip(request),
    )
    return VideoAnalysisResponse(
        media=services.to_media_response(analysis_res["media"]),
        job=AnalysisJobResponse.model_validate(analysis_res["job"]),
        video_metadata=VideoMetadata.model_validate(analysis_res["video_metadata"]),
        total_detected_objects=analysis_res["total_detected_objects"],
        detections=analysis_res["detections"],
    )



@router.get(
    "/media/{media_id}/summary",
    response_model=SummaryResponse,
    summary="Get LLM Investigation Summary for evidence media item",
)
def get_investigation_summary(
    media_id: int,
    request: Request,
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    return services.get_investigation_summary(
        db=db,
        media_id=media_id,
        user=current_user,
        force_refresh=force_refresh,
        ip_address=get_client_ip(request),
    )


@router.post(
    "/media/{media_id}/summary",
    response_model=SummaryResponse,
    summary="Generate or refresh LLM Investigation Summary for evidence media item",
)
def generate_investigation_summary(
    media_id: int,
    request: Request,
    payload: Optional[GenerateSummaryRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    force_ref = payload.force_refresh if payload is not None else True
    return services.get_investigation_summary(
        db=db,
        media_id=media_id,
        user=current_user,
        force_refresh=force_ref,
        ip_address=get_client_ip(request),
    )


@router.get(
    "/media/{media_id}/crime-detection",
    response_model=CrimeVideoDetectionResponse,
    summary="Get Crime Video Detection decision layer analysis for evidence media",
)
def get_crime_video_detection(
    media_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CrimeVideoDetectionResponse:
    res = services.get_crime_video_detection(db=db, media_id=media_id, user=current_user)
    return CrimeVideoDetectionResponse(**res)


@router.get(
    "/media/{media_id}/ai-report",
    response_model=AIInvestigationReportResponse,
    summary="Get AI Investigation Report for evidence media item",
)
def get_ai_investigation_report(
    media_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIInvestigationReportResponse:
    report = services.get_ai_investigation_report(
        db=db, media_id=media_id, user=current_user, ip_address=get_client_ip(request),
    )
    return AIInvestigationReportResponse(**report)


@router.post(
    "/media/{media_id}/ai-report",
    response_model=AIInvestigationReportResponse,
    summary="Generate or refresh AI Investigation Report for evidence media item",
)
def generate_ai_investigation_report(
    media_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIInvestigationReportResponse:
    report = services.get_ai_investigation_report(
        db=db, media_id=media_id, user=current_user,
        force_refresh=True, ip_address=get_client_ip(request),
    )
    return AIInvestigationReportResponse(**report)
