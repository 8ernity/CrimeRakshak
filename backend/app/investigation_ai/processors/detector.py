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


def _parse_box(
    box: Any,
    names: Dict[int, str],
    keypoints_obj: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """Safely parse bounding box, class, confidence, track ID, and pose keypoints from an Ultralytics Box object."""
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

        bbox_dict = {
            "xmin": round(float(xmin), 2),
            "ymin": round(float(ymin), 2),
            "xmax": round(float(xmax), 2),
            "ymax": round(float(ymax), 2),
        }

        res_dict = {
            "tracking_id": track_id,
            "object_class": class_name,
            "confidence": round(conf, 4),
            "bbox": bbox_dict,
        }

        # Associate pose keypoints & estimate posture for person detections
        if class_name == "person":
            from app.investigation_ai.processors.pose_estimator import (
                estimate_posture_from_keypoints,
                parse_ultralytics_pose_keypoints,
            )

            kps = parse_ultralytics_pose_keypoints(keypoints_obj) if keypoints_obj is not None else []
            posture, posture_conf = estimate_posture_from_keypoints(kps, bbox=bbox_dict)
            res_dict["keypoints"] = kps
            res_dict["posture"] = posture
            res_dict["posture_confidence"] = round(posture_conf, 4)

        return res_dict
    except Exception as e:
        logger.warning(f"Error parsing box: {e}")
        return None


class YOLODetector:
    """YOLO Object & Pose Detector for Crime Scene Image & Video Analysis."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        enable_pose: bool = True,
    ):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.CONFIDENCE_THRESHOLD
        self.enable_pose = enable_pose

    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """Detect objects and human pose keypoints in an image using YOLO."""
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
                    keypoints_data = getattr(res, "keypoints", None)

                    for idx, box in enumerate(boxes):
                        kp_obj = keypoints_data[idx] if keypoints_data is not None and idx < len(keypoints_data) else None
                        parsed = _parse_box(box, names, keypoints_obj=kp_obj)
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
        """Detect objects and human poses directly on an in-memory frame numpy array."""
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
                    keypoints_data = getattr(res, "keypoints", None)

                    for idx, box in enumerate(boxes):
                        kp_obj = keypoints_data[idx] if keypoints_data is not None and idx < len(keypoints_data) else None
                        parsed = _parse_box(box, names, keypoints_obj=kp_obj)
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
        """Track objects and human pose keypoints across video frames using ByteTrack."""
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
                    keypoints_data = getattr(res, "keypoints", None)

                    for idx, box in enumerate(boxes):
                        kp_obj = keypoints_data[idx] if keypoints_data is not None and idx < len(keypoints_data) else None
                        parsed = _parse_box(box, names, keypoints_obj=kp_obj)
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

