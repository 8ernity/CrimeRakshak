"""Unit tests for CrimeDecisionEngine in Investigation AI."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.investigation_ai.processors.crime_decision_engine import CrimeDecisionEngine


def test_clear_suspicious_sequence_potential_crime():
    """Test 1: Clear suspicious sequence (rapid chase + physical interaction + fall) -> potential_crime."""
    engine = CrimeDecisionEngine()

    detections = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.85},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.88},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 2.0, "confidence": 0.90},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 2.0, "confidence": 0.91},
    ]

    events = [
        {
            "event_type": "posture_falling",
            "timestamp_seconds": 2.5,
            "tracking_id": 1,
            "confidence": 0.88,
        },
        {
            "event_type": "posture_lying_down",
            "timestamp_seconds": 3.0,
            "tracking_id": 1,
            "confidence": 0.85,
        },
    ]

    temporal_events = [
        {
            "event_type": "pattern_rapid_movement_chase",
            "timestamp_seconds": 1.5,
            "tracking_id": 1,
            "confidence": 0.80,
        },
        {
            "event_type": "pattern_multi_person_interaction",
            "timestamp_seconds": 2.0,
            "tracking_id": 1,
            "confidence": 0.85,
        },
        {
            "event_type": "pattern_fall_lying_down",
            "timestamp_seconds": 2.5,
            "tracking_id": 1,
            "confidence": 0.88,
        },
    ]

    result = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=temporal_events,
        is_video=True,
        media_id=101,
    )

    print("\nTest 1 (Suspicious Sequence):", result)
    assert result["decision"] == "potential_crime", f"Expected potential_crime, got {result['decision']}"
    assert result["confidence"] >= 0.75
    assert result["evidence_score"] >= 0.55
    assert 1 in result["track_ids"]
    assert 2 in result["track_ids"]
    assert len(result["timestamps"]) > 0
    print("[PASS] Clear suspicious sequence -> potential_crime")


def test_normal_walking_non_crime():
    """Test 2: Normal walking / routine standing -> non_crime."""
    engine = CrimeDecisionEngine()

    detections = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 0.5, "confidence": 0.92},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.93},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.5, "confidence": 0.91},
    ]

    events = [
        {
            "event_type": "person_entered_frame",
            "timestamp_seconds": 0.5,
            "tracking_id": 1,
            "confidence": 0.92,
        },
        {
            "event_type": "posture_standing",
            "timestamp_seconds": 1.0,
            "tracking_id": 1,
            "confidence": 0.93,
        },
        {
            "event_type": "person_exited_frame",
            "timestamp_seconds": 1.5,
            "tracking_id": 1,
            "confidence": 0.91,
        },
    ]

    temporal_events = [
        {
            "event_type": "pattern_entry_activity_exit",
            "timestamp_seconds": 0.5,
            "tracking_id": 1,
            "confidence": 0.90,
        }
    ]

    result = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=temporal_events,
        is_video=True,
        media_id=102,
    )

    print("\nTest 2 (Normal Walking):", result)
    assert result["decision"] == "non_crime", f"Expected non_crime, got {result['decision']}"
    assert "NORMAL_ACTIVITY_ONLY" in result["safeguards_triggered"]
    print("[PASS] Normal walking -> non_crime")


def test_lying_down_alone_non_crime_or_uncertain():
    """Test 3: Lying down alone without physical assault or pursuit -> non_crime/uncertain."""
    engine = CrimeDecisionEngine()

    detections = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.85},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 2.0, "confidence": 0.86},
    ]

    events = [
        {
            "event_type": "posture_lying_down",
            "timestamp_seconds": 1.5,
            "tracking_id": 1,
            "confidence": 0.85,
        },
        {
            "event_type": "possible_person_down",
            "timestamp_seconds": 1.5,
            "tracking_id": 1,
            "confidence": 0.80,
        },
    ]

    temporal_events = [
        {
            "event_type": "pattern_fall_lying_down",
            "timestamp_seconds": 1.5,
            "tracking_id": 1,
            "confidence": 0.82,
        }
    ]

    result_video = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=temporal_events,
        is_video=True,
        media_id=103,
    )

    print("\nTest 3 (Lying Down Alone Video):", result_video)
    assert result_video["decision"] in ("non_crime", "uncertain"), (
        f"Expected non_crime/uncertain, got {result_video['decision']}"
    )
    assert result_video["decision"] != "potential_crime"
    assert "ISOLATED_FALL_OR_LYING_DOWN" in result_video["safeguards_triggered"]

    # Image test
    result_image = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=[],
        is_video=False,
        media_id=104,
    )

    print("Test 3 (Lying Down Alone Image):", result_image)
    assert result_image["decision"] in ("non_crime", "uncertain")
    assert result_image["decision"] != "potential_crime"
    print("[PASS] Lying down alone -> non_crime / uncertain")


def test_ambiguous_interaction_uncertain():
    """Test 4: Ambiguous interaction (approach -> interaction -> leave) without violence/chase/fall -> uncertain."""
    engine = CrimeDecisionEngine()

    detections = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.88},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.89},
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 3.0, "confidence": 0.88},
        {"tracking_id": 2, "object_class": "person", "timestamp_seconds": 3.0, "confidence": 0.89},
    ]

    events = [
        {"event_type": "posture_standing", "timestamp_seconds": 1.0, "tracking_id": 1, "confidence": 0.88},
        {"event_type": "posture_standing", "timestamp_seconds": 1.0, "tracking_id": 2, "confidence": 0.89},
    ]

    temporal_events = [
        {
            "event_type": "pattern_approach_interaction_leave",
            "timestamp_seconds": 2.0,
            "tracking_id": 1,
            "confidence": 0.75,
        },
        {
            "event_type": "pattern_person_following",
            "timestamp_seconds": 1.5,
            "tracking_id": 2,
            "confidence": 0.70,
        },
    ]

    result = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=temporal_events,
        is_video=True,
        media_id=105,
    )

    print("\nTest 4 (Ambiguous Interaction):", result)
    assert result["decision"] == "uncertain", f"Expected uncertain, got {result['decision']}"
    assert "AMBIGUOUS_INTERACTION_NO_VIOLENCE" in result["safeguards_triggered"]
    print("[PASS] Ambiguous interaction -> uncertain")


def test_person_vehicle_overlap_alone_non_crime():
    """Test 5: Person + vehicle overlap alone (pedestrian walking past car) -> non_crime."""
    engine = CrimeDecisionEngine()

    detections = [
        {"tracking_id": 1, "object_class": "person", "timestamp_seconds": 1.0, "confidence": 0.90},
        {"tracking_id": 2, "object_class": "car", "timestamp_seconds": 1.0, "confidence": 0.95},
    ]

    events = [
        {"event_type": "vehicle_detected", "timestamp_seconds": 1.0, "tracking_id": 2, "confidence": 0.95},
        {"event_type": "posture_standing", "timestamp_seconds": 1.0, "tracking_id": 1, "confidence": 0.90},
    ]

    temporal_events = [
        {
            "event_type": "pattern_person_vehicle_interaction",
            "timestamp_seconds": 1.0,
            "tracking_id": 1,
            "confidence": 0.80,
        }
    ]

    result = engine.evaluate_decision(
        detections=detections,
        events=events,
        temporal_events=temporal_events,
        is_video=True,
        media_id=106,
    )

    print("\nTest 5 (Person + Vehicle Overlap Alone):", result)
    assert result["decision"] == "non_crime", f"Expected non_crime, got {result['decision']}"
    assert "PERSON_VEHICLE_OVERLAP_ONLY" in result["safeguards_triggered"]
    print("[PASS] Person + vehicle overlap alone -> non_crime")


if __name__ == "__main__":
    test_clear_suspicious_sequence_potential_crime()
    test_normal_walking_non_crime()
    test_lying_down_alone_non_crime_or_uncertain()
    test_ambiguous_interaction_uncertain()
    test_person_vehicle_overlap_alone_non_crime()
    print("\n==========================================")
    print("ALL CRIME DECISION ENGINE TESTS PASSED!")
    print("==========================================")
