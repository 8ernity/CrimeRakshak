"""Unit tests for Investigation Event Extraction Layer."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ["POSTGRES_URI"] = "postgresql://u:p@localhost:5432/placeholder"

from app.investigation_ai.processors.event_extractor import EventExtractor


def test_event_extractor_person_and_vehicle():
    extractor = EventExtractor()
    sample_detections = [
        {
            "frame_number": 0,
            "timestamp_seconds": 0.0,
            "object_class": "person",
            "tracking_id": 1,
            "confidence": 0.88,
            "bbox": {"xmin": 50, "ymin": 20, "xmax": 80, "ymax": 150},
        },
        {
            "frame_number": 10,
            "timestamp_seconds": 1.0,
            "object_class": "car",
            "tracking_id": 10,
            "confidence": 0.95,
            "bbox": {"xmin": 100, "ymin": 100, "xmax": 250, "ymax": 200},
        },
        {
            "frame_number": 20,
            "timestamp_seconds": 2.0,
            "object_class": "person",
            "tracking_id": 1,
            "confidence": 0.85,
            "bbox": {"xmin": 60, "ymin": 25, "xmax": 90, "ymax": 155},
        },
    ]

    events = extractor.extract_events(sample_detections, media_id=99)
    assert len(events) >= 3

    event_types = [e["event_type"] for e in events]
    assert "person_detected" in event_types
    assert "vehicle_detected" in event_types
    assert "person_entered_frame" in event_types
    assert "person_exited_frame" in event_types

    # Ensure required fields are present in every event
    for ev in events:
        assert "event_type" in ev
        assert "timestamp_seconds" in ev
        assert "frame_number" in ev
        assert "media_id" in ev
        assert "confidence" in ev
        assert "description" in ev
        # Verify language neutrality (no guilt/crime assertions)
        desc = ev["description"].lower()
        assert "criminal" not in desc
        assert "guilty" not in desc
        assert "suspect" not in desc


def test_event_extractor_person_down_heuristic():
    extractor = EventExtractor()
    fall_detections = [
        {
            "frame_number": 5,
            "timestamp_seconds": 0.5,
            "object_class": "person",
            "tracking_id": 2,
            "confidence": 0.82,
            # Normal upright person: W=30, H=100
            "bbox": {"xmin": 50, "ymin": 20, "xmax": 80, "ymax": 120},
        },
        {
            "frame_number": 15,
            "timestamp_seconds": 1.5,
            "object_class": "person",
            "tracking_id": 2,
            "confidence": 0.78,
            # Horizontal posture / fall: W=120, H=50 (W/H = 2.4 >= 1.25)
            "bbox": {"xmin": 50, "ymin": 100, "xmax": 170, "ymax": 150},
        },
    ]

    events = extractor.extract_events(fall_detections, media_id=100)
    event_types = [e["event_type"] for e in events]
    assert "possible_person_down" in event_types

    down_ev = [e for e in events if e["event_type"] == "possible_person_down"][0]
    assert down_ev["tracking_id"] == 2
    assert down_ev["frame_number"] == 15
    assert "horizontal posture" in down_ev["description"].lower() or "person-down" in down_ev["description"].lower()


if __name__ == "__main__":
    test_event_extractor_person_and_vehicle()
    print("[PASS] test_event_extractor_person_and_vehicle")
    test_event_extractor_person_down_heuristic()
    print("[PASS] test_event_extractor_person_down_heuristic")
    print("ALL EVENT EXTRACTION TESTS PASSED CLEANLY!")
