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
    media_url: Optional[str] = None

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
    posture: Optional[str] = None
    keypoints: Optional[List[dict]] = None

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
    tracking_id: Optional[int] = None
    confidence: Optional[float] = None
    posture: Optional[str] = None
    linked_person_id: Optional[str] = None
    linked_fir_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    media_id: int
    events: List[EventResponse]
    total_events: int


# ── FIR / Case Linking & Aggregation ──

class LinkFIRRequest(BaseModel):
    fir_id: Optional[str] = None


class CaseMediaSummaryResponse(BaseModel):
    fir_id: str
    district_id: Optional[int] = None
    total_media: int
    media_items: List[InvestigationMediaResponse]
    total_detections: int
    total_events: int



# ── Crime Decision Layer Response ──

class CrimeDecisionResponse(BaseModel):
    media_id: int
    decision: str  # 'potential_crime', 'non_crime', 'uncertain'
    status: str  # Alias for decision (backward compatibility requirement)
    confidence: float
    evidence_score: float
    reasons: str  # Human-readable rationale explanation
    evidence_events: List[str] = Field(default_factory=list)
    timestamps: List[float] = Field(default_factory=list)
    track_ids: List[int] = Field(default_factory=list)
    safeguards_triggered: List[str] = Field(default_factory=list)
    is_video: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimestampRange(BaseModel):
    start: float
    end: float


class CrimeVideoDetectionResponse(BaseModel):
    classification: str  # 'possible_crime' or 'no_clear_crime_evidence'
    confidence: float
    crime_indicators: List[str] = Field(default_factory=list)
    relevant_timestamps: List[TimestampRange] = Field(default_factory=list)
    evidence_events: List[dict] = Field(default_factory=list)



# ── Image & Video Analysis Direct Responses ──

class ImageAnalysisResponse(BaseModel):
    media: InvestigationMediaResponse
    job: AnalysisJobResponse
    image_width: int
    image_height: int
    total_detected_objects: int
    detections: List[DetectionResponse]
    crime_decision: Optional[CrimeDecisionResponse] = None


class VideoMetadata(BaseModel):
    fps: float
    total_frames: int
    duration_seconds: float
    width: int
    height: int
    sample_rate_fps: int
    sampled_frames_count: int


class VideoAnalysisResponse(BaseModel):
    media: InvestigationMediaResponse
    job: AnalysisJobResponse
    video_metadata: VideoMetadata
    total_detected_objects: int
    detections: List[DetectionResponse]
    crime_decision: Optional[CrimeDecisionResponse] = None


# ── LLM Investigation Summary ──

class GenerateSummaryRequest(BaseModel):
    force_refresh: Optional[bool] = False


class SummaryResponse(BaseModel):
    summary_id: Optional[int] = None
    media_id: int
    job_id: Optional[int] = None
    summary_text: str
    observed_events: List[str] = Field(default_factory=list)
    relevant_timestamps: List[str] = Field(default_factory=list)
    detected_objects_summary: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    uncertainty_limitations: List[str] = Field(default_factory=list)
    provider_used: str = "llm"
    created_at: datetime

    class Config:
        from_attributes = True



# ── AI Investigation Report ──

class EvidenceObservation(BaseModel):
    observation: str
    source: str = "directly_observed"  # "directly_observed" | "ai_inference" | "uncertain"
    confidence: float = 0.5
    timestamp_seconds: Optional[float] = None
    tracking_id: Optional[int] = None


class DetectedEntity(BaseModel):
    entity_type: str = "object"  # "person" | "vehicle" | "weapon" | "object"
    description: str = ""
    tracking_id: Optional[int] = None
    first_seen_seconds: Optional[float] = None
    last_seen_seconds: Optional[float] = None
    confidence: float = 0.5


class TimelineEntry(BaseModel):
    timestamp_seconds: float = 0.0
    description: str = ""
    source: str = "directly_observed"
    significance: str = "routine"  # "critical" | "notable" | "routine"


class EvidenceFrameRef(BaseModel):
    frame_index: int = 0
    timestamp_seconds: float = 0.0
    description: str = ""
    relevant_observations: List[str] = Field(default_factory=list)


class AIInvestigationReportResponse(BaseModel):
    media_id: int = 0
    report_id: Optional[int] = None
    incident_classification: str = "Insufficient Evidence for Classification"
    confidence: float = 0.5
    executive_summary: str = ""
    observed_evidence: List[EvidenceObservation] = Field(default_factory=list)
    detected_objects: List[str] = Field(default_factory=list)
    detected_persons_vehicles: List[DetectedEntity] = Field(default_factory=list)
    chronological_timeline: List[TimelineEntry] = Field(default_factory=list)
    relevant_timestamps: List[TimestampRange] = Field(default_factory=list)
    evidence_frame_references: List[EvidenceFrameRef] = Field(default_factory=list)
    crime_indicators: List[str] = Field(default_factory=list)
    uncertainty_notes: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provider_used: str = "gemini_vision"
    frames_supplied_to_model: int = 0
    fallback_reason: Optional[str] = None
    created_at: Optional[str] = None
