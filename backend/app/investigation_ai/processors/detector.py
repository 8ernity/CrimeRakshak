"""YOLO Object Detection Engine for Investigation AI."""
import logging
import os
from typing import Any, Dict, List, Optional
from PIL import Image

from app.core.config import settings

logger = logging.getLogger("investigation.detector")

_YOLO_MODEL_INSTANCE = None


def get_yolo_model(model_path: Optional[str] = None):
    """Lazy loader for YOLO model singleton."""
    global _YOLO_MODEL_INSTANCE
    if _YOLO_MODEL_INSTANCE is not None:
        return _YOLO_MODEL_INSTANCE

    path = model_path or settings.YOLO_MODEL_PATH
    try:
        from ultralytics import YOLO
        logger.info(f"Loading YOLO model from '{path}'...")
        _YOLO_MODEL_INSTANCE = YOLO(path)
        logger.info("YOLO model loaded successfully.")
        return _YOLO_MODEL_INSTANCE
    except Exception as e:
        logger.error(f"Failed to load YOLO model from '{path}': {e}")
        return None


def _parse_box(box: Any, names: Dict[int, str]) -> Optional[Dict[str, Any]]:
    """Safely parse bounding box, class, confidence, and track ID from an Ultralytics Box object."""
    try:
        if box.cls is None or box.cls.numel() == 0:
            return None
        cls_id = int(box.cls.item()) if box.cls.numel() == 1 else int(box.cls[0].item())
        class_name = names.get(cls_id, f"class_{cls_id}")

        if box.conf is None or box.conf.numel() == 0:
            return None
        conf = float(box.conf.item()) if box.conf.numel() == 1 else float(box.conf[0].item())

        if box.xyxy is None or box.xyxy.numel() < 4:
            return None

        xyxy_vals = box.xyxy.cpu().numpy().reshape(-1).tolist()
        if len(xyxy_vals) < 4:
            return None
        xmin, ymin, xmax, ymax = xyxy_vals[0], xyxy_vals[1], xyxy_vals[2], xyxy_vals[3]

        track_id = None
        if hasattr(box, "id") and box.id is not None and box.id.numel() > 0:
            try:
                track_id = int(box.id.item()) if box.id.numel() == 1 else int(box.id[0].item())
            except Exception:
                track_id = None

        return {
            "tracking_id": track_id,
            "object_class": class_name,
            "confidence": round(conf, 4),
            "bbox": {
                "xmin": round(float(xmin), 2),
                "ymin": round(float(ymin), 2),
                "xmax": round(float(xmax), 2),
                "ymax": round(float(ymax), 2),
            },
        }
    except Exception as e:
        logger.warning(f"Error parsing box: {e}")
        return None


class YOLODetector:
    """YOLO Object Detector for Crime Scene Image & Video Analysis."""

    def __init__(self, model_path: Optional[str] = None, conf_threshold: Optional[float] = None):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.CONFIDENCE_THRESHOLD

    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """Detect objects (persons, vehicles, items) in an image using YOLO."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at '{image_path}'")

        try:
            with Image.open(image_path) as img:
                img_w, img_h = img.size
        except Exception as e:
            raise ValueError(f"Corrupted or unreadable image file '{image_path}': {e}")

        model = get_yolo_model(self.model_path)
        detections: List[Dict[str, Any]] = []

        if model is not None:
            try:
                results = model.predict(source=image_path, conf=self.conf_threshold, verbose=False)
                for res in results:
                    boxes = res.boxes
                    if boxes is None:
                        continue
                    names = res.names or {}
                    for box in boxes:
                        parsed = _parse_box(box, names)
                        if parsed is not None:
                            detections.append(parsed)
            except Exception as e:
                logger.error(f"Error running YOLO inference on '{image_path}': {e}")

        return {
            "image_path": image_path,
            "image_width": img_w,
            "image_height": img_h,
            "total_objects": len(detections),
            "detections": detections,
        }

    def detect_objects_in_ndarray(self, frame_ndarray: Any) -> List[Dict[str, Any]]:
        """Detect objects directly on an in-memory image/frame numpy array."""
        model = get_yolo_model(self.model_path)
        detections: List[Dict[str, Any]] = []

        if model is not None:
            try:
                results = model.predict(source=frame_ndarray, conf=self.conf_threshold, verbose=False)
                for res in results:
                    boxes = res.boxes
                    if boxes is None:
                        continue
                    names = res.names or {}
                    for box in boxes:
                        parsed = _parse_box(box, names)
                        if parsed is not None:
                            detections.append(parsed)
            except Exception as e:
                logger.error(f"Error running YOLO inference on frame ndarray: {e}")

        return detections

    def track_objects_in_ndarray(
        self,
        frame_ndarray: Any,
        tracker: str = "bytetrack.yaml",
        persist: bool = True,
    ) -> List[Dict[str, Any]]:
        """Track objects across consecutive video frames using ByteTrack or BoT-SORT."""
        model = get_yolo_model(self.model_path)
        detections: List[Dict[str, Any]] = []

        if model is not None:
            try:
                results = model.track(
                    source=frame_ndarray,
                    tracker=tracker,
                    persist=persist,
                    conf=self.conf_threshold,
                    verbose=False,
                )
                for res in results:
                    boxes = res.boxes
                    if boxes is None:
                        continue
                    names = res.names or {}
                    for box in boxes:
                        parsed = _parse_box(box, names)
                        if parsed is not None:
                            detections.append(parsed)
            except Exception as e:
                logger.error(f"Error running YOLO tracking on frame ndarray: {e}")

        return detections

    def reset_tracker(self) -> None:
        """Reset internal tracker state by re-initializing predictor instance."""
        model = get_yolo_model(self.model_path)
        if model is not None and hasattr(model, "predictor"):
            model.predictor = None
