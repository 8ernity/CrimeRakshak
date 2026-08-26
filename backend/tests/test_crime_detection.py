"""Unit & Integration Tests for Crime Video Detection Decision Layer.

Verifies classification, confidence calculation, indicator extraction, timestamp merging,
and evidence event aggregation for both crime-like and normal/non-crime video inputs.
"""

import unittest
from app.investigation_ai.processors.crime_detection_analyzer import CrimeDetectionAnalyzer


class TestCrimeVideoDetection(unittest.TestCase):

    def setUp(self):
        self.analyzer = CrimeDetectionAnalyzer()

    def test_crime_like_video_analysis(self):
        """Test 1: Crime-like video containing weapon detection, fall/person-down, and physical altercation."""
        detections = [
            {
                "frame_number": 30,
                "timestamp_seconds": 1.0,
                "object_class": "person",
                "tracking_id": 1,
                "confidence": 0.92,
                "posture": "standing",
            },
            {
                "frame_number": 90,
                "timestamp_seconds": 3.0,
                "object_class": "knife",
                "tracking_id": 2,
                "confidence": 0.88,
                "posture": None,
            },
            {
                "frame_number": 240,
                "timestamp_seconds": 8.0,
                "object_class": "person",
                "tracking_id": 1,
                "confidence": 0.85,
                "posture": "lying_down",
            },
        ]

        events = [
            {
                "event_type": "pattern_multi_person_interaction",
                "description": "Multi-person close proximity interaction with sudden posture change",
                "start_timestamp_seconds": 2.5,
                "end_timestamp_seconds": 6.0,
                "tracking_id": 1,
                "confidence": 0.86,
            },
            {
                "event_type": "possible_person_down",
                "description": "Person down posture anomaly detected following physical conflict",
                "start_timestamp_seconds": 7.5,
                "end_timestamp_seconds": 11.0,
                "tracking_id": 1,
                "confidence": 0.89,
            },
        ]

        result = self.analyzer.analyze_video_evidence(
            detections=detections,
            events=events,
            is_video=True,
            media_id=101,
        )

        print("\n========================================================")
        print("TEST 1 OUTPUT: Crime-like Video Evidence Analysis")
        print("========================================================")
        import json
        print(json.dumps(result, indent=2))

        # Assertions
        self.assertEqual(result["classification"], "possible_crime")
        self.assertGreaterEqual(result["confidence"], 0.85)
        self.assertIn("weapon_detected", result["crime_indicators"])
        self.assertIn("possible_person_down", result["crime_indicators"])
        self.assertIn("aggressive_physical_interaction", result["crime_indicators"])
        self.assertIn("multiple_correlated_events", result["crime_indicators"])
        self.assertGreater(len(result["relevant_timestamps"]), 0)
        self.assertGreater(len(result["evidence_events"]), 0)

    def test_normal_video_analysis(self):
        """Test 2: Normal / Non-crime video containing routine walking, vehicle proximity, and no visual anomalies."""
        detections = [
            {
                "frame_number": 0,
                "timestamp_seconds": 0.0,
                "object_class": "person",
                "tracking_id": 1,
                "confidence": 0.94,
                "posture": "walking",
            },
            {
                "frame_number": 60,
                "timestamp_seconds": 2.0,
                "object_class": "car",
                "tracking_id": 2,
                "confidence": 0.96,
                "posture": None,
            },
            {
                "frame_number": 150,
                "timestamp_seconds": 5.0,
                "object_class": "person",
                "tracking_id": 1,
                "confidence": 0.91,
                "posture": "standing",
            },
        ]

        events = [
            {
                "event_type": "person_entered_frame",
                "description": "Subject (Track #1) entered frame walking along sidewalk",
                "start_timestamp_seconds": 0.0,
                "end_timestamp_seconds": 1.0,
                "tracking_id": 1,
                "confidence": 0.92,
            },
            {
                "event_type": "pattern_entry_activity_exit",
                "description": "Routine entry and transit across camera view",
                "start_timestamp_seconds": 1.0,
                "end_timestamp_seconds": 5.5,
                "tracking_id": 1,
                "confidence": 0.90,
            },
        ]

        result = self.analyzer.analyze_video_evidence(
            detections=detections,
            events=events,
            is_video=True,
            media_id=102,
        )

        print("\n========================================================")
        print("TEST 2 OUTPUT: Normal / Non-Crime Video Evidence Analysis")
        print("========================================================")
        import json
        print(json.dumps(result, indent=2))

        # Assertions
        self.assertEqual(result["classification"], "no_clear_crime_evidence")
        self.assertGreaterEqual(result["confidence"], 0.85)
        self.assertEqual(result["crime_indicators"], [])
        self.assertEqual(result["relevant_timestamps"], [])
        self.assertEqual(result["evidence_events"], [])


if __name__ == "__main__":
    unittest.main()
