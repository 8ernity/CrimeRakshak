"""Unit tests for Temporal Sequence & Action Pattern Analysis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ["POSTGRES_URI"] = "postgresql://u:p@localhost:5432/placeholder"

from app.investigation_ai.processors.temporal_analyzer import TemporalAnalyzer
from app.investigation_ai.processors.event_extractor import EventExtractor


def test_temporal_fall_lying_down_sequence():
    analyzer = TemporalAnalyzer()
    detections = [
        {
            "frame_number": 0,
            "timestamp_seconds": 0.0,
            "object_class": "person",
            "tracking_id": 10,
            "posture": "standing",
            "bbox": {"xmin": 100, "ymin": 50, "xmax": 140, "ymax": 200},
        },
        {
            "frame_number": 10,
            "timestamp_seconds": 0.5,
            "object_class": "person",
            "tracking_id": 10,
            "posture": "falling",
            "bbox": {"xmin": 110, "ymin": 80, "xmax": 180, "ymax": 200},
        },
        {
            "frame_number": 20,
            "timestamp_seconds": 1.0,
            "object_class": "person",
            "tracking_id": 10,
            "posture": "lying_down",
            "bbox": {"xmin": 100, "ymin": 150, "xmax": 250, "ymax": 210},
        },
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=301)
    event_types = [p["event_type"] for p in patterns]

    assert "pattern_fall_lying_down" in event_types
    fall_event = [p for p in patterns if p["event_type"] == "pattern_fall_lying_down"][0]
    assert fall_event["tracking_id"] == 10
    assert fall_event["timestamp_seconds"] == 0.5
    assert fall_event["end_timestamp_seconds"] == 1.0
    assert "exhibited fall transition to lying_down" in fall_event["description"]


def test_temporal_approach_interaction_leave():
    analyzer = TemporalAnalyzer()
    detections = [
        # Frame 0: Track 1 at (50,50), Track 2 at (300,50) -> dist = 250
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 40, "ymin": 40, "xmax": 60, "ymax": 60}},
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 290, "ymin": 40, "xmax": 310, "ymax": 60}},
        # Frame 10: Track 1 at (150,50), Track 2 at (180,50) -> dist = 30 (Interaction)
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 140, "ymin": 40, "xmax": 160, "ymax": 60}},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 170, "ymin": 40, "xmax": 190, "ymax": 60}},
        # Frame 20: Track 1 at (30,50), Track 2 at (350,50) -> dist = 320 (Leave)
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 20, "ymin": 40, "xmax": 40, "ymax": 60}},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 340, "ymin": 40, "xmax": 360, "ymax": 60}},
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=302)
    event_types = [p["event_type"] for p in patterns]

    assert "pattern_approach_interaction_leave" in event_types
    app_event = [p for p in patterns if p["event_type"] == "pattern_approach_interaction_leave"][0]
    assert app_event["tracking_id"] in (1, 2)
    assert app_event["secondary_tracking_id"] in (1, 2)
    assert app_event["timestamp_seconds"] == 0.0
    assert app_event["end_timestamp_seconds"] == 2.0


def test_temporal_person_following():
    analyzer = TemporalAnalyzer()
    detections = [
        # Frame 0: T1 at (50, 50), T2 at (100, 50)
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 40, "ymin": 40, "xmax": 60, "ymax": 60}},
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 90, "ymin": 40, "xmax": 110, "ymax": 60}},
        # Frame 10: T1 moved to (90, 50), T2 moved to (140, 50) - vector (40, 0)
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 80, "ymin": 40, "xmax": 100, "ymax": 60}},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 130, "ymin": 40, "xmax": 150, "ymax": 60}},
        # Frame 20: T1 moved to (130, 50), T2 moved to (180, 50) - vector (40, 0)
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 1, "bbox": {"xmin": 120, "ymin": 40, "xmax": 140, "ymax": 60}},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 2, "bbox": {"xmin": 170, "ymin": 40, "xmax": 190, "ymax": 60}},
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=303)
    event_types = [p["event_type"] for p in patterns]

    assert "pattern_person_following" in event_types
    f_event = [p for p in patterns if p["event_type"] == "pattern_person_following"][0]
    assert f_event["tracking_id"] == 1
    assert f_event["secondary_tracking_id"] == 2


def test_temporal_person_vehicle_walking_past_no_interaction():
    """Case 1: Pedestrian walking past a vehicle (IoU < 0.18 or < 3 frames persistence) -> NO interaction."""
    analyzer = TemporalAnalyzer()
    detections = [
        # Frame 0: Person walking past vehicle, distance 150px, IoU = 0.0
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 3, "bbox": {"xmin": 10, "ymin": 100, "xmax": 40, "ymax": 180}},
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "car", "tracking_id": 20, "bbox": {"xmin": 100, "ymin": 90, "xmax": 220, "ymax": 190}},
        # Frame 10: Brief overlap (IoU = 0.10 < 0.18)
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 3, "bbox": {"xmin": 90, "ymin": 100, "xmax": 130, "ymax": 180}},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "car", "tracking_id": 20, "bbox": {"xmin": 100, "ymin": 90, "xmax": 220, "ymax": 190}},
        # Frame 20: Person already walked past, distance 160px, IoU = 0.0
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 3, "bbox": {"xmin": 230, "ymin": 100, "xmax": 260, "ymax": 180}},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "car", "tracking_id": 20, "bbox": {"xmin": 100, "ymin": 90, "xmax": 220, "ymax": 190}},
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=304)
    event_types = [p["event_type"] for p in patterns]

    # Verify NO false positive vehicle interaction event is produced
    assert "pattern_person_vehicle_interaction" not in event_types


def test_temporal_person_vehicle_interaction_stopping():
    """Case 2: Person actually approaching and stopping near vehicle for 3+ consecutive frames with IoU >= 0.18 -> Interaction."""
    analyzer = TemporalAnalyzer()
    # High overlap (xmin=100..150 overlapping xmin=100..220 -> IoU = 50*80 / (50*80 + 120*100 - 4000) = 4000/12000 = 0.33 >= 0.18)
    p_box = {"xmin": 100, "ymin": 100, "xmax": 150, "ymax": 180}
    v_box = {"xmin": 100, "ymin": 90, "xmax": 220, "ymax": 190}

    detections = [
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 3, "posture": "standing", "bbox": p_box},
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 3, "posture": "standing", "bbox": p_box},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 3, "posture": "standing", "bbox": p_box},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=305)
    event_types = [p["event_type"] for p in patterns]

    assert "pattern_person_vehicle_interaction" in event_types
    v_event = [p for p in patterns if p["event_type"] == "pattern_person_vehicle_interaction"][0]
    assert v_event["tracking_id"] == 3
    assert v_event["secondary_tracking_id"] == 20


def test_temporal_person_vehicle_interaction_posture():
    """Case 3: Person sitting/interacting near vehicle for 3+ consecutive frames with IoU >= 0.18 -> Interaction."""
    analyzer = TemporalAnalyzer()
    p_box = {"xmin": 100, "ymin": 100, "xmax": 150, "ymax": 180}
    v_box = {"xmin": 100, "ymin": 90, "xmax": 220, "ymax": 190}

    detections = [
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 3, "posture": "sitting", "bbox": p_box},
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 3, "posture": "sitting", "bbox": p_box},
        {"frame_number": 10, "timestamp_seconds": 1.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "person", "tracking_id": 3, "posture": "sitting", "bbox": p_box},
        {"frame_number": 20, "timestamp_seconds": 2.0, "object_class": "car", "tracking_id": 20, "bbox": v_box},
    ]

    patterns = analyzer.analyze_temporal_patterns(detections, media_id=306)
    event_types = [p["event_type"] for p in patterns]

    assert "pattern_person_vehicle_interaction" in event_types


def test_event_extractor_integrates_temporal_patterns():
    extractor = EventExtractor()
    detections = [
        {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person", "tracking_id": 7, "posture": "standing", "bbox": {"xmin": 50, "ymin": 50, "xmax": 90, "ymax": 200}},
        {"frame_number": 10, "timestamp_seconds": 0.5, "object_class": "person", "tracking_id": 7, "posture": "falling", "bbox": {"xmin": 60, "ymin": 80, "xmax": 140, "ymax": 200}},
        {"frame_number": 20, "timestamp_seconds": 1.0, "object_class": "person", "tracking_id": 7, "posture": "lying_down", "bbox": {"xmin": 50, "ymin": 150, "xmax": 220, "ymax": 210}},
    ]

    events = extractor.extract_events(detections, media_id=307)
    event_types = [e["event_type"] for e in events]

    assert "person_detected" in event_types
    assert "posture_lying_down" in event_types
    assert "pattern_fall_lying_down" in event_types


def run_all_temporal_tests():
    test_temporal_fall_lying_down_sequence()
    test_temporal_approach_interaction_leave()
    test_temporal_person_following()
    test_temporal_person_vehicle_walking_past_no_interaction()
    test_temporal_person_vehicle_interaction_stopping()
    test_temporal_person_vehicle_interaction_posture()
    test_event_extractor_integrates_temporal_patterns()
    print("[PASS] ALL TEMPORAL SEQUENCE ANALYSIS TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_all_temporal_tests()
