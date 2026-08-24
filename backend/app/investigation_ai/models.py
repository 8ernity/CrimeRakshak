"""ORM models for AI Video & Image Investigation Support."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InvestigationMedia(Base):
    """Uploaded crime video or image media record."""

    __tablename__ = "investigation_media"

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "image" or "video"
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Video metadata (nullable for images)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_frames: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Scoping and linkage
    district_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    fir_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    jobs: Mapped[List["InvestigationAnalysisJob"]] = relationship(
        "InvestigationAnalysisJob", back_populates="media", cascade="all, delete-orphan"
    )
    detections: Mapped[List["DetectionResult"]] = relationship(
        "DetectionResult", back_populates="media", cascade="all, delete-orphan"
    )
    events: Mapped[List["InvestigationEvent"]] = relationship(
        "InvestigationEvent", back_populates="media", cascade="all, delete-orphan"
    )
    summaries: Mapped[List["InvestigationSummary"]] = relationship(
        "InvestigationSummary", back_populates="media", cascade="all, delete-orphan"
    )
    crime_decisions: Mapped[List["InvestigationCrimeDecision"]] = relationship(
        "InvestigationCrimeDecision", back_populates="media", cascade="all, delete-orphan"
    )


class InvestigationAnalysisJob(Base):
    """Analysis processing job associated with a media item."""

    __tablename__ = "investigation_analysis_jobs"

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_media.media_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), default="full_analysis", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    media: Mapped[InvestigationMedia] = relationship("InvestigationMedia", back_populates="jobs")
    detections: Mapped[List["DetectionResult"]] = relationship(
        "DetectionResult", back_populates="job", cascade="all, delete-orphan"
    )
    events: Mapped[List["InvestigationEvent"]] = relationship(
        "InvestigationEvent", back_populates="job", cascade="all, delete-orphan"
    )


class DetectionResult(Base):
    """Detected person, vehicle, or object bounding box record."""

    __tablename__ = "detection_results"

    detection_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_analysis_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_media.media_id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    object_class: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tracking_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Bounding box coordinates normalized (0.0 to 1.0) or in pixels
    bbox_xmin: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_ymin: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_xmax: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_ymax: Mapped[float] = mapped_column(Float, nullable=False)
    crop_image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    media: Mapped[InvestigationMedia] = relationship("InvestigationMedia", back_populates="detections")
    job: Mapped[InvestigationAnalysisJob] = relationship("InvestigationAnalysisJob", back_populates="detections")


class InvestigationEvent(Base):
    """Extracted investigative timeline event."""

    __tablename__ = "investigation_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_analysis_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_media.media_id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    frame_start: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_end: Mapped[int] = mapped_column(Integer, nullable=False)
    tracking_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    linked_person_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linked_fir_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    media: Mapped[InvestigationMedia] = relationship("InvestigationMedia", back_populates="events")
    job: Mapped[InvestigationAnalysisJob] = relationship("InvestigationAnalysisJob", back_populates="events")


class InvestigationSummary(Base):
    """Generated LLM Investigation Summary for evidence media."""

    __tablename__ = "investigation_summaries"

    summary_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_media.media_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("investigation_analysis_jobs.job_id", ondelete="SET NULL"), nullable=True, index=True
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    observed_events: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevant_timestamps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_objects_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uncertainty_limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_used: Mapped[str] = mapped_column(String(50), default="llm", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    media: Mapped[InvestigationMedia] = relationship("InvestigationMedia", back_populates="summaries")


class InvestigationCrimeDecision(Base):
    """Persisted Crime Decision Layer output for an evidence media item."""

    __tablename__ = "investigation_crime_decisions"

    decision_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_media.media_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("investigation_analysis_jobs.job_id", ondelete="SET NULL"), nullable=True, index=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # 'potential_crime', 'non_crime', 'uncertain'
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_events: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    timestamps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    track_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    safeguards_triggered: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    is_video: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    media: Mapped[InvestigationMedia] = relationship("InvestigationMedia", back_populates="crime_decisions")


