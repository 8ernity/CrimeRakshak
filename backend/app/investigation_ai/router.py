"""API Router for AI Video & Image Investigation Support."""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_client_ip, get_current_active_user, require_permissions
from app.models.rbac import User
from app.investigation_ai import services
from app.investigation_ai.schemas import (
    AnalysisJobResponse,
    DetectionListResponse,
    EventListResponse,
    ImageAnalysisResponse,
    InvestigationMediaListResponse,
    InvestigationMediaResponse,
    LinkFIRRequest,
    ProcessMediaRequest,
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
    return InvestigationMediaResponse.model_validate(media)


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
        items=[InvestigationMediaResponse.model_validate(m) for m in items],
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
    return InvestigationMediaResponse.model_validate(media)


@router.post(
    "/media/{media_id}/process",
    response_model=AnalysisJobResponse,
    summary="Trigger computer vision analysis job on uploaded media",
)
def process_investigation_media(
    media_id: int,
    payload: ProcessMediaRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AnalysisJobResponse:
    job = services.create_analysis_job(
        db=db,
        media_id=media_id,
        user=current_user,
        job_type=payload.job_type,
        ip_address=get_client_ip(request),
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
    return InvestigationMediaResponse.model_validate(media)


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
        media=InvestigationMediaResponse.model_validate(analysis_res["media"]),
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
        media=InvestigationMediaResponse.model_validate(analysis_res["media"]),
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
        media=InvestigationMediaResponse.model_validate(analysis_res["media"]),
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
        media=InvestigationMediaResponse.model_validate(analysis_res["media"]),
        job=AnalysisJobResponse.model_validate(analysis_res["job"]),
        video_metadata=VideoMetadata.model_validate(analysis_res["video_metadata"]),
        total_detected_objects=analysis_res["total_detected_objects"],
        detections=analysis_res["detections"],
    )


