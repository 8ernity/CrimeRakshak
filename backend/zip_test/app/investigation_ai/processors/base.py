"""Abstract base interfaces for image and video processing engines."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMediaProcessor(ABC):
    """Abstract base class for vision processing engines."""

    @abstractmethod
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process single static image file."""
        pass

    @abstractmethod
    def process_video(
        self,
        video_path: str,
        sample_rate_fps: int = 2,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Process video file with frame sampling and object tracking."""
        pass
