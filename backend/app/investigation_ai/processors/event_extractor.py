"""Investigation Event Extraction Engine.

Converts raw detections and tracking trajectories into structured, timestamped investigation events.
Maintains strict investigative neutrality without making criminal identity or guilt assertions.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("investigation.event_extractor")

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}


from app.investigation_ai.processors.pose_estimator import estimate_posture_from_keypoints


class EventExtractor:
    """Extractor for investigative events from detection and tracking metadata."""

    def extract_events(
        self,
        detections: List[Dict[str, Any]],
        media_id: int,
        total_frames: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Extract structured events from a list of detections/tracks for a media item."""
        events: List[Dict[str, Any]] = []
        if not detections:
            return events

        # Sort detections by frame_number / timestamp
        sorted_dets = sorted(detections, key=lambda d: (d.get("frame_number", 0), d.get("timestamp_seconds", 0.0)))

        person_tracks: Dict[int, List[Dict[str, Any]]] = {}
        vehicle_tracks: Dict[int, List[Dict[str, Any]]] = {}
        track_posture_state: Dict[int, str] = {}
        first_person_seen = False
        first_vehicle_seen = False

        for det in sorted_dets:
            obj_cls = (det.get("object_class") or "").lower()
            track_id = det.get("tracking_id")
            frame_num = det.get("frame_number", 0)
            timestamp = det.get("timestamp_seconds", 0.0)
            conf = det.get("confidence", 0.0)
            bbox = det.get("bbox", {})
            keypoints = det.get("keypoints", [])

            # 1. Person Detected Event (First detection overall or new track)
            if obj_cls == "person":
                if not first_person_seen:
                    first_person_seen = True
                    events.append({
                        "event_type": "person_detected",
                        "timestamp_seconds": timestamp,
                        "frame_number": frame_num,
                        "media_id": media_id,
                        "tracking_id": track_id,
                        "confidence": conf,
                        "description": f"Person detected in evidence media (Track #{track_id if track_id else 'N/A'}) at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                    })

                if track_id is not None:
                    if track_id not in person_tracks:
                        person_tracks[track_id] = []
                        # 3. Person Entered Frame Event
                        events.append({
                            "event_type": "person_entered_frame",
                            "timestamp_seconds": timestamp,
                            "frame_number": frame_num,
                            "media_id": media_id,
                            "tracking_id": track_id,
                            "confidence": conf,
                            "description": f"Person (Track #{track_id}) entered frame view at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                        })
                    person_tracks[track_id].append(det)

                # 5. Pose Estimation & Posture State Analysis
                posture = det.get("posture")
                if not posture:
                    posture, _ = estimate_posture_from_keypoints(keypoints, bbox=bbox)

                tid_label = f"Track #{track_id}" if track_id is not None else "N/A"

                # Check if posture changed or if it's a critical posture (lying_down / falling)
                prev_posture = track_posture_state.get(track_id) if track_id is not None else None

                if posture in ("lying_down", "falling"):
                    # Emit pose event
                    event_type_name = f"posture_{posture}"
                    events.append({
                        "event_type": event_type_name,
                        "timestamp_seconds": timestamp,
                        "frame_number": frame_num,
                        "media_id": media_id,
                        "tracking_id": track_id,
                        "confidence": conf,
                        "posture": posture,
                        "description": f"Person ({tid_label}) observed in {posture} posture at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                    })

                    # Maintain backward compatibility for possible_person_down heuristic listener
                    events.append({
                        "event_type": "possible_person_down",
                        "timestamp_seconds": timestamp,
                        "frame_number": frame_num,
                        "media_id": media_id,
                        "tracking_id": track_id,
                        "confidence": conf,
                        "posture": posture,
                        "description": f"Possible person-down / horizontal posture detected ({tid_label}) at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                    })

                elif posture in ("sitting", "running") and prev_posture != posture:
                    events.append({
                        "event_type": f"posture_{posture}",
                        "timestamp_seconds": timestamp,
                        "frame_number": frame_num,
                        "media_id": media_id,
                        "tracking_id": track_id,
                        "confidence": conf,
                        "posture": posture,
                        "description": f"Person ({tid_label}) posture transition to '{posture}' at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                    })

                if track_id is not None:
                    track_posture_state[track_id] = posture

            # 2. Vehicle Detected Event
            elif obj_cls in VEHICLE_CLASSES:
                if not first_vehicle_seen:
                    first_vehicle_seen = True
                    events.append({
                        "event_type": "vehicle_detected",
                        "timestamp_seconds": timestamp,
                        "frame_number": frame_num,
                        "media_id": media_id,
                        "tracking_id": track_id,
                        "confidence": conf,
                        "description": f"Vehicle ({obj_cls.capitalize()}) detected in evidence media at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                    })

                if track_id is not None and track_id not in vehicle_tracks:
                    vehicle_tracks[track_id] = [det]

        # 4. Person Exited Frame Events
        for tid, track_dets in person_tracks.items():
            if len(track_dets) > 0:
                last_det = track_dets[-1]
                last_frame = last_det.get("frame_number", 0)
                last_timestamp = last_det.get("timestamp_seconds", 0.0)
                last_conf = last_det.get("confidence", 0.0)

                events.append({
                    "event_type": "person_exited_frame",
                    "timestamp_seconds": last_timestamp,
                    "frame_number": last_frame,
                    "media_id": media_id,
                    "tracking_id": tid,
                    "confidence": last_conf,
                    "description": f"Person (Track #{tid}) last observed / exited frame view at timestamp {last_timestamp:.1f}s (Frame #{last_frame}).",
                })

        # 5. Single-Frame Multi-Person Interaction (For Static Images)
        # If there are multiple people in the same frame with high IoU, flag as interaction
        from app.investigation_ai.processors.temporal_analyzer import _bbox_iou
        for i in range(len(sorted_dets)):
            for j in range(i + 1, len(sorted_dets)):
                dA = sorted_dets[i]
                dB = sorted_dets[j]
                if dA.get("object_class") == "person" and dB.get("object_class") == "person" and dA.get("frame_number") == dB.get("frame_number"):
                    if _bbox_iou(dA.get("bbox", {}), dB.get("bbox", {})) > 0.15:
                        events.append({
                            "event_type": "pattern_multi_person_interaction",
                            "timestamp_seconds": dA.get("timestamp_seconds", 0.0),
                            "frame_number": dA.get("frame_number", 0),
                            "media_id": media_id,
                            "confidence": 0.86,
                            "pattern_name": "multi_person_interaction",
                            "description": "Physical proximity/interaction detected in static frame."
                        })
                        break
            else:
                continue
            break

        # 6. Multi-Frame Temporal Pattern Analysis
        try:
            from app.investigation_ai.processors.temporal_analyzer import TemporalAnalyzer
            t_analyzer = TemporalAnalyzer()
            pattern_events = t_analyzer.analyze_temporal_patterns(sorted_dets, media_id=media_id)
            events.extend(pattern_events)
        except Exception as e:
            logger.warning(f"Error extracting temporal patterns for media ID {media_id}: {e}")

        # Sort all generated events chronologically
        events.sort(key=lambda e: (e.get("timestamp_seconds", 0.0), e.get("frame_number", 0)))
        logger.info(f"Extracted {len(events)} investigation events for media ID {media_id}.")
        return events

