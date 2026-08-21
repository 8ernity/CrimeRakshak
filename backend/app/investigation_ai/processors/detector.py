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


class YOLODetector:
    """YOLO Object Detector for Crime Scene Image Analysis."""

    def __init__(self, model_path: Optional[str] = None, conf_threshold: Optional[float] = None):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.CONFIDENCE_THRESHOLD

    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """Detect objects (persons, vehicles, items) in an image using YOLO."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at '{image_path}'")

        # Open image with PIL to verify validity and extract dimensions
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
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        class_name = res.names.get(cls_id, f"class_{cls_id}")
                        conf = float(box.conf[0].item())
                        
                        # Get bounding box coordinates [xmin, ymin, xmax, ymax]
                        xyxy = box.xyxy[0].tolist()
                        xmin, ymin, xmax, ymax = xyxy[0], xyxy[1], xyxy[2], xyxy[3]

                        detections.append({
                            "object_class": class_name,
                            "confidence": round(conf, 4),
                            "bbox": {
                                "xmin": round(float(xmin), 2),
                                "ymin": round(float(ymin), 2),
                                "xmax": round(float(xmax), 2),
                                "ymax": round(float(ymax), 2),
                            },
                        })
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
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        class_name = res.names.get(cls_id, f"class_{cls_id}")
                        conf = float(box.conf[0].item())

                        xyxy = box.xyxy[0].tolist()
                        xmin, ymin, xmax, ymax = xyxy[0], xyxy[1], xyxy[2], xyxy[3]

                        detections.append({
                            "object_class": class_name,
                            "confidence": round(conf, 4),
                            "bbox": {
                                "xmin": round(float(xmin), 2),
                                "ymin": round(float(ymin), 2),
                                "xmax": round(float(xmax), 2),
                                "ymax": round(float(ymax), 2),
                            },
                        })
            except Exception as e:
                logger.error(f"Error running YOLO inference on frame ndarray: {e}")

        return detections

