"""Pydantic schemas for AI Video & Image Investigation Support API."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Media Upload & Details ──

class InvestigationMediaBase(BaseModel):
    file_name: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    district_id: Optional[int] = None
    fir_id: Optional[str] = None


class InvestigationMediaResponse(InvestigationMediaBase):
    media_id: int
    sha256_hash: str
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    uploaded_by_user_id: Optional[int] = None
    status: str
    upload_timestamp: datetime

    class Config:
        from_attributes = True


class InvestigationMediaListResponse(BaseModel):
    items: List[InvestigationMediaResponse]
    total: int


# ── Analysis Jobs ──

class ProcessMediaRequest(BaseModel):
    job_type: str = "full_analysis"
    sample_rate_fps: Optional[int] = 2


class AnalysisJobResponse(BaseModel):
    job_id: int
    media_id: int
    job_type: str
    status: str
    progress_pct: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Detections ──

class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class DetectionResponse(BaseModel):
    detection_id: int
    job_id: int
    media_id: int
    frame_number: int
    timestamp_seconds: float
    object_class: str
    tracking_id: Optional[int] = None
    confidence: float
    bbox: BoundingBox
    crop_image_path: Optional[str] = None

    class Config:
        from_attributes = True


class DetectionListResponse(BaseModel):
    media_id: int
    detections: List[DetectionResponse]
    total_detections: int


# ── Events ──

class EventResponse(BaseModel):
    event_id: int
    job_id: int
    media_id: int
    event_type: str
    description: str
    start_timestamp_seconds: float
    end_timestamp_seconds: float
    frame_start: int
    frame_end: int
    linked_person_id: Optional[str] = None
    linked_fir_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    media_id: int
    events: List[EventResponse]
    total_events: int


# ── FIR Linking ──

class LinkFIRRequest(BaseModel):
    fir_id: str


# ── Image Analysis Direct Response ──

class ImageAnalysisResponse(BaseModel):
    media: InvestigationMediaResponse
    job: AnalysisJobResponse
    image_width: int
    image_height: int
    total_detected_objects: int
    detections: List[DetectionResponse]

