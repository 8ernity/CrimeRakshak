"""Unit & Integration Tests for AI Investigation Report Generator.

Verifies multimodal report pipeline with actual frame extraction from image/video files,
Gemini API invocation (when GEMINI_API_KEY is set), and explicit fallback reason tracking
when LLM is unavailable or fails.

Scenarios tested:
  1. Crime image → actual image frame sent to model / fallback checked
  2. Normal image → actual image frame sent to model / fallback checked
  3. Crime video → actual key frames extracted & sent in chronological order
  4. Normal video → actual key frames extracted & sent in chronological order
  5. Gemini / API failure → deterministic fallback with clear fallback_reason logging
"""

import json
import os
import tempfile
import unittest
import cv2
import numpy as np

from app.core.config import settings
from app.investigation_ai.processors.crime_detection_analyzer import CrimeDetectionAnalyzer
from app.investigation_ai.processors.report_generator import AIReportGenerator, generate_fallback_report


def _build_structured_evidence(
    media_id=1,
    file_name="test_media.mp4",
    file_type="video",
    detections_breakdown=None,
    total_detections=0,
    tracking_results=None,
    investigation_events=None,
):
    return {
        "media_metadata": {
            "media_id": media_id,
            "file_name": file_name,
            "file_type": file_type,
            "duration_seconds": 10.0 if file_type == "video" else None,
            "fps": 30.0 if file_type == "video" else None,
            "total_frames": 300 if file_type == "video" else None,
            "district_id": None,
            "fir_id": None,
            "status": "processed",
        },
        "detection_stats": {
            "total_detections": total_detections,
            "class_breakdown": detections_breakdown or {},
            "class_confidence_summary": {},
        },
        "tracking_results": tracking_results or [],
        "investigation_events": investigation_events or [],
        "fir_metadata": {"status": "No linked FIR case number."},
    }


def _create_temp_image(file_prefix="test_img_"):
    """Create a temporary synthetic JPEG image file."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add colored rectangles for visual content
    cv2.rectangle(img, (50, 50), (200, 200), (0, 255, 0), -1)
    cv2.putText(img, "TEST EVIDENCE IMAGE", (30, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", prefix=file_prefix, delete=False)
    cv2.imwrite(tmp.name, img)
    tmp.close()
    return tmp.name


def _create_temp_video(file_prefix="test_vid_", duration_sec=5.0, fps=30.0):
    """Create a temporary synthetic MP4 video file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", prefix=file_prefix, delete=False)
    tmp.close()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp.name, fourcc, fps, (640, 480))

    total_frames = int(duration_sec * fps)
    for f in range(total_frames):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"FRAME {f} t={f/fps:.2f}s", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        out.write(img)

    out.release()
    return tmp.name


