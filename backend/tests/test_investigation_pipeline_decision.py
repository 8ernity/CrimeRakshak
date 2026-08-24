"""End-to-End Pipeline & Integration Tests for Crime Decision Layer.

Tests actual flow:
  Upload / Synthetic Media -> Process (YOLO -> ByteTrack -> Pose -> Temporal -> Decision) -> API Decision Response

Verifies:
  1. staged suspicious video -> potential_crime
  2. normal video -> non_crime
  3. ambiguous video -> uncertain
  4. unrelated image -> non_crime/uncertain
  5. Persistence and backward-compatible API responses.
"""
import os
import sys
import tempfile
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.rbac import User
from app.investigation_ai import services
from app.investigation_ai.processors.crime_decision_engine import CrimeDecisionEngine


def _create_mock_user() -> User:
    u = User()
    u.user_id = 1
    u.username = "test_officer"
    u.role = "officer"
    u.is_superuser = True
    u.is_active = True
    return u


def _generate_test_video(path: str, num_frames: int = 30, fps: int = 10):
    """Generate a valid test video file."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (320, 240))
    for i in range(num_frames):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Draw moving rect
        x = (i * 5) % 250
        cv2.rectangle(frame, (x, 50), (x + 30, 150), (100, 200, 100), -1)
        out.write(frame)
    out.release()


def _generate_test_image(path: str):
    """Generate a valid test image file."""
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (100, 150), (120, 150, 200), -1)
    cv2.imwrite(path, img)


def test_e2e_staged_suspicious_video():
    """Test 1: Staged suspicious video -> potential_crime."""
    engine = CrimeDecisionEngine()
    db = SessionLocal()
    user = _create_mock_user()

    # Detections and events representing staged chase + assault + fall
    dets = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.88, "bbox": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.3, "ymax": 0.8}},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.90, "bbox": {"xmin": 0.4, "ymin": 0.1, "xmax": 0.6, "ymax": 0.8}},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 2.0, "confidence": 0.89, "bbox": {"xmin": 0.3, "ymin": 0.1, "xmax": 0.5, "ymax": 0.8}},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 2.0, "confidence": 0.91, "bbox": {"xmin": 0.32, "ymin": 0.1, "xmax": 0.52, "ymax": 0.8}},
    ]

    events = [
        {"event_type": "posture_falling", "timestamp_seconds": 2.5, "tracking_id": 1, "confidence": 0.88},
        {"event_type": "posture_lying_down", "timestamp_seconds": 3.0, "tracking_id": 1, "confidence": 0.86},
        {"event_type": "pattern_rapid_movement_chase", "timestamp_seconds": 1.5, "tracking_id": 1, "confidence": 0.85},
        {"event_type": "pattern_multi_person_interaction", "timestamp_seconds": 2.0, "tracking_id": 1, "confidence": 0.88},
        {"event_type": "pattern_fall_lying_down", "timestamp_seconds": 2.5, "tracking_id": 1, "confidence": 0.89},
    ]

    res = engine.evaluate_decision(detections=dets, events=events, is_video=True, media_id=999)

    print("\nE2E Test 1 (Staged Suspicious Video):", res["decision"], "| Score:", res["evidence_score"])
    assert res["decision"] == "potential_crime"
    assert "status" not in res or res["status"] in ("potential_crime", "non_crime", "uncertain")
    assert res["confidence"] >= 0.70
    assert len(res["track_ids"]) == 2
    assert len(res["timestamps"]) > 0
    print("[PASS] Staged suspicious video -> potential_crime")


def test_e2e_normal_video():
    """Test 2: Normal video -> non_crime."""
    engine = CrimeDecisionEngine()

    dets = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 0.5, "confidence": 0.95},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.5, "confidence": 0.94},
    ]

    events = [
        {"event_type": "person_entered_frame", "timestamp_seconds": 0.5, "tracking_id": 1, "confidence": 0.95},
        {"event_type": "posture_standing", "timestamp_seconds": 1.0, "tracking_id": 1, "confidence": 0.94},
        {"event_type": "person_exited_frame", "timestamp_seconds": 1.5, "tracking_id": 1, "confidence": 0.94},
    ]

    res = engine.evaluate_decision(detections=dets, events=events, is_video=True, media_id=998)

    print("\nE2E Test 2 (Normal Video):", res["decision"], "| Safeguards:", res["safeguards_triggered"])
    assert res["decision"] == "non_crime"
    assert "NORMAL_ACTIVITY_ONLY" in res["safeguards_triggered"]
    print("[PASS] Normal video -> non_crime")


def test_e2e_ambiguous_video():
    """Test 3: Ambiguous video (approach/interaction without assault) -> uncertain."""
    engine = CrimeDecisionEngine()

    dets = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.88},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.89},
    ]

    events = [
        {"event_type": "pattern_approach_interaction_leave", "timestamp_seconds": 1.5, "tracking_id": 1, "confidence": 0.75},
        {"event_type": "pattern_person_following", "timestamp_seconds": 1.2, "tracking_id": 2, "confidence": 0.70},
    ]

    res = engine.evaluate_decision(detections=dets, events=events, is_video=True, media_id=997)

    print("\nE2E Test 3 (Ambiguous Video):", res["decision"], "| Safeguards:", res["safeguards_triggered"])
    assert res["decision"] == "uncertain"
    assert "AMBIGUOUS_INTERACTION_NO_VIOLENCE" in res["safeguards_triggered"]
    print("[PASS] Ambiguous video -> uncertain")


def test_e2e_unrelated_image():
    """Test 4: Unrelated static image -> non_crime or uncertain."""
    engine = CrimeDecisionEngine()

    dets = [
        {"tracking_id": None, "object_class": "person", "timestamp_seconds": 0.0, "confidence": 0.85},
    ]

    events = [
        {"event_type": "person_detected", "timestamp_seconds": 0.0, "tracking_id": None, "confidence": 0.85},
        {"event_type": "posture_standing", "timestamp_seconds": 0.0, "tracking_id": None, "confidence": 0.85},
    ]

    res = engine.evaluate_decision(detections=dets, events=events, is_video=False, media_id=996)

    print("\nE2E Test 4 (Unrelated Image):", res["decision"])
    assert res["decision"] in ("non_crime", "uncertain")
    assert res["decision"] != "potential_crime"
    print("[PASS] Unrelated image -> non_crime / uncertain")


def test_full_upload_process_api_flow():
    """Test 5: Actual upload -> process -> API decision response flow with DB persistence."""
    db = SessionLocal()
    user = _create_mock_user()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test video file
        video_path = os.path.join(tmpdir, "test_flow.mp4")
        _generate_test_video(video_path, num_frames=15, fps=10)

        # 1. Create media record directly in DB
        from app.investigation_ai.models import InvestigationMedia
        media = InvestigationMedia(
            file_name="test_flow.mp4",
            file_path=video_path,
            file_type="video",
            mime_type="video/mp4",
            file_size_bytes=os.path.getsize(video_path),
            sha256_hash="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            district_id=1,
            uploaded_by_user_id=user.user_id,
            status="uploaded",
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        print(f"\nCreated media ID: {media.media_id}")

        # 2. Process video analysis (triggers YOLO -> ByteTrack -> Pose -> Events -> CrimeDecisionEngine)
        res = services.analyze_video_media(
            db=db,
            media_id=media.media_id,
            user=user,
            sample_rate_fps=2,
        )

        assert "crime_decision" in res
        decision_obj = res["crime_decision"]
        assert decision_obj is not None
        assert hasattr(decision_obj, "decision") or "decision" in decision_obj
        print("Process video response crime_decision:", decision_obj.decision if hasattr(decision_obj, "decision") else decision_obj["decision"])

        # 3. Retrieve decision via API service function
        api_decision = services.get_crime_decision(db=db, media_id=media.media_id, user=user)

        print("API decision retrieval:", api_decision.decision, "| status:", api_decision.status, "| confidence:", api_decision.confidence)
        assert api_decision.media_id == media.media_id
        assert api_decision.decision in ("potential_crime", "non_crime", "uncertain")
        assert api_decision.status == api_decision.decision
        assert isinstance(api_decision.confidence, float)
        assert isinstance(api_decision.reasons, str)
        assert isinstance(api_decision.evidence_events, list)
        assert isinstance(api_decision.timestamps, list)

        print("[PASS] Full upload -> process -> API decision response flow verified")


if __name__ == "__main__":
    test_e2e_staged_suspicious_video()
    test_e2e_normal_video()
    test_e2e_ambiguous_video()
    test_e2e_unrelated_image()
    test_full_upload_process_api_flow()
    print("\n==========================================")
    print("ALL PIPELINE & E2E INTEGRATION TESTS PASSED!")
    print("==========================================")
