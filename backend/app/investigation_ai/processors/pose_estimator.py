"""YOLOv8 Pose Estimation & Posture Analysis Module.

Detects human body keypoints (17 COCO keypoints), associates them with tracking IDs,
and estimates basic human posture states:
- standing
- sitting
- lying_down
- falling
- running
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger("investigation.pose_estimator")

COCO_KEYPOINTS = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]

_YOLO_POSE_MODEL_INSTANCE = None


def get_yolo_pose_model(model_path: Optional[str] = None):
    """Lazy loader for YOLOv8 Pose model singleton."""
    global _YOLO_POSE_MODEL_INSTANCE
    if _YOLO_POSE_MODEL_INSTANCE is not None:
        return _YOLO_POSE_MODEL_INSTANCE

    path = model_path or getattr(settings, "YOLO_POSE_MODEL_PATH", "yolov8n-pose.pt")
    try:
        from ultralytics import YOLO

        logger.info(f"Loading YOLO Pose model from '{path}'...")
        _YOLO_POSE_MODEL_INSTANCE = YOLO(path)
        logger.info("YOLO Pose model loaded successfully.")
        return _YOLO_POSE_MODEL_INSTANCE
    except Exception as e:
        logger.warning(f"Could not load YOLO Pose model from '{path}': {e}")
        return None


def estimate_posture_from_keypoints(
    keypoints: List[Dict[str, Any]],
    bbox: Optional[Dict[str, float]] = None,
) -> Tuple[str, float]:
    """Determine posture state ('standing', 'sitting', 'lying_down', 'falling', 'running')
    based on 17 COCO keypoints and fallback bounding box geometry.
    """
    kp_map = {kp["name"]: kp for kp in keypoints if kp.get("conf", 0.0) >= 0.2}

    def get_pt(name: str) -> Optional[Tuple[float, float]]:
        item = kp_map.get(name)
        return (item["x"], item["y"]) if item else None

    l_sh, r_sh = get_pt("left_shoulder"), get_pt("right_shoulder")
    l_hip, r_hip = get_pt("left_hip"), get_pt("right_hip")
    l_knee, r_knee = get_pt("left_knee"), get_pt("right_knee")
    l_ank, r_ank = get_pt("left_ankle"), get_pt("right_ankle")

    def mid_pt(
        p1: Optional[Tuple[float, float]], p2: Optional[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        if p1 and p2:
            return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
        return p1 or p2

    sh = mid_pt(l_sh, r_sh)
    hip = mid_pt(l_hip, r_hip)
    knee = mid_pt(l_knee, r_knee)
    ank = mid_pt(l_ank, r_ank)

    # 1. Keypoint-based evaluation if both shoulder and hip are reliable
    if sh and hip:
        dx = abs(sh[0] - hip[0])
        dy = abs(sh[1] - hip[1])  # note: y increases downwards in pixel space

        torso_len = math.hypot(dx, dy)
        if torso_len > 5.0:
            # Angle relative to vertical axis (0 deg = straight up, 90 deg = horizontal)
            torso_angle = math.degrees(math.atan2(dx, dy))

            # Lying Down: Torso is close to horizontal (>= 55 deg or dy < 0.5 * dx)
            if torso_angle >= 55.0 or (dy < 0.5 * dx):
                return "lying_down", 0.90

            # Falling: High angle tilt (40-55 deg) with head/shoulders low or drooping
            if 40.0 <= torso_angle < 55.0:
                if sh[1] >= hip[1] - 15.0:
                    return "falling", 0.85

            # Sitting: Upright/moderate torso, but knees at similar y-level to hips and ankles lower
            if torso_angle < 45.0 and knee:
                hip_knee_dy = abs(knee[1] - hip[1])
                if hip_knee_dy < 0.55 * torso_len:
                    if ank and ank[1] > knee[1]:
                        return "sitting", 0.88

            # Running: Upright/forward lean, wide leg stride (ankle spread >= 0.65 * torso_len)
            if l_ank and r_ank and torso_angle <= 40.0:
                stride = abs(l_ank[0] - r_ank[0])
                if stride >= 0.65 * torso_len:
                    return "running", 0.85

            # Falling: Moderate tilt off balance
            if 40.0 <= torso_angle < 55.0:
                return "falling", 0.80

            # Default upright posture
            return "standing", 0.92

    # 2. Fallback Bounding Box Aspect Ratio Heuristic
    if bbox and isinstance(bbox, dict):
        xmin = bbox.get("xmin", 0.0)
        ymin = bbox.get("ymin", 0.0)
        xmax = bbox.get("xmax", 0.0)
        ymax = bbox.get("ymax", 0.0)
        w = abs(xmax - xmin)
        h = abs(ymax - ymin)
        if h > 0:
            aspect_ratio = w / h
            if aspect_ratio >= 1.25:
                return "lying_down", 0.70
            elif aspect_ratio <= 0.55:
                return "standing", 0.75

    return "standing", 0.60


def parse_ultralytics_pose_keypoints(keypoint_tensor: Any) -> List[Dict[str, Any]]:
    """Parse keypoints tensor from Ultralytics Pose result into list of 17 keypoint dicts."""
    parsed: List[Dict[str, Any]] = []
    if keypoint_tensor is None:
        return parsed

    try:
        if hasattr(keypoint_tensor, "xy"):
            xy = keypoint_tensor.xy.cpu().numpy()
            conf = (
                keypoint_tensor.conf.cpu().numpy()
                if hasattr(keypoint_tensor, "conf") and keypoint_tensor.conf is not None
                else None
            )

            # Squeeze batch dimension if present
            if len(xy.shape) == 3:
                xy = xy[0]
            if conf is not None and len(conf.shape) == 2:
                conf = conf[0]

            for idx, (x, y) in enumerate(xy):
                kp_name = COCO_KEYPOINTS[idx] if idx < len(COCO_KEYPOINTS) else f"kp_{idx}"
                kp_conf = float(conf[idx]) if conf is not None and idx < len(conf) else 1.0
                parsed.append(
                    {
                        "name": kp_name,
                        "x": round(float(x), 2),
                        "y": round(float(y), 2),
                        "conf": round(kp_conf, 4),
                    }
                )
    except Exception as e:
        logger.warning(f"Failed to parse Ultralytics keypoints: {e}")

    return parsed
