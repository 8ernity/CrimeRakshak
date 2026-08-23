"""Unit and integration tests for LLM Investigation Summary layer."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ["POSTGRES_URI"] = "postgresql://u:p@localhost:5432/placeholder"

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import app.core.database as database

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
database.engine = test_engine
database.SessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)

from app.core.database import Base, get_db
import app.models.rbac  # noqa: F401
import app.investigation_ai.models  # noqa: F401
from app.main import app

Base.metadata.create_all(bind=test_engine)

TestingSession = database.SessionLocal


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Seed dev admin user
from app.models.rbac import User
_seed_db = TestingSession()
admin_user = _seed_db.query(User).filter_by(username="admin").first()
if not admin_user:
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password_hash="dummy",
        is_active=True,
        is_superuser=True,
        district_id=1,
    )
    _seed_db.add(admin_user)
    _seed_db.commit()
    _seed_db.refresh(admin_user)
_seed_db.close()

client = TestClient(app)

from app.investigation_ai.models import (
    InvestigationMedia,
    InvestigationAnalysisJob,
    DetectionResult,
    InvestigationEvent,
)
from app.investigation_ai.summary_generator import (
    build_structured_evidence,
    generate_fallback_summary,
    get_or_create_investigation_summary,
)


def seed_test_investigation_data():
    """Seed sample media, detections, and events in test DB."""
    db = TestingSession()
    media = InvestigationMedia(
        file_name="evidence_video_01.mp4",
        file_path="storage/investigation/uploads/test_video.mp4",
        file_type="video",
        mime_type="video/mp4",
        file_size_bytes=1024000,
        sha256_hash="abc123hash",
        duration_seconds=10.0,
        fps=30.0,
        total_frames=300,
        district_id=1,
        fir_id="FIR-2026-BLR-001",
        uploaded_by_user_id=1,
        status="processed",
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    job = InvestigationAnalysisJob(
        media_id=media.media_id,
        job_type="full_analysis",
        status="completed",
        progress_pct=100.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Add Detections
    d1 = DetectionResult(
        job_id=job.job_id,
        media_id=media.media_id,
        frame_number=0,
        timestamp_seconds=0.0,
        object_class="person",
        tracking_id=1,
        confidence=0.92,
        bbox_xmin=0.1,
        bbox_ymin=0.1,
        bbox_xmax=0.3,
        bbox_ymax=0.8,
    )
    d2 = DetectionResult(
        job_id=job.job_id,
        media_id=media.media_id,
        frame_number=30,
        timestamp_seconds=1.0,
        object_class="car",
        tracking_id=10,
        confidence=0.95,
        bbox_xmin=0.4,
        bbox_ymin=0.4,
        bbox_xmax=0.8,
        bbox_ymax=0.9,
    )
    d3 = DetectionResult(
        job_id=job.job_id,
        media_id=media.media_id,
        frame_number=60,
        timestamp_seconds=2.0,
        object_class="person",
        tracking_id=2,
        confidence=0.88,
        bbox_xmin=0.2,
        bbox_ymin=0.6,
        bbox_xmax=0.8,
        bbox_ymax=0.85,
    )
    db.add_all([d1, d2, d3])
    db.commit()

    # Add Events
    e1 = InvestigationEvent(
        job_id=job.job_id,
        media_id=media.media_id,
        event_type="person_entered_frame",
        description="Person entered frame at 0.0s.",
        start_timestamp_seconds=0.0,
        end_timestamp_seconds=0.0,
        frame_start=0,
        frame_end=0,
        tracking_id=1,
        confidence=0.92,
    )
    e2 = InvestigationEvent(
        job_id=job.job_id,
        media_id=media.media_id,
        event_type="possible_person_down",
        description="Possible person-down / horizontal posture detected.",
        start_timestamp_seconds=2.0,
        end_timestamp_seconds=2.0,
        frame_start=60,
        frame_end=60,
        tracking_id=2,
        confidence=0.88,
    )
    db.add_all([e1, e2])
    db.commit()

    media_id = media.media_id
    db.close()
    return media_id


def test_structured_evidence_collection():
    media_id = seed_test_investigation_data()
    db = TestingSession()
    user = db.query(User).filter_by(username="admin").first()
    media = db.query(InvestigationMedia).filter_by(media_id=media_id).first()

    evidence = build_structured_evidence(db, media, user)

    assert "media_metadata" in evidence
    assert evidence["media_metadata"]["media_id"] == media_id
    assert evidence["media_metadata"]["fir_id"] == "FIR-2026-BLR-001"

    assert "detection_stats" in evidence
    assert evidence["detection_stats"]["total_detections"] == 3
    assert evidence["detection_stats"]["class_breakdown"]["person"] == 2
    assert evidence["detection_stats"]["class_breakdown"]["car"] == 1

    assert "tracking_results" in evidence
    assert len(evidence["tracking_results"]) == 3
    track_ids = [t["tracking_id"] for t in evidence["tracking_results"]]
    assert 1 in track_ids
    assert 10 in track_ids
    assert 2 in track_ids

    assert "investigation_events" in evidence
    assert len(evidence["investigation_events"]) == 2

    assert "fir_metadata" in evidence
    assert evidence["fir_metadata"]["authorized"] is True

    db.close()


def test_case_fir_authorization_restriction():
    media_id = seed_test_investigation_data()
    db = TestingSession()
    
    # Create non-superuser restricted officer in district 99 (media is district 1)
    restricted_user = User(
        username="officer_district99",
        email="officer@example.com",
        password_hash="dummy",
        is_active=True,
        is_superuser=False,
        district_id=99,
    )
    media = db.query(InvestigationMedia).filter_by(media_id=media_id).first()

    evidence = build_structured_evidence(db, media, restricted_user)
    assert evidence["fir_metadata"]["authorized"] is False
    assert "restricted" in evidence["fir_metadata"]["status"].lower()

    db.close()


def test_fallback_summary_generation():
    media_id = seed_test_investigation_data()
    db = TestingSession()
    user = db.query(User).filter_by(username="admin").first()
    media = db.query(InvestigationMedia).filter_by(media_id=media_id).first()

    evidence = build_structured_evidence(db, media, user)
    summary = generate_fallback_summary(evidence)

    assert "summary_text" in summary
    assert "observed_events" in summary
    assert "relevant_timestamps" in summary
    assert "detected_objects_summary" in summary
    assert "evidence_references" in summary
    assert "uncertainty_limitations" in summary

    # Verify required content
    assert len(summary["observed_events"]) >= 2
    assert len(summary["relevant_timestamps"]) >= 3
    assert len(summary["uncertainty_limitations"]) >= 4

    # Verify legal guardrails compliance
    prose = summary["summary_text"].lower()
    assert "criminal" not in prose
    assert "guilty" not in prose

    db.close()


def test_summary_api_endpoints():
    media_id = seed_test_investigation_data()

    # GET Summary
    get_res = client.get(f"/api/v1/investigation/media/{media_id}/summary")
    assert get_res.status_code == 200
    data = get_res.json()

    assert data["media_id"] == media_id
    assert "summary_text" in data
    assert isinstance(data["observed_events"], list)
    assert isinstance(data["relevant_timestamps"], list)
    assert isinstance(data["detected_objects_summary"], list)
    assert isinstance(data["evidence_references"], list)
    assert isinstance(data["uncertainty_limitations"], list)

    # POST Summary (force refresh)
    post_res = client.post(
        f"/api/v1/investigation/media/{media_id}/summary",
        json={"force_refresh": True},
    )
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["media_id"] == media_id
    assert "summary_text" in post_data


if __name__ == "__main__":
    test_structured_evidence_collection()
    print("[PASS] test_structured_evidence_collection")
    test_case_fir_authorization_restriction()
    print("[PASS] test_case_fir_authorization_restriction")
    test_fallback_summary_generation()
    print("[PASS] test_fallback_summary_generation")
    test_summary_api_endpoints()
    print("[PASS] test_summary_api_endpoints")
    print("ALL LLM INVESTIGATION SUMMARY TESTS PASSED CLEANLY!")
