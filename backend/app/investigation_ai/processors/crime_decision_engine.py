"""Crime Decision Engine for Investigation AI.

Evaluates evidence from YOLO detections, Pose estimation posture events,
and TemporalAnalyzer sequence patterns to reach an investigative decision:
  - 'potential_crime'
  - 'non_crime'
  - 'uncertain'

Maintains strict investigative safeguards:
  - Does NOT issue single-frame crime verdicts.
  - Requires multi-event corroboration for 'potential_crime'.
  - Does NOT label normal walking, vehicle proximity, or isolated falls/lying down as crime.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("investigation.crime_decision_engine")

# Event Severity Weights for Evidence Scoring
EVENT_WEIGHTS: Dict[str, float] = {
    # High-severity suspicious/aggressive events
    "pattern_rapid_movement_chase": 0.35,
    "pattern_multi_person_interaction": 0.35,
    "pattern_fall_lying_down": 0.30,
    "posture_falling": 0.15,
    "posture_lying_down": 0.10,
    "possible_person_down": 0.05,
    # Ambiguous sequence events
    "pattern_person_following": 0.10,
    "pattern_approach_interaction_leave": 0.10,
    "pattern_person_vehicle_interaction": 0.0,  # Proximity alone is neutral
    # Benign / normal activity events
    "posture_standing": -0.15,
    "posture_walking": -0.15,
    "posture_sitting": -0.10,
    "posture_running": -0.05,  # Isolated running is neutral/slightly benign unless in chase
    "person_entered_frame": -0.05,
    "person_exited_frame": -0.05,
    "person_detected": -0.05,
    "vehicle_detected": -0.05,
    "pattern_entry_activity_exit": -0.15,
}

CRIME_DECISIONS = {"potential_crime", "non_crime", "uncertain"}


class CrimeDecisionEngine:
    """Decision Layer for classifying evidence into potential_crime, non_crime, or uncertain."""

    def __init__(self, crime_threshold: float = 0.55, non_crime_threshold: float = 0.20):
        self.crime_threshold = crime_threshold
        self.non_crime_threshold = non_crime_threshold

    def evaluate_decision(
        self,
        detections: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        temporal_events: Optional[List[Dict[str, Any]]] = None,
        is_video: bool = True,
        media_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Evaluate detections, pose events, and temporal sequence patterns to output a decision.

        Args:
            detections: List of detection dicts (YOLOv8 + ByteTrack + Pose).
            events: List of extracted pose/posture & frame events from EventExtractor.
            temporal_events: Optional list of temporal sequence events from TemporalAnalyzer.
            is_video: Boolean indicating video (True) or static image (False).
            media_id: Optional media ID for tracking provenance.

        Returns:
            Dict containing:
                - decision: 'potential_crime' | 'non_crime' | 'uncertain'
                - confidence: Float (0.0 to 1.0)
                - evidence_score: Float (-1.0 to 1.0)
                - track_ids: List of involved track IDs
                - timestamps: List of key evidence timestamps (seconds)
                - primary_triggers: List of event types driving the decision
                - safeguards_triggered: List of safeguard rules applied
                - evidence_breakdown: Breakdown of positive/negative weights
                - rationale: Human-readable explanation
        """
        all_events = list(events or [])
        if temporal_events:
            all_events.extend(temporal_events)

        # 1. Extract Track IDs and Timestamps
        track_ids, timestamps = self._extract_provenance(detections, all_events)

        # 2. Compute Raw Evidence Score & Breakdown
        raw_score, breakdown, primary_triggers = self._calculate_evidence_score(all_events, detections)

        # 3. Apply False-Positive Safeguard Rules
        safeguards_triggered: List[str] = []
        forced_decision: Optional[str] = None

        # Safeguard A: Person + vehicle overlap alone
        if self._check_person_vehicle_overlap_alone(detections, all_events):
            safeguards_triggered.append("PERSON_VEHICLE_OVERLAP_ONLY")
            forced_decision = "non_crime"

        elif self._check_normal_walking_only(detections, all_events):
            safeguards_triggered.append("NORMAL_ACTIVITY_ONLY")
            forced_decision = "non_crime"

        elif self._check_isolated_fall_or_lying_down(all_events, is_video):
            safeguards_triggered.append("ISOLATED_FALL_OR_LYING_DOWN")
            # Isolated fall/lying down without attack or chase -> non_crime or uncertain (never potential_crime)
            forced_decision = "uncertain" if is_video else "non_crime"

        elif self._check_ambiguous_interaction_only(all_events):
            safeguards_triggered.append("AMBIGUOUS_INTERACTION_NO_VIOLENCE")
            forced_decision = "uncertain"

        # Pre-calculate combination rules
        has_multi_person_interaction = any(
            e.get("event_type") == "pattern_multi_person_interaction" for e in all_events
        )
        has_chase = any(
            e.get("event_type") == "pattern_rapid_movement_chase" for e in all_events
        )
        has_fall = any(
            e.get("event_type") in ("pattern_fall_lying_down", "posture_falling", "posture_lying_down")
            for e in all_events
        )

        is_suspicious_combo = (
            (has_multi_person_interaction or has_chase) and has_fall
        ) or (has_multi_person_interaction and has_chase)

        # 4. Handle Image vs Video Specific Constraints
        if not is_video and forced_decision is None:
            # Single static image cannot confirm a crime without explicit violent indicators
            # Bypass if we have a highly suspicious physical combo (e.g. fight with fall)
            if not is_suspicious_combo and raw_score < 0.70:
                if raw_score < 0.20:
                    forced_decision = "non_crime"
                else:
                    safeguards_triggered.append("STATIC_IMAGE_INSUFFICIENT_EVIDENCE")
                    forced_decision = "uncertain"

        # 5. Multi-Event Combination Rules for potential_crime
        if forced_decision is None:

            # Lower threshold for static images since they can't accumulate temporal sequence scores
            threshold = 0.30 if not is_video else self.crime_threshold

            if is_suspicious_combo and raw_score >= threshold:
                final_decision = "potential_crime"
            elif raw_score < self.non_crime_threshold:
                final_decision = "non_crime"
            else:
                final_decision = "uncertain"
        else:
            final_decision = forced_decision

        # 6. Calculate Confidence
        confidence = self._compute_confidence(final_decision, raw_score, all_events, safeguards_triggered)

        # 7. Generate Rationale
        rationale = self._generate_rationale(
            final_decision, raw_score, primary_triggers, safeguards_triggered, is_video
        )

        return {
            "decision": final_decision,
            "confidence": round(confidence, 2),
            "evidence_score": round(raw_score, 2),
            "is_video": is_video,
            "media_id": media_id,
            "track_ids": sorted(list(track_ids)),
            "timestamps": sorted(list(timestamps)),
            "primary_triggers": primary_triggers,
            "safeguards_triggered": safeguards_triggered,
            "evidence_breakdown": breakdown,
            "rationale": rationale,
        }

    def _extract_provenance(
        self, detections: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> Tuple[Set[int], Set[float]]:
        """Extract set of involved track IDs and timestamps."""
        tids: Set[int] = set()
        timestamps: Set[float] = set()

        for d in detections:
            tid = d.get("tracking_id")
            if tid is not None:
                tids.add(tid)
            ts = d.get("timestamp_seconds")
            if ts is not None:
                timestamps.add(round(float(ts), 1))

        for e in events:
            tid = e.get("tracking_id")
            if tid is not None:
                tids.add(tid)
            ts = e.get("timestamp_seconds")
            if ts is not None:
                timestamps.add(round(float(ts), 1))

        return tids, timestamps

    def _calculate_evidence_score(
        self, events: List[Dict[str, Any]], detections: List[Dict[str, Any]]
    ) -> Tuple[float, Dict[str, List[str]], List[str]]:
        """Compute accumulated evidence score and breakdown."""
        score = 0.0
        pos_signals: List[str] = []
        neg_signals: List[str] = []
        primary_triggers: List[str] = []

        for ev in events:
            ev_type = ev.get("event_type", "")
            if not ev_type:
                continue

            w = EVENT_WEIGHTS.get(ev_type, 0.0)
            score += w

            if w > 0:
                pos_signals.append(f"{ev_type} (+{w:.2f})")
                if ev_type not in primary_triggers:
                    primary_triggers.append(ev_type)
            elif w < 0:
                neg_signals.append(f"{ev_type} ({w:.2f})")

        # Normalize score between 0.0 and 1.0
        norm_score = max(0.0, min(1.0, score))
        breakdown = {
            "positive_signals": pos_signals,
            "negative_signals": neg_signals,
        }
        return norm_score, breakdown, primary_triggers

    def _check_normal_walking_only(
        self, detections: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> bool:
        """Check if media contains only normal walking/standing activity."""
        if not events:
            return True
        suspicious_types = {
            "pattern_rapid_movement_chase",
            "pattern_multi_person_interaction",
            "pattern_fall_lying_down",
            "posture_falling",
            "posture_lying_down",
            "possible_person_down",
            "pattern_person_following",
        }
        for e in events:
            if e.get("event_type") in suspicious_types:
                return False
        return True

    def _check_person_vehicle_overlap_alone(
        self, detections: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> bool:
        """Check if only person-vehicle proximity/overlap is present without violence."""
        event_types = {e.get("event_type") for e in events if e.get("event_type")}
        violent_types = {
            "pattern_rapid_movement_chase",
            "pattern_multi_person_interaction",
            "pattern_fall_lying_down",
            "posture_falling",
            "posture_lying_down",
        }
        if event_types.intersection(violent_types):
            return False
        # Has person_vehicle_interaction or vehicle_detected but no violent patterns
        if "pattern_person_vehicle_interaction" in event_types or "vehicle_detected" in event_types:
            return True
        return False

    def _check_isolated_fall_or_lying_down(
        self, events: List[Dict[str, Any]], is_video: bool
    ) -> bool:
        """Check if fall or lying down occurs in isolation without assault or chase."""
        event_types = {e.get("event_type") for e in events if e.get("event_type")}
        has_fall = bool(
            event_types.intersection({
                "pattern_fall_lying_down", "posture_falling", "posture_lying_down", "possible_person_down"
            })
        )
        if not has_fall:
            return False

        has_conflict_or_chase = bool(
            event_types.intersection({
                "pattern_multi_person_interaction", "pattern_rapid_movement_chase"
            })
        )
        return not has_conflict_or_chase

    def _check_ambiguous_interaction_only(self, events: List[Dict[str, Any]]) -> bool:
        """Check if only ambiguous interaction/following occurs without violence or fall."""
        event_types = {e.get("event_type") for e in events if e.get("event_type")}
        has_ambiguous = bool(
            event_types.intersection({
                "pattern_approach_interaction_leave", "pattern_person_following"
            })
        )
        if not has_ambiguous:
            return False

        has_violent_or_fall = bool(
            event_types.intersection({
                "pattern_multi_person_interaction",
                "pattern_rapid_movement_chase",
                "pattern_fall_lying_down",
                "posture_falling",
                "posture_lying_down",
            })
        )
        return not has_violent_or_fall

    def _compute_confidence(
        self,
        decision: str,
        evidence_score: float,
        events: List[Dict[str, Any]],
        safeguards: List[str],
    ) -> float:
        """Compute decision confidence level (0.50 to 0.95)."""
        if decision == "potential_crime":
            return min(0.95, 0.65 + evidence_score * 0.30)
        elif decision == "non_crime":
            if "NORMAL_ACTIVITY_ONLY" in safeguards or "PERSON_VEHICLE_OVERLAP_ONLY" in safeguards:
                return 0.90
            return min(0.90, 0.70 + (1.0 - evidence_score) * 0.20)
        else:  # uncertain
            return 0.50 + abs(0.50 - evidence_score) * 0.30

    def _generate_rationale(
        self,
        decision: str,
        score: float,
        triggers: List[str],
        safeguards: List[str],
        is_video: bool,
    ) -> str:
        """Generate clear forensic explanation for decision."""
        if decision == "potential_crime":
            trig_str = ", ".join(triggers) if triggers else "multiple physical indicators"
            return (
                f"POTENTIAL INCIDENT DETECTED (Score: {score:.2f}): "
                f"Sequence analysis identified structured high-severity indicators ({trig_str}). "
                f"Requires law enforcement verification."
            )
        elif decision == "non_crime":
            if "PERSON_VEHICLE_OVERLAP_ONLY" in safeguards:
                return "NON-CRIME / NORMAL: Pedestrian activity near vehicle without suspicious or physical interaction."
            if "NORMAL_ACTIVITY_ONLY" in safeguards:
                return "NON-CRIME / NORMAL: Routine movement observed with no posture anomalies or conflict patterns."
            return f"NON-CRIME: Evidence score ({score:.2f}) indicates routine surveillance scene without incident indicators."
        else:  # uncertain
            if "ISOLATED_FALL_OR_LYING_DOWN" in safeguards:
                return "UNCERTAIN / MEDICAL ANOMALY: Horizontal/fall posture detected in isolation without physical assault or pursuit."
            if "AMBIGUOUS_INTERACTION_NO_VIOLENCE" in safeguards:
                return "UNCERTAIN: Person proximity/interaction sequence observed without physical conflict or chase."
            if not is_video:
                return "UNCERTAIN: Single frame provides insufficient evidence for definitive action decision."
            return f"UNCERTAIN (Score: {score:.2f}): Evidence is ambiguous and requires officer review."
