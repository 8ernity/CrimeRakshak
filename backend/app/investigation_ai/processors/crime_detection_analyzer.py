"""Crime Detection Analyzer Engine for AI Investigation Support.

Acts as a dedicated decision layer on top of existing OpenCV + YOLOv8 + ByteTrack
detections and extracted visual events. Evaluates configured crime indicator rules
to output structured classification:
  - "possible_crime"
  - "no_clear_crime_evidence"

IMPORTANT DESIGN PRINCIPLES:
  - Reuses existing detections, tracking IDs, and extracted events.
  - Never uses "confirmed crime" label.
  - Classification logic is separate and configurable.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("investigation.crime_detection_analyzer")

# Configurable Crime Indicator Categories & Class Keywords
WEAPON_CLASSES: Set[str] = {
    "weapon",
    "knife",
    "gun",
    "pistol",
    "rifle",
    "firearm",
    "blade",
    "sword",
    "baseball bat",
    "bat",
    "stick",
    "hammer",
    "axe",
    "crowbar",
}

PERSON_DOWN_EVENT_TYPES: Set[str] = {
    "possible_person_down",
    "posture_falling",
    "posture_lying_down",
    "pattern_fall_lying_down",
    "person_down",
}

AGGRESSIVE_INTERACTION_TYPES: Set[str] = {
    "pattern_multi_person_interaction",
    "physical_conflict",
    "assault_posture",
    "struggle_detected",
    "brawl_detected",
}

SUSPICIOUS_MOVEMENT_TYPES: Set[str] = {
    "pattern_rapid_movement_chase",
    "pattern_person_following",
    "rapid_fleeing",
    "loitering_near_restricted_vehicle",
    "running_chase",
}


class CrimeDetectionAnalyzer:
    """Configurable Crime Video Detection decision layer."""

    def __init__(
        self,
        possible_crime_threshold: float = 0.50,
        weapon_conf_threshold: float = 0.35,
    ):
        self.possible_crime_threshold = possible_crime_threshold
        self.weapon_conf_threshold = weapon_conf_threshold

    def analyze_video_evidence(
        self,
        detections: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        is_video: bool = True,
        media_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Analyze complete video detections & events to produce final classification.

        Args:
            detections: List of detection dicts (YOLOv8 + ByteTrack).
            events: List of event dicts (posture, temporal, spatial).
            is_video: Whether the media item is a video.
            media_id: Optional media identifier.

        Returns:
            Dict containing:
                - classification: "possible_crime" | "no_clear_crime_evidence"
                - confidence: float (0.0 to 1.0)
                - crime_indicators: List[str]
                - relevant_timestamps: List[Dict[str, float]] (start/end ranges)
                - evidence_events: List[Dict[str, Any]]
        """
        all_events = list(events or [])

        # 1. Evaluate configured crime indicator rules
        indicators: Set[str] = set()
        matched_events: List[Dict[str, Any]] = []
        raw_intervals: List[Tuple[float, float]] = []

        # Indicator Rule 1: Weapon Detection
        has_weapon, weapon_evts, weapon_intervals = self._check_weapon_indicator(detections, all_events)
        if has_weapon:
            indicators.add("weapon_detected")
            matched_events.extend(weapon_evts)
            raw_intervals.extend(weapon_intervals)

        # Indicator Rule 2: Person Down / Fall Detection
        has_person_down, down_evts, down_intervals = self._check_person_down_indicator(all_events, detections)
        if has_person_down:
            indicators.add("possible_person_down")
            matched_events.extend(down_evts)
            raw_intervals.extend(down_intervals)

        # Indicator Rule 3: Aggressive Physical Interaction
        has_aggression, agg_evts, agg_intervals = self._check_aggression_indicator(all_events)
        if has_aggression:
            indicators.add("aggressive_physical_interaction")
            matched_events.extend(agg_evts)
            raw_intervals.extend(agg_intervals)

        # Indicator Rule 4: Suspicious Movement / Chase / Following
        has_suspicious, susp_evts, susp_intervals = self._check_suspicious_movement_indicator(all_events)
        if has_suspicious:
            indicators.add("suspicious_movement")
            matched_events.extend(susp_evts)
            raw_intervals.extend(susp_intervals)

        # Indicator Rule 5: Multiple Correlated Events
        if len(indicators) >= 2:
            indicators.add("multiple_correlated_events")

        # 2. Final Classification Decision & Confidence Calculation
        crime_indicators_list = sorted(list(indicators))

        if len(crime_indicators_list) > 0:
            classification = "possible_crime"
            confidence = self._compute_possible_crime_confidence(crime_indicators_list, matched_events)
        else:
            classification = "no_clear_crime_evidence"
            confidence = self._compute_normal_video_confidence(detections, all_events)

        # 3. Consolidate and Merge Relevant Timestamps into continuous windows
        merged_timestamps = self._merge_timestamp_intervals(raw_intervals)

        # Deduplicate evidence_events
        deduped_evidence_events = self._deduplicate_events(matched_events)

        return {
          "classification": classification,
          "confidence": round(confidence, 2),
          "crime_indicators": crime_indicators_list,
          "relevant_timestamps": merged_timestamps,
          "evidence_events": deduped_evidence_events,
        }

    def _check_weapon_indicator(
        self, detections: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Tuple[float, float]]]:
        """Check for weapon-related detections or events."""
        matched: List[Dict[str, Any]] = []
        intervals: List[Tuple[float, float]] = []

        # Check YOLO object detections for weapon classes
        for d in detections:
            obj_cls = str(d.get("object_class", "")).lower()
            conf = float(d.get("confidence", 0.0))
            if any(w in obj_cls for w in WEAPON_CLASSES) and conf >= self.weapon_conf_threshold:
                ts = float(d.get("timestamp_seconds", 0.0))
                matched.append({
                    "event_type": "weapon_detected",
                    "description": f"Detected weapon ({obj_cls}) with confidence {conf:.2f}",
                    "timestamp_seconds": ts,
                    "tracking_id": d.get("tracking_id"),
                    "confidence": conf,
                })
                intervals.append((max(0.0, ts - 1.5), ts + 1.5))

        # Check visual events for weapon references
        for e in events:
            ev_type = str(e.get("event_type", "")).lower()
            desc = str(e.get("description", "")).lower()
            if any(w in ev_type or w in desc for w in WEAPON_CLASSES):
                ts_start = float(e.get("start_timestamp_seconds", e.get("timestamp_seconds", 0.0)))
                ts_end = float(e.get("end_timestamp_seconds", ts_start + 2.0))
                matched.append({
                    "event_type": e.get("event_type", "weapon_detected"),
                    "description": e.get("description", "Weapon-related visual event"),
                    "timestamp_seconds": ts_start,
                    "tracking_id": e.get("tracking_id"),
                    "confidence": float(e.get("confidence", 0.85)),
                })
                intervals.append((ts_start, ts_end))

        return (len(matched) > 0), matched, intervals

    def _check_person_down_indicator(
        self, events: List[Dict[str, Any]], detections: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Tuple[float, float]]]:
        """Check for person-down or fall events."""
        matched: List[Dict[str, Any]] = []
        intervals: List[Tuple[float, float]] = []

        for e in events:
            ev_type = str(e.get("event_type", "")).lower()
            if ev_type in PERSON_DOWN_EVENT_TYPES or "fall" in ev_type or "lying" in ev_type:
                ts_start = float(e.get("start_timestamp_seconds", e.get("timestamp_seconds", 0.0)))
                ts_end = float(e.get("end_timestamp_seconds", ts_start + 3.0))
                matched.append({
                    "event_type": "possible_person_down",
                    "description": e.get("description", "Person fall or lying down posture detected"),
                    "timestamp_seconds": ts_start,
                    "tracking_id": e.get("tracking_id"),
                    "confidence": float(e.get("confidence", 0.80)),
                })
                intervals.append((ts_start, ts_end))

        # Check posture in detections if not present in events
        if not matched:
            for d in detections:
                posture = str(d.get("posture", "")).lower()
                if posture in ("falling", "lying_down", "person_down"):
                    ts = float(d.get("timestamp_seconds", 0.0))
                    matched.append({
                        "event_type": "possible_person_down",
                        "description": f"Person posture detected as {posture}",
                        "timestamp_seconds": ts,
                        "tracking_id": d.get("tracking_id"),
                        "confidence": float(d.get("confidence", 0.75)),
                    })
                    intervals.append((max(0.0, ts - 1.0), ts + 2.5))

        return (len(matched) > 0), matched, intervals

    def _check_aggression_indicator(
        self, events: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Tuple[float, float]]]:
        """Check for physical altercation / multi-person aggressive interactions."""
        matched: List[Dict[str, Any]] = []
        intervals: List[Tuple[float, float]] = []

        for e in events:
            ev_type = str(e.get("event_type", "")).lower()
            if ev_type in AGGRESSIVE_INTERACTION_TYPES or "struggle" in ev_type or "brawl" in ev_type:
                ts_start = float(e.get("start_timestamp_seconds", e.get("timestamp_seconds", 0.0)))
                ts_end = float(e.get("end_timestamp_seconds", ts_start + 4.0))
                matched.append({
                    "event_type": "aggressive_physical_interaction",
                    "description": e.get("description", "Aggressive physical interaction between subjects"),
                    "timestamp_seconds": ts_start,
                    "tracking_id": e.get("tracking_id"),
                    "confidence": float(e.get("confidence", 0.82)),
                })
                intervals.append((ts_start, ts_end))

        return (len(matched) > 0), matched, intervals

    def _check_suspicious_movement_indicator(
        self, events: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Tuple[float, float]]]:
        """Check for suspicious movement, chase, or stalker following events."""
        matched: List[Dict[str, Any]] = []
        intervals: List[Tuple[float, float]] = []

        for e in events:
            ev_type = str(e.get("event_type", "")).lower()
            if ev_type in SUSPICIOUS_MOVEMENT_TYPES or "chase" in ev_type or "following" in ev_type:
                ts_start = float(e.get("start_timestamp_seconds", e.get("timestamp_seconds", 0.0)))
                ts_end = float(e.get("end_timestamp_seconds", ts_start + 4.0))
                matched.append({
                    "event_type": "suspicious_movement",
                    "description": e.get("description", "Suspicious movement or rapid pursuit pattern"),
                    "timestamp_seconds": ts_start,
                    "tracking_id": e.get("tracking_id"),
                    "confidence": float(e.get("confidence", 0.78)),
                })
                intervals.append((ts_start, ts_end))

        return (len(matched) > 0), matched, intervals

    def _compute_possible_crime_confidence(
        self, indicators: List[str], evidence_events: List[Dict[str, Any]]
    ) -> float:
        """Compute confidence for possible_crime classification (0.75 to 0.98)."""
        base_conf = 0.82
        if "weapon_detected" in indicators:
            base_conf += 0.08
        if "multiple_correlated_events" in indicators:
            base_conf += 0.06
        if len(evidence_events) >= 3:
            base_conf += 0.04
        return min(0.98, max(0.75, base_conf))

    def _compute_normal_video_confidence(
        self, detections: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> float:
        """Compute confidence for no_clear_crime_evidence classification (0.85 to 0.95)."""
        if not events and not detections:
            return 0.85
        return 0.90

    def _merge_timestamp_intervals(
        self, intervals: List[Tuple[float, float]]
    ) -> List[Dict[str, float]]:
        """Merge overlapping or adjacent timestamp intervals into formatted ranges."""
        if not intervals:
            return []

        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged: List[Tuple[float, float]] = []

        current_start, current_end = sorted_intervals[0]

        for next_start, next_end in sorted_intervals[1:]:
            if next_start <= current_end + 2.0:  # Allow 2-second gap for continuity
                current_end = max(current_end, next_end)
            else:
                merged.append((round(current_start, 1), round(current_end, 1)))
                current_start, current_end = next_start, next_end

        merged.append((round(current_start, 1), round(current_end, 1)))

        return [{"start": m[0], "end": m[1]} for m in merged]

    def _deduplicate_events(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate matched evidence event list."""
        seen: Set[str] = set()
        unique: List[Dict[str, Any]] = []

        for e in events:
            key = f"{e.get('event_type')}_{round(float(e.get('timestamp_seconds', 0.0)), 1)}_{e.get('tracking_id')}"
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique
