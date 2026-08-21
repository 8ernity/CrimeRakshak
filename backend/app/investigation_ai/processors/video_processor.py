"""Video Processing Engine for AI Investigation Support."""
import logging
import os
from typing import Any, Callable, Dict, List, Optional
import cv2

from app.core.config import settings
from app.investigation_ai.processors.base import BaseMediaProcessor
from app.investigation_ai.processors.detector import YOLODetector

logger = logging.getLogger("investigation.video_processor")


class VideoProcessor(BaseMediaProcessor):
    """Processor for crime incident video evidence analysis."""

    def __init__(self, conf_threshold: Optional[float] = None):
        self.detector = YOLODetector(conf_threshold=conf_threshold)

    def process_image(self, image_path: str) -> Dict[str, Any]:
        raise NotImplementedError("Image processing is handled by ImageProcessor.")

    def process_video(
        self,
        video_path: str,
        sample_rate_fps: int = 2,
        tracker_type: str = "bytetrack",
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> Dict[str, Any]:
        """Perform object detection and multi-object tracking on sampled frames of a video file."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at '{video_path}'")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open or read video file at '{video_path}'")

        # Reset tracker state before starting video stream
        self.detector.reset_tracker()
        tracker_cfg = "botsort.yaml" if tracker_type.lower() == "botsort" else "bytetrack.yaml"

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0 or not (fps > 0):
                fps = 30.0  # Fallback to standard 30 FPS if header FPS is invalid

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = round(total_frames / fps, 3) if total_frames > 0 else 0.0

            # Calculate frame sampling step
            step_frames = max(1, int(round(fps / max(1, sample_rate_fps))))

            frame_detections: List[Dict[str, Any]] = []
            sampled_frames_count = 0
            current_frame_idx = 0

            logger.info(
                f"Starting video tracking: '{video_path}' | Tracker: {tracker_cfg} | FPS: {fps:.2f} | Total Frames: {total_frames} | Step: {step_frames}"
            )

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if current_frame_idx % step_frames == 0:
                    timestamp = round(current_frame_idx / fps, 3)
                    dets = self.detector.track_objects_in_ndarray(frame, tracker=tracker_cfg, persist=True)
                    
                    for d in dets:
                        d["frame_number"] = current_frame_idx
                        d["timestamp_seconds"] = timestamp
                        frame_detections.append(d)

                    sampled_frames_count += 1

                    if progress_callback and total_frames > 0:
                        pct = round((current_frame_idx / total_frames) * 100.0, 1)
                        progress_callback(current_frame_idx, total_frames, min(100.0, pct))

                current_frame_idx += 1

            logger.info(
                f"Completed video processing for '{video_path}': {len(frame_detections)} objects detected across {sampled_frames_count} sampled frames."
            )

            return {
                "video_path": video_path,
                "fps": round(float(fps), 2),
                "total_frames": total_frames,
                "duration_seconds": duration_seconds,
                "width": width,
                "height": height,
                "sample_rate_fps": sample_rate_fps,
                "sampled_frames_count": sampled_frames_count,
                "total_detected_objects": len(frame_detections),
                "detections": frame_detections,
            }

        finally:
            cap.release()