class TestAIReportGenerator(unittest.TestCase):

    def setUp(self):
        self.analyzer = CrimeDetectionAnalyzer()
        self.generator = AIReportGenerator()
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def _print_report_summary(self, test_name: str, report: dict):
        print(f"\n============================================================")
        print(f"REPORT OUTPUT: {test_name}")
        print(f"============================================================")
        print(f"provider_used:            {report.get('provider_used')}")
        print(f"frames_supplied_to_model: {report.get('frames_supplied_to_model')}")
        print(f"evidence_frame_references: {json.dumps(report.get('evidence_frame_references'), indent=2)}")
        print(f"incident_classification:   {report.get('incident_classification')}")
        print(f"executive_summary:         {report.get('executive_summary')}")
        print(f"uncertainty_notes:         {json.dumps(report.get('uncertainty_notes'), indent=2)}")
        print(f"fallback_reason:           {report.get('fallback_reason')}")

    # ─── Test 1: Crime Image ───
    def test_1_crime_image_report(self):
        """Test crime image: passes real image file, checks frame extraction & report generation."""
        img_path = _create_temp_image("crime_img_")
        self.temp_files.append(img_path)

        detections = [
            {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.91, "posture": "standing"},
            {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "knife",
             "tracking_id": 2, "confidence": 0.87, "posture": None},
        ]
        events = []

        crime_detection = self.analyzer.analyze_video_evidence(
            detections=detections, events=events, is_video=False, media_id=301)

        structured_evidence = _build_structured_evidence(
            media_id=301, file_name=os.path.basename(img_path), file_type="image",
            detections_breakdown={"person": 1, "knife": 1}, total_detections=2,
            tracking_results=[
                {"tracking_id": 1, "object_class": "person", "start_timestamp_seconds": 0.0,
                 "end_timestamp_seconds": 0.0, "duration_active_seconds": 0, "active_frames": "0 - 0",
                 "detection_count": 1, "average_confidence": 0.91},
                {"tracking_id": 2, "object_class": "knife", "start_timestamp_seconds": 0.0,
                 "end_timestamp_seconds": 0.0, "duration_active_seconds": 0, "active_frames": "0 - 0",
                 "detection_count": 1, "average_confidence": 0.87},
            ],
        )

        report = self.generator.generate_report(
            structured_evidence=structured_evidence,
            crime_detection=crime_detection,
            media_file_path=img_path,
            is_video=False,
            media_id=301,
        )

        self._print_report_summary("Test 1: Crime Image", report)

        self.assertEqual(report["frames_supplied_to_model"], 1)
        self.assertGreater(len(report["evidence_frame_references"]), 0)
        self.assertIn("Possible", report["incident_classification"])
        if report["provider_used"] == "deterministic_fallback":
            self.assertIsNotNone(report["fallback_reason"])

    # ─── Test 2: Normal Image ───
    def test_2_normal_image_report(self):
        """Test normal image: passes real image file, checks frame extraction & normal classification."""
        img_path = _create_temp_image("normal_img_")
        self.temp_files.append(img_path)

        detections = [
            {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.94, "posture": "standing"},
        ]
        events = []

        crime_detection = self.analyzer.analyze_video_evidence(
            detections=detections, events=events, is_video=False, media_id=302)

        structured_evidence = _build_structured_evidence(
            media_id=302, file_name=os.path.basename(img_path), file_type="image",
            detections_breakdown={"person": 1}, total_detections=1,
            tracking_results=[
                {"tracking_id": 1, "object_class": "person", "start_timestamp_seconds": 0.0,
                 "end_timestamp_seconds": 0.0, "duration_active_seconds": 0, "active_frames": "0 - 0",
                 "detection_count": 1, "average_confidence": 0.94},
            ],
        )

        report = self.generator.generate_report(
            structured_evidence=structured_evidence,
            crime_detection=crime_detection,
            media_file_path=img_path,
            is_video=False,
            media_id=302,
        )

        self._print_report_summary("Test 2: Normal Image", report)

        self.assertEqual(report["frames_supplied_to_model"], 1)
        self.assertGreater(len(report["evidence_frame_references"]), 0)
        self.assertEqual(report["incident_classification"], "No Criminal Activity Observed")

    # ─── Test 3: Crime Video ───
    def test_3_crime_video_report(self):
        """Test crime video: extracts key frames at event timestamps from video file."""
        vid_path = _create_temp_video("crime_vid_", duration_sec=6.0)
        self.temp_files.append(vid_path)

        detections = [
            {"frame_number": 30, "timestamp_seconds": 1.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.92, "posture": "standing"},
            {"frame_number": 90, "timestamp_seconds": 3.0, "object_class": "knife",
             "tracking_id": 2, "confidence": 0.88, "posture": None},
            {"frame_number": 150, "timestamp_seconds": 5.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.85, "posture": "lying_down"},
        ]
        events = [
            {"event_type": "pattern_multi_person_interaction",
             "description": "Multi-person close proximity interaction",
             "start_timestamp_seconds": 2.5, "end_timestamp_seconds": 4.0,
             "tracking_id": 1, "confidence": 0.86},
            {"event_type": "possible_person_down",
             "description": "Person down posture anomaly detected",
             "start_timestamp_seconds": 4.5, "end_timestamp_seconds": 5.5,
             "tracking_id": 1, "confidence": 0.89},
        ]

        crime_detection = self.analyzer.analyze_video_evidence(
            detections=detections, events=events, is_video=True, media_id=303)

        structured_evidence = _build_structured_evidence(
            media_id=303, file_name=os.path.basename(vid_path), file_type="video",
            detections_breakdown={"person": 2, "knife": 1}, total_detections=3,
            tracking_results=[
                {"tracking_id": 1, "object_class": "person", "start_timestamp_seconds": 1.0,
                 "end_timestamp_seconds": 5.0, "duration_active_seconds": 4.0, "active_frames": "30 - 150",
                 "detection_count": 2, "average_confidence": 0.89},
                {"tracking_id": 2, "object_class": "knife", "start_timestamp_seconds": 3.0,
                 "end_timestamp_seconds": 3.0, "duration_active_seconds": 0, "active_frames": "90 - 90",
                 "detection_count": 1, "average_confidence": 0.88},
            ],
            investigation_events=events,
        )

        report = self.generator.generate_report(
            structured_evidence=structured_evidence,
            crime_detection=crime_detection,
            media_file_path=vid_path,
            is_video=True,
            media_id=303,
        )

        self._print_report_summary("Test 3: Crime Video", report)

        self.assertGreater(report["frames_supplied_to_model"], 0)
        self.assertGreater(len(report["evidence_frame_references"]), 0)
        self.assertIn("Possible", report["incident_classification"])

    # ─── Test 4: Normal Video ───
    def test_4_normal_video_report(self):
        """Test normal video: extracts key frames at routine timestamps from video file."""
        vid_path = _create_temp_video("normal_vid_", duration_sec=4.0)
        self.temp_files.append(vid_path)

        detections = [
            {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.94, "posture": "walking"},
            {"frame_number": 60, "timestamp_seconds": 2.0, "object_class": "car",
             "tracking_id": 2, "confidence": 0.96, "posture": None},
        ]
        events = [
            {"event_type": "person_entered_frame",
             "description": "Subject entered frame walking along sidewalk",
             "start_timestamp_seconds": 0.0, "end_timestamp_seconds": 1.0,
             "tracking_id": 1, "confidence": 0.92},
        ]

        crime_detection = self.analyzer.analyze_video_evidence(
            detections=detections, events=events, is_video=True, media_id=304)

        structured_evidence = _build_structured_evidence(
            media_id=304, file_name=os.path.basename(vid_path), file_type="video",
            detections_breakdown={"person": 1, "car": 1}, total_detections=2,
            tracking_results=[
                {"tracking_id": 1, "object_class": "person", "start_timestamp_seconds": 0.0,
                 "end_timestamp_seconds": 2.0, "duration_active_seconds": 2.0, "active_frames": "0 - 60",
                 "detection_count": 1, "average_confidence": 0.94},
                {"tracking_id": 2, "object_class": "car", "start_timestamp_seconds": 2.0,
                 "end_timestamp_seconds": 2.0, "duration_active_seconds": 0, "active_frames": "60 - 60",
                 "detection_count": 1, "average_confidence": 0.96},
            ],
            investigation_events=events,
        )

        report = self.generator.generate_report(
            structured_evidence=structured_evidence,
            crime_detection=crime_detection,
            media_file_path=vid_path,
            is_video=True,
            media_id=304,
        )

        self._print_report_summary("Test 4: Normal Video", report)

        self.assertGreater(report["frames_supplied_to_model"], 0)
        self.assertGreater(len(report["evidence_frame_references"]), 0)
        self.assertEqual(report["incident_classification"], "No Criminal Activity Observed")

    # ─── Test 5: Gemini / API Failure Fallback ───
    def test_5_api_failure_fallback(self):
        """Test API failure fallback: forces missing/invalid API key and verifies fallback_reason logging."""
        img_path = _create_temp_image("fail_img_")
        self.temp_files.append(img_path)

        detections = [
            {"frame_number": 0, "timestamp_seconds": 0.0, "object_class": "person",
             "tracking_id": 1, "confidence": 0.91, "posture": "standing"},
        ]
        crime_detection = self.analyzer.analyze_video_evidence(
            detections=detections, events=[], is_video=False, media_id=305)

        structured_evidence = _build_structured_evidence(
            media_id=305, file_name=os.path.basename(img_path), file_type="image",
            detections_breakdown={"person": 1}, total_detections=1,
        )

        # Save original API key and temporarily set to empty
        orig_key = settings.GEMINI_API_KEY
        try:
            settings.GEMINI_API_KEY = ""

            report = self.generator.generate_report(
                structured_evidence=structured_evidence,
                crime_detection=crime_detection,
                media_file_path=img_path,
                is_video=False,
                media_id=305,
            )

            self._print_report_summary("Test 5: API Failure Fallback", report)

            self.assertEqual(report["provider_used"], "deterministic_fallback")
            self.assertEqual(report["frames_supplied_to_model"], 1)
            self.assertGreater(len(report["evidence_frame_references"]), 0)
            self.assertIsNotNone(report["fallback_reason"])
            self.assertIn("GEMINI_API_KEY", report["fallback_reason"])
        finally:
            settings.GEMINI_API_KEY = orig_key


if __name__ == "__main__":
    unittest.main()
