"""Unit tests for YOLOv8 Pose Estimation & Posture Analysis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ["POSTGRES_URI"] = "postgresql://u:p@localhost:5432/placeholder"

from app.investigation_ai.processors.pose_estimator import (
    COCO_KEYPOINTS,
    estimate_posture_from_keypoints,
)
from app.investigation_ai.processors.event_extractor import EventExtractor


def test_coco_keypoint_names():
    assert len(COCO_KEYPOINTS) == 17
    assert "left_shoulder" in COCO_KEYPOINTS
    assert "right_shoulder" in COCO_KEYPOINTS
    assert "left_hip" in COCO_KEYPOINTS
    assert "right_hip" in COCO_KEYPOINTS
    assert "left_knee" in COCO_KEYPOINTS
    assert "right_ankle" in COCO_KEYPOINTS


def test_posture_standing():
    # Vertical posture: Shoulders at y=50, Hips at y=150, Knees at y=230, Ankles at y=300
    kps = [
        {"name": "left_shoulder", "x": 100, "y": 50, "conf": 0.9},
        {"name": "right_shoulder", "x": 120, "y": 50, "conf": 0.9},
        {"name": "left_hip", "x": 100, "y": 150, "conf": 0.9},
        {"name": "right_hip", "x": 120, "y": 150, "conf": 0.9},
        {"name": "left_knee", "x": 100, "y": 230, "conf": 0.9},
        {"name": "right_knee", "x": 120, "y": 230, "conf": 0.9},
        {"name": "left_ankle", "x": 100, "y": 300, "conf": 0.9},
        {"name": "right_ankle", "x": 120, "y": 300, "conf": 0.9},
    ]
    posture, conf = estimate_posture_from_keypoints(kps)
    assert posture == "standing"
    assert conf >= 0.85


def test_posture_lying_down():
    # Horizontal posture: Shoulders at x=50, y=100; Hips at x=180, y=105
    kps = [
        {"name": "left_shoulder", "x": 50, "y": 100, "conf": 0.9},
        {"name": "right_shoulder", "x": 50, "y": 110, "conf": 0.9},
        {"name": "left_hip", "x": 180, "y": 105, "conf": 0.9},
        {"name": "right_hip", "x": 180, "y": 115, "conf": 0.9},
    ]
    posture, conf = estimate_posture_from_keypoints(kps)
    assert posture == "lying_down"
    assert conf >= 0.85


def test_posture_lying_down_bbox_fallback():
    # Fallback to aspect ratio when keypoints are missing: W=200, H=80 (W/H = 2.5 >= 1.25)
    bbox = {"xmin": 10, "ymin": 50, "xmax": 210, "ymax": 130}
    posture, conf = estimate_posture_from_keypoints([], bbox=bbox)
    assert posture == "lying_down"


def test_posture_falling():
    # Tilted torso (45 degrees): Shoulders at (50, 100), Hips at (120, 170)
    kps = [
        {"name": "left_shoulder", "x": 50, "y": 100, "conf": 0.9},
        {"name": "right_shoulder", "x": 60, "y": 100, "conf": 0.9},
        {"name": "left_hip", "x": 120, "y": 170, "conf": 0.9},
        {"name": "right_hip", "x": 130, "y": 170, "conf": 0.9},
    ]
    posture, conf = estimate_posture_from_keypoints(kps)
    assert posture in ("falling", "lying_down")


def test_posture_sitting():
    # Sitting: Torso vertical (Shoulders y=50, Hips y=150), Knees at y=160 (near hips), Ankles at y=230
    kps = [
        {"name": "left_shoulder", "x": 100, "y": 50, "conf": 0.9},
        {"name": "right_shoulder", "x": 120, "y": 50, "conf": 0.9},
        {"name": "left_hip", "x": 100, "y": 150, "conf": 0.9},
        {"name": "right_hip", "x": 120, "y": 150, "conf": 0.9},
        {"name": "left_knee", "x": 160, "y": 160, "conf": 0.9},
        {"name": "right_knee", "x": 170, "y": 160, "conf": 0.9},
        {"name": "left_ankle", "x": 160, "y": 230, "conf": 0.9},
        {"name": "right_ankle", "x": 170, "y": 230, "conf": 0.9},
    ]
    posture, conf = estimate_posture_from_keypoints(kps)
    assert posture == "sitting"


def test_posture_running():
    # Running: Torso lean 20 deg (Shoulders x=110 y=50, Hips x=100 y=150), Wide stride (Left Ankle x=40, Right Ankle x=160)
    kps = [
        {"name": "left_shoulder", "x": 110, "y": 50, "conf": 0.9},
        {"name": "right_shoulder", "x": 130, "y": 50, "conf": 0.9},
        {"name": "left_hip", "x": 100, "y": 150, "conf": 0.9},
        {"name": "right_hip", "x": 120, "y": 150, "conf": 0.9},
        {"name": "left_ankle", "x": 40, "y": 250, "conf": 0.9},
        {"name": "right_ankle", "x": 160, "y": 250, "conf": 0.9},
    ]
    posture, conf = estimate_posture_from_keypoints(kps)
    assert posture == "running"


def test_event_extractor_posture_events():
    extractor = EventExtractor()
    detections = [
        {
            "frame_number": 0,
            "timestamp_seconds": 0.0,
            "object_class": "person",
            "tracking_id": 5,
            "confidence": 0.90,
            "posture": "standing",
            "bbox": {"xmin": 100, "ymin": 50, "xmax": 150, "ymax": 250},
        },
        {
            "frame_number": 10,
            "timestamp_seconds": 1.0,
            "object_class": "person",
            "tracking_id": 5,
            "confidence": 0.88,
            "posture": "running",
            "bbox": {"xmin": 120, "ymin": 50, "xmax": 180, "ymax": 250},
        },
        {
            "frame_number": 20,
            "timestamp_seconds": 2.0,
            "object_class": "person",
            "tracking_id": 5,
            "confidence": 0.85,
            "posture": "lying_down",
            "bbox": {"xmin": 50, "ymin": 200, "xmax": 250, "ymax": 260},
        },
    ]

    events = extractor.extract_events(detections, media_id=202)
    event_types = [e["event_type"] for e in events]

    assert "person_detected" in event_types
    assert "person_entered_frame" in event_types
    assert "posture_running" in event_types
    assert "posture_lying_down" in event_types
    assert "possible_person_down" in event_types

    lying_event = [e for e in events if e["event_type"] == "posture_lying_down"][0]
    assert lying_event["tracking_id"] == 5
    assert lying_event["timestamp_seconds"] == 2.0
    assert lying_event["frame_number"] == 20
    assert lying_event["posture"] == "lying_down"


def test_track_id_persistence_across_posture_transition():
    from app.investigation_ai.processors.video_processor import _smooth_track_continuity

    raw_detections = [
        # Frame 0-10: Track 1 standing upright at (150, 250)
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 1, "posture": "standing", "bbox": {"xmin": 130, "ymin": 150, "xmax": 170, "ymax": 350}},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 1, "posture": "standing", "bbox": {"xmin": 130, "ymin": 150, "xmax": 170, "ymax": 350}},
        # Frame 15-30: Abrupt fall/rotation -> tracker assigned Track 2 at (150, 300)
        {"frame_number": 15, "timestamp_seconds": 1.5, "object_class": "person", "tracking_id": 2, "posture": "falling", "bbox": {"xmin": 110, "ymin": 280, "xmax": 210, "ymax": 350}},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 2, "posture": "lying_down", "bbox": {"xmin": 100, "ymin": 300, "xmax": 250, "ymax": 350}},
    ]

    smoothed = _smooth_track_continuity(raw_detections)
    assigned_tids = [d["tracking_id"] for d in smoothed]

    # Verify that Track 2 was remapped to Track 1 so identity is retained
    assert all(tid == 1 for tid in assigned_tids)


def run_all_pose_tests():
    test_coco_keypoint_names()
    test_posture_standing()
    test_posture_lying_down()
    test_posture_lying_down_bbox_fallback()
    test_posture_falling()
    test_posture_sitting()
    test_posture_running()
    test_event_extractor_posture_events()
    test_track_id_persistence_across_posture_transition()
    print("[PASS] ALL POSE ESTIMATION & POSTURE TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_all_pose_tests()
