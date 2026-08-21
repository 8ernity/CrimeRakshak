"""Image Processing Engine for AI Investigation Support."""
import logging
from typing import Any, Dict, Optional

from app.investigation_ai.processors.base import BaseMediaProcessor
from app.investigation_ai.processors.detector import YOLODetector

logger = logging.getLogger("investigation.image_processor")


class ImageProcessor(BaseMediaProcessor):
    """Processor for single image evidence analysis."""

    def __init__(self, conf_threshold: Optional[float] = None):
        self.detector = YOLODetector(conf_threshold=conf_threshold)

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Perform object detection on static image file."""
        logger.info(f"Processing image for investigation analysis: '{image_path}'")
        return self.detector.detect_objects(image_path)

    def process_video(
        self,
        video_path: str,
        sample_rate_fps: int = 2,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Video processing is handled by VideoProcessor.")
