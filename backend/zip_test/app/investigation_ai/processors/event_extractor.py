"""Investigation Event Extraction Engine.

Converts raw detections and tracking trajectories into structured, timestamped investigation events.
Maintains strict investigative neutrality without making criminal identity or guilt assertions.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("investigation.event_extractor")

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}


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

        seen_tracks = set()
        person_tracks: Dict[int, List[Dict[str, Any]]] = {}
        vehicle_tracks: Dict[int, List[Dict[str, Any]]] = {}
        first_person_seen = False
        first_vehicle_seen = False

        for det in sorted_dets:
            obj_cls = (det.get("object_class") or "").lower()
            track_id = det.get("tracking_id")
            frame_num = det.get("frame_number", 0)
            timestamp = det.get("timestamp_seconds", 0.0)
            conf = det.get("confidence", 0.0)
            bbox = det.get("bbox", {})

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

                # 5. Possible Person Down / Fall Event (Aspect Ratio Heuristic)
                # Bounding box width significantly larger than height (W >= 1.25 * H)
                if bbox and isinstance(bbox, dict):
                    xmin = bbox.get("xmin", 0)
                    ymin = bbox.get("ymin", 0)
                    xmax = bbox.get("xmax", 0)
                    ymax = bbox.get("ymax", 0)
                    w = abs(xmax - xmin)
                    h = abs(ymax - ymin)
                    if h > 0 and (w / h) >= 1.25 and conf >= 0.35:
                        events.append({
                            "event_type": "possible_person_down",
                            "timestamp_seconds": timestamp,
                            "frame_number": frame_num,
                            "media_id": media_id,
                            "tracking_id": track_id,
                            "confidence": conf,
                            "description": f"Possible person-down / horizontal posture detected (Track #{track_id if track_id else 'N/A'}) at timestamp {timestamp:.1f}s (Frame #{frame_num}).",
                        })

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

                # If the video ended or track ceased before final frame
                events.append({
                    "event_type": "person_exited_frame",
                    "timestamp_seconds": last_timestamp,
                    "frame_number": last_frame,
                    "media_id": media_id,
                    "tracking_id": tid,
                    "confidence": last_conf,
                    "description": f"Person (Track #{tid}) last observed / exited frame view at timestamp {last_timestamp:.1f}s (Frame #{last_frame}).",
                })

        # Sort all generated events chronologically
        events.sort(key=lambda e: (e["timestamp_seconds"], e["frame_number"]))
        logger.info(f"Extracted {len(events)} investigation events for media ID {media_id}.")
        return events
