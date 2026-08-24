"""Temporal Event & Action Pattern Analysis Module.

Analyzes object trajectories, postures, and spatial interactions across consecutive video frames
for tracked subjects (ByteTrack tracking IDs) to identify structured potential incident patterns.

Maintains strict investigative neutrality without asserting criminal guilt or single-frame conclusions.
"""
import logging
import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("investigation.temporal_analyzer")

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}


def _center(bbox: Dict[str, float]) -> Tuple[float, float]:
    """Calculate center coordinate (cx, cy) from bounding box."""
    xmin = bbox.get("xmin", 0.0)
    ymin = bbox.get("ymin", 0.0)
    xmax = bbox.get("xmax", 0.0)
    ymax = bbox.get("ymax", 0.0)
    return ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)


def _bbox_iou(boxA: Dict[str, float], boxB: Dict[str, float]) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes."""
    xA = max(boxA.get("xmin", 0.0), boxB.get("xmin", 0.0))
    yA = max(boxA.get("ymin", 0.0), boxB.get("ymin", 0.0))
    xB = min(boxA.get("xmax", 0.0), boxB.get("xmax", 0.0))
    yB = min(boxA.get("ymax", 0.0), boxB.get("ymax", 0.0))

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA.get("xmax", 0.0) - boxA.get("xmin", 0.0)) * (boxA.get("ymax", 0.0) - boxA.get("ymin", 0.0))
    boxBArea = (boxB.get("xmax", 0.0) - boxB.get("xmin", 0.0)) * (boxB.get("ymax", 0.0) - boxB.get("ymin", 0.0))

    unionArea = boxAArea + boxBArea - interArea
    return interArea / unionArea if unionArea > 0 else 0.0


class TemporalAnalyzer:
    """Temporal Sequence Analyzer for multi-frame action pattern detection."""

    def analyze_temporal_patterns(
        self,
        detections: List[Dict[str, Any]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Extract structured potential incident patterns from sorted detections."""
        patterns: List[Dict[str, Any]] = []
        if not detections:
            return patterns

        # Group detections by track ID and by frame
        person_tracks: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        vehicle_tracks: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        frame_detections: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        for det in detections:
            f_num = det.get("frame_number", 0)
            frame_detections[f_num].append(det)

            tid = det.get("tracking_id")
            if tid is not None:
                obj_cls = (det.get("object_class") or "").lower()
                if obj_cls == "person":
                    person_tracks[tid].append(det)
                elif obj_cls in VEHICLE_CLASSES:
                    vehicle_tracks[tid].append(det)

        # 1. Fall -> Lying Down Pattern
        patterns.extend(self._detect_fall_lying_down_pattern(person_tracks, media_id))

        # 2. Approach -> Interaction -> Leave Pattern
        patterns.extend(self._detect_approach_interaction_leave(person_tracks, media_id))

        # 3. Person Following Pattern
        patterns.extend(self._detect_person_following(person_tracks, media_id))

        # 4. Rapid Movement / Chase-like Sequence
        patterns.extend(self._detect_rapid_movement_chase(person_tracks, media_id))

        # 5. Multi-Person Physical Interaction Pattern
        patterns.extend(self._detect_multi_person_interaction(person_tracks, media_id))

        # 6. Person -> Vehicle / Object Interaction Pattern
        patterns.extend(self._detect_person_vehicle_interaction(person_tracks, vehicle_tracks, media_id))

        # 7. Entry -> Activity -> Exit Trajectory Pattern
        patterns.extend(self._detect_entry_activity_exit(person_tracks, media_id))

        # Sort patterns chronologically
        patterns.sort(key=lambda p: (p.get("timestamp_seconds", 0.0), p.get("frame_number", 0)))
        logger.info(f"Extracted {len(patterns)} temporal pattern events for media ID {media_id}.")
        return patterns

    def _detect_fall_lying_down_pattern(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: standing/running -> falling -> lying_down sequence."""
        events: List[Dict[str, Any]] = []

        for tid, dets in person_tracks.items():
            if len(dets) < 2:
                continue

            sorted_dets = sorted(dets, key=lambda d: d.get("frame_number", 0))
            posture_seq = [(d.get("posture"), d.get("timestamp_seconds", 0.0), d.get("frame_number", 0)) for d in sorted_dets]

            has_fall = False
            fall_start_t = 0.0
            fall_start_f = 0

            for posture, ts, fn in posture_seq:
                if posture in ("falling", "lying_down") and not has_fall:
                    has_fall = True
                    fall_start_t = ts
                    fall_start_f = fn
                elif has_fall and posture == "lying_down":
                    events.append({
                        "event_type": "pattern_fall_lying_down",
                        "timestamp_seconds": fall_start_t,
                        "end_timestamp_seconds": ts,
                        "frame_number": fall_start_f,
                        "media_id": media_id,
                        "tracking_id": tid,
                        "confidence": 0.88,
                        "pattern_name": "fall_lying_down",
                        "description": f"Potential incident pattern: Track #{tid} exhibited fall transition to lying_down from timestamp {fall_start_t:.1f}s to {ts:.1f}s.",
                    })
                    break

        return events

    def _detect_approach_interaction_leave(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: approach -> interaction -> leave between two tracked persons."""
        events: List[Dict[str, Any]] = []
        track_ids = sorted(list(person_tracks.keys()))

        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                tidA, tidB = track_ids[i], track_ids[j]
                detsA = {d["frame_number"]: d for d in person_tracks[tidA]}
                detsB = {d["frame_number"]: d for d in person_tracks[tidB]}

                common_frames = sorted(list(set(detsA.keys()).intersection(set(detsB.keys()))))
                if len(common_frames) < 3:
                    continue

                distances = []
                for f in common_frames:
                    cA = _center(detsA[f]["bbox"])
                    cB = _center(detsB[f]["bbox"])
                    dist = math.hypot(cA[0] - cB[0], cA[1] - cB[1])
                    ts = detsA[f]["timestamp_seconds"]
                    distances.append((dist, ts, f))

                # Check pattern: distance decreases -> stays low (<100px) -> increases
                min_dist_idx = min(range(len(distances)), key=lambda idx: distances[idx][0])
                min_dist, min_ts, min_f = distances[min_dist_idx]

                if min_dist < 100.0 and len(distances) >= 3:
                    initial_dist = distances[0][0]
                    final_dist = distances[-1][0]
                    if initial_dist > min_dist + 30.0 and final_dist > min_dist + 30.0:
                        t_start = distances[0][1]
                        t_end = distances[-1][1]
                        events.append({
                            "event_type": "pattern_approach_interaction_leave",
                            "timestamp_seconds": t_start,
                            "end_timestamp_seconds": t_end,
                            "frame_number": distances[0][2],
                            "media_id": media_id,
                            "tracking_id": tidA,
                            "secondary_tracking_id": tidB,
                            "confidence": 0.85,
                            "pattern_name": "approach_interaction_leave",
                            "description": f"Potential incident pattern: Approach -> interaction -> leave sequence between Track #{tidA} and Track #{tidB} from {t_start:.1f}s to {t_end:.1f}s.",
                        })

        return events

    def _detect_person_following(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: person A following trajectory of person B for multiple consecutive frames."""
        events: List[Dict[str, Any]] = []
        track_ids = sorted(list(person_tracks.keys()))

        for i in range(len(track_ids)):
            for j in range(len(track_ids)):
                if i == j:
                    continue
                tidA, tidB = track_ids[i], track_ids[j]
                detsA = {d["frame_number"]: d for d in person_tracks[tidA]}
                detsB = {d["frame_number"]: d for d in person_tracks[tidB]}

                common_frames = sorted(list(set(detsA.keys()).intersection(set(detsB.keys()))))
                if len(common_frames) < 3:
                    continue

                following_count = 0
                t_start, t_end = 0.0, 0.0
                f_start = common_frames[0]

                for idx in range(len(common_frames) - 1):
                    f1, f2 = common_frames[idx], common_frames[idx + 1]
                    cA1, cA2 = _center(detsA[f1]["bbox"]), _center(detsA[f2]["bbox"])
                    cB1, cB2 = _center(detsB[f1]["bbox"]), _center(detsB[f2]["bbox"])

                    vA = (cA2[0] - cA1[0], cA2[1] - cA1[1])
                    vB = (cB2[0] - cB1[0], cB2[1] - cB1[1])

                    magA = math.hypot(vA[0], vA[1])
                    magB = math.hypot(vB[0], vB[1])

                    if magA > 5.0 and magB > 5.0:
                        dot = (vA[0] * vB[0] + vA[1] * vB[1]) / (magA * magB)
                        dist = math.hypot(cA1[0] - cB1[0], cA1[1] - cB1[1])
                        if dot > 0.70 and 30.0 < dist < 220.0:
                            if following_count == 0:
                                t_start = detsA[f1]["timestamp_seconds"]
                                f_start = f1
                            following_count += 1
                            t_end = detsA[f2]["timestamp_seconds"]

                if following_count >= 2:
                    events.append({
                        "event_type": "pattern_person_following",
                        "timestamp_seconds": t_start,
                        "end_timestamp_seconds": t_end,
                        "frame_number": f_start,
                        "media_id": media_id,
                        "tracking_id": tidA,
                        "secondary_tracking_id": tidB,
                        "confidence": 0.82,
                        "pattern_name": "person_following",
                        "description": f"Potential incident pattern: Track #{tidA} following trajectory of Track #{tidB} from timestamp {t_start:.1f}s to {t_end:.1f}s.",
                    })

        return events

    def _detect_rapid_movement_chase(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: rapid movement / chase-like sequence."""
        events: List[Dict[str, Any]] = []

        for tid, dets in person_tracks.items():
            if len(dets) < 2:
                continue

            sorted_dets = sorted(dets, key=lambda d: d.get("frame_number", 0))
            rapid_count = 0
            t_start, t_end = 0.0, 0.0
            f_start = sorted_dets[0].get("frame_number", 0)

            for idx in range(len(sorted_dets) - 1):
                d1, d2 = sorted_dets[idx], sorted_dets[idx + 1]
                dt = abs(d2.get("timestamp_seconds", 0.0) - d1.get("timestamp_seconds", 0.0))
                if dt <= 0.001:
                    dt = 0.5  # default frame interval fallback

                c1, c2 = _center(d1["bbox"]), _center(d2["bbox"])
                dist = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
                speed = dist / dt

                posture = d1.get("posture") or d2.get("posture")
                if speed > 120.0 or posture == "running":
                    if rapid_count == 0:
                        t_start = d1.get("timestamp_seconds", 0.0)
                        f_start = d1.get("frame_number", 0)
                    rapid_count += 1
                    t_end = d2.get("timestamp_seconds", 0.0)

            if rapid_count >= 2:
                events.append({
                    "event_type": "pattern_rapid_movement_chase",
                    "timestamp_seconds": t_start,
                    "end_timestamp_seconds": t_end,
                    "frame_number": f_start,
                    "media_id": media_id,
                    "tracking_id": tid,
                    "confidence": 0.84,
                    "pattern_name": "rapid_movement_chase",
                    "description": f"Potential incident pattern: Rapid movement / chase-like sequence observed for Track #{tid} from {t_start:.1f}s to {t_end:.1f}s.",
                })

        return events

    def _detect_multi_person_interaction(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: multiple-person physical interaction / close proximity."""
        events: List[Dict[str, Any]] = []
        track_ids = sorted(list(person_tracks.keys()))

        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                tidA, tidB = track_ids[i], track_ids[j]
                detsA = {d["frame_number"]: d for d in person_tracks[tidA]}
                detsB = {d["frame_number"]: d for d in person_tracks[tidB]}

                common_frames = sorted(list(set(detsA.keys()).intersection(set(detsB.keys()))))
                if len(common_frames) < 2:
                    continue

                contact_count = 0
                t_start, t_end = 0.0, 0.0
                f_start = common_frames[0]

                for f in common_frames:
                    dA, dB = detsA[f], detsB[f]
                    iou = _bbox_iou(dA["bbox"], dB["bbox"])
                    cA, cB = _center(dA["bbox"]), _center(dB["bbox"])
                    dist = math.hypot(cA[0] - cB[0], cA[1] - cB[1])

                    if iou > 0.12 or dist < 65.0:
                        if contact_count == 0:
                            t_start = dA["timestamp_seconds"]
                            f_start = f
                        contact_count += 1
                        t_end = dA["timestamp_seconds"]

                if contact_count >= 2:
                    events.append({
                        "event_type": "pattern_multi_person_interaction",
                        "timestamp_seconds": t_start,
                        "end_timestamp_seconds": t_end,
                        "frame_number": f_start,
                        "media_id": media_id,
                        "tracking_id": tidA,
                        "secondary_tracking_id": tidB,
                        "confidence": 0.86,
                        "pattern_name": "multi_person_interaction",
                        "description": f"Potential incident pattern: Sustained physical proximity/interaction between Track #{tidA} and Track #{tidB} from {t_start:.1f}s to {t_end:.1f}s.",
                    })

        return events

    def _detect_person_vehicle_interaction(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        vehicle_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: person -> object / vehicle interaction.

        Requires:
        - IoU >= 0.18 (distance alone does not trigger event)
        - Interaction persists for at least 3 consecutive frames
        - Meaningful spatial/posture interaction (dwelling/stopping or posture change)
        """
        events: List[Dict[str, Any]] = []
        if not person_tracks or not vehicle_tracks:
            return events

        for p_tid, p_dets in person_tracks.items():
            for v_tid, v_dets in vehicle_tracks.items():
                p_by_f = {d["frame_number"]: d for d in p_dets}
                v_by_f = {d["frame_number"]: d for d in v_dets}

                common = sorted(list(set(p_by_f.keys()).intersection(set(v_by_f.keys()))))
                if len(common) < 3:
                    continue

                consecutive_count = 0
                max_consecutive_count = 0
                has_meaningful_interaction = False

                t_start, t_end = 0.0, 0.0
                f_start = common[0]
                v_cls = v_dets[0].get("object_class", "vehicle").capitalize()

                for idx, f in enumerate(common):
                    p_det, v_det = p_by_f[f], v_by_f[f]
                    iou = _bbox_iou(p_det["bbox"], v_det["bbox"])

                    # Rule 1: Must satisfy IoU >= 0.18 (distance alone is NOT enough)
                    if iou >= 0.18:
                        if consecutive_count == 0:
                            t_start = p_det["timestamp_seconds"]
                            f_start = f
                        consecutive_count += 1
                        t_end = p_det["timestamp_seconds"]

                        if consecutive_count > max_consecutive_count:
                            max_consecutive_count = consecutive_count

                        # Rule 3: Check meaningful posture or spatial dwelling/stopping
                        posture = p_det.get("posture")
                        if posture in ("sitting", "lying_down", "falling"):
                            has_meaningful_interaction = True

                        # Check spatial dwelling (low speed or stationary position between consecutive frames)
                        if idx > 0:
                            prev_f = common[idx - 1]
                            prev_p_det = p_by_f[prev_f]
                            cP1, cP2 = _center(prev_p_det["bbox"]), _center(p_det["bbox"])
                            delta_pos = math.hypot(cP2[0] - cP1[0], cP2[1] - cP1[1])
                            if delta_pos < 30.0:  # Person is stopping/dwelling near vehicle
                                has_meaningful_interaction = True
                        else:
                            # Single frame or initial frame near vehicle
                            has_meaningful_interaction = True
                    else:
                        consecutive_count = 0

                # Rule 2: Must persist for at least 3 consecutive frames AND have meaningful spatial/posture interaction
                if max_consecutive_count >= 3 and has_meaningful_interaction:
                    events.append({
                        "event_type": "pattern_person_vehicle_interaction",
                        "timestamp_seconds": t_start,
                        "end_timestamp_seconds": t_end,
                        "frame_number": f_start,
                        "media_id": media_id,
                        "tracking_id": p_tid,
                        "secondary_tracking_id": v_tid,
                        "confidence": 0.85,
                        "pattern_name": "person_vehicle_interaction",
                        "description": f"Potential incident pattern: Track #{p_tid} interaction with vehicle ({v_cls} Track #{v_tid}) from {t_start:.1f}s to {t_end:.1f}s.",
                    })

        return events

    def _detect_entry_activity_exit(
        self,
        person_tracks: Dict[int, List[Dict[str, Any]]],
        media_id: int,
    ) -> List[Dict[str, Any]]:
        """Detect pattern: complete entry -> activity -> exit trajectory."""
        events: List[Dict[str, Any]] = []

        for tid, dets in person_tracks.items():
            if len(dets) < 3:
                continue

            sorted_dets = sorted(dets, key=lambda d: d.get("frame_number", 0))
            t_entry = sorted_dets[0].get("timestamp_seconds", 0.0)
            t_exit = sorted_dets[-1].get("timestamp_seconds", 0.0)
            f_entry = sorted_dets[0].get("frame_number", 0)

            postures = {d.get("posture") for d in sorted_dets if d.get("posture")}
            duration = t_exit - t_entry

            if duration >= 1.5 and len(postures) >= 2:
                events.append({
                    "event_type": "pattern_entry_activity_exit",
                    "timestamp_seconds": t_entry,
                    "end_timestamp_seconds": t_exit,
                    "frame_number": f_entry,
                    "media_id": media_id,
                    "tracking_id": tid,
                    "confidence": 0.80,
                    "pattern_name": "entry_activity_exit",
                    "description": f"Potential incident pattern: Complete entry -> activity -> exit trajectory for Track #{tid} from {t_entry:.1f}s to {t_exit:.1f}s.",
                })

        return events
