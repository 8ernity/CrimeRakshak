"""AI Investigation Report Generator.

Multimodal report pipeline that consumes existing pipeline outputs
(detections, tracks, events, crime detection results) and optional
key video frames, then invokes the project's existing Gemini LLM
(via app.chat.llm.chat_completion) to produce a structured 12-section
forensic investigation report.

IMPORTANT:
  - Reuses the EXISTING LLM client — does NOT create a second one.
  - Does NOT modify YOLO, ByteTrack, event extraction, or crime detection.
  - Gracefully falls back to a deterministic report when LLM is unavailable.
  - Never states a person is a criminal or that a crime is legally confirmed.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings

logger = logging.getLogger("investigation.report_generator")

# ─── Maximum key frames to supply to the vision model ───────────────
MAX_KEY_FRAMES = 6
FRAME_JPEG_QUALITY = 80
FRAME_MAX_WIDTH = 768
# Minimum gap (seconds) between extracted key frames to avoid duplicates
MIN_FRAME_GAP_SECONDS = 1.0


# ═════════════════════════════════════════════════════════════════════
#  1.  KEY FRAME EXTRACTOR
# ═════════════════════════════════════════════════════════════════════

class KeyFrameExtractor:
    """Extract key frames from a video at specific timestamps, or read
    the original image file, returning base64-encoded JPEG data."""

    @staticmethod
    def extract_video_frames(
        video_path: str,
        timestamps: List[float],
        max_frames: int = MAX_KEY_FRAMES,
    ) -> List[Dict[str, Any]]:
        """Extract frames at given timestamps from a video file.

        Returns list of dicts:
          {"index": int, "timestamp_seconds": float, "base64_jpeg": str, "width": int, "height": int}
        """
        try:
            import cv2
        except ImportError:
            logger.warning("OpenCV not available — skipping video frame extraction.")
            return []

        if not os.path.exists(video_path):
            logger.warning(f"Video file not found for frame extraction: {video_path}")
            return []

        # Deduplicate and sort timestamps, enforce minimum gap
        sorted_ts = sorted(set(timestamps))
        filtered_ts: List[float] = []
        for ts in sorted_ts:
            if not filtered_ts or (ts - filtered_ts[-1]) >= MIN_FRAME_GAP_SECONDS:
                filtered_ts.append(ts)
        filtered_ts = filtered_ts[:max_frames]

        if not filtered_ts:
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Cannot open video for frame extraction: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frames: List[Dict[str, Any]] = []

        try:
            for idx, ts in enumerate(filtered_ts):
                frame_num = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    continue

                b64, w, h = KeyFrameExtractor._encode_frame(frame)
                frames.append({
                    "index": idx,
                    "timestamp_seconds": round(ts, 1),
                    "base64_jpeg": b64,
                    "width": w,
                    "height": h,
                })
        finally:
            cap.release()

        logger.info(f"Extracted {len(frames)} key frames from video at timestamps {[f['timestamp_seconds'] for f in frames]}")
        return frames

    @staticmethod
    def extract_image_frame(image_path: str) -> List[Dict[str, Any]]:
        """Read a single image file and return it as a base64-encoded frame."""
        try:
            import cv2
        except ImportError:
            logger.warning("OpenCV not available — skipping image frame extraction.")
            return []

        if not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}")
            return []

        frame = cv2.imread(image_path)
        if frame is None:
            logger.warning(f"Cannot read image file: {image_path}")
            return []

        b64, w, h = KeyFrameExtractor._encode_frame(frame)
        return [{
            "index": 0,
            "timestamp_seconds": 0.0,
            "base64_jpeg": b64,
            "width": w,
            "height": h,
        }]

    @staticmethod
    def _encode_frame(frame) -> Tuple[str, int, int]:
        """Resize frame to max width and encode as base64 JPEG."""
        import cv2
        h, w = frame.shape[:2]
        if w > FRAME_MAX_WIDTH:
            scale = FRAME_MAX_WIDTH / w
            new_w = FRAME_MAX_WIDTH
            new_h = int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            w, h = new_w, new_h

        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, FRAME_JPEG_QUALITY])
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        return b64, w, h


# ═════════════════════════════════════════════════════════════════════
#  2.  REPORT PROMPT BUILDER
# ═════════════════════════════════════════════════════════════════════

REPORT_SYSTEM_PROMPT = """You are CrimeRakshak AI Forensic Investigation Report Generator for Karnataka State Police.

Your task: Produce a comprehensive, structured, forensic-grade AI Investigation Report based STRICTLY on the provided evidence data and visual frames.

YOU MUST RESPOND ONLY WITH A VALID JSON OBJECT matching the schema below. No markdown, no commentary.

JSON SCHEMA:
{
  "incident_classification": "string — one of: 'Possible Violent Crime', 'Possible Property Crime', 'Possible Weapon Offense', 'Suspicious Activity', 'Traffic/Vehicle Incident', 'Person in Distress', 'No Criminal Activity Observed', 'Insufficient Evidence for Classification'",
  "confidence": 0.0 to 1.0,
  "executive_summary": "string — 3-5 sentence objective forensic summary of what was observed",
  "observed_evidence": [
    {
      "observation": "string — what was observed",
      "source": "directly_observed | ai_inference | uncertain",
      "confidence": 0.0 to 1.0,
      "timestamp_seconds": null or float,
      "tracking_id": null or int
    }
  ],
  "detected_objects": ["string — list of all distinct object classes detected"],
  "detected_persons_vehicles": [
    {
      "entity_type": "person | vehicle | weapon | object",
      "description": "string — description of the entity",
      "tracking_id": null or int,
      "first_seen_seconds": null or float,
      "last_seen_seconds": null or float,
      "confidence": 0.0 to 1.0
    }
  ],
  "chronological_timeline": [
    {
      "timestamp_seconds": float,
      "description": "string — what happened at this time",
      "source": "directly_observed | ai_inference | uncertain",
      "significance": "critical | notable | routine"
    }
  ],
  "relevant_timestamps": [
    {"start": float, "end": float}
  ],
  "evidence_frame_references": [
    {
      "frame_index": int,
      "timestamp_seconds": float,
      "description": "string — what is visible in this frame",
      "relevant_observations": ["string"]
    }
  ],
  "crime_indicators": ["string — e.g. 'weapon_detected', 'possible_person_down'"],
  "uncertainty_notes": ["string — things that could NOT be determined with confidence"],
  "limitations": ["string — technical and procedural limitations of this analysis"]
}

CRITICAL LEGAL AND SAFETY GUARDRAILS:
1. NEVER identify any individual as a criminal, suspect, perpetrator, or guilty party.
2. Use neutral forensic language: "Individual corresponding to Track #X" not "The attacker".
3. CLEARLY DISTINGUISH between:
   - "directly_observed": Fact seen in frames/detections (e.g. "knife detected with 88% confidence")
   - "ai_inference": Reasonable conclusion from evidence (e.g. "interaction pattern suggests physical altercation")
   - "uncertain": Observation that could not be confirmed (e.g. "possible weapon-like object, low confidence")
4. Never state that a crime has been legally confirmed.
5. Frame all findings as "possible", "potential", or "observed indicators" requiring human verification.
6. Include at least 2 uncertainty notes and 2 limitations.
"""


class ReportPromptBuilder:
    """Build the multimodal prompt for the AI Investigation Report."""

    @staticmethod
    def build_messages(
        structured_evidence: Dict[str, Any],
        crime_detection: Dict[str, Any],
        key_frames: List[Dict[str, Any]],
        is_video: bool = True,
    ) -> List[Dict[str, Any]]:
        """Build OpenAI-compatible messages list with text + image content."""

        # ── Text context ──
        media_meta = structured_evidence.get("media_metadata", {})
        detection_stats = structured_evidence.get("detection_stats", {})
        tracking_results = structured_evidence.get("tracking_results", [])
        events = structured_evidence.get("investigation_events", [])
        fir_meta = structured_evidence.get("fir_metadata", {})

        context_parts = [
            "=== MEDIA METADATA ===",
            json.dumps(media_meta, indent=2),
            "",
            "=== DETECTION STATISTICS ===",
            json.dumps(detection_stats, indent=2),
            "",
            "=== OBJECT TRACKING RESULTS ===",
            json.dumps(tracking_results, indent=2),
            "",
            "=== INVESTIGATION EVENTS TIMELINE ===",
            json.dumps(events, indent=2),
            "",
            "=== CRIME DETECTION LAYER RESULTS ===",
            json.dumps(crime_detection, indent=2),
            "",
            "=== FIR/CASE METADATA ===",
            json.dumps(fir_meta, indent=2),
            "",
        ]

        if key_frames:
            frame_meta = [
                {"frame_index": f["index"], "timestamp_seconds": f["timestamp_seconds"],
                 "width": f["width"], "height": f["height"]}
                for f in key_frames
            ]
            context_parts.extend([
                f"=== KEY EVIDENCE FRAMES ({len(key_frames)} frames supplied) ===",
                f"Frame metadata: {json.dumps(frame_meta)}",
                "The actual frame images are attached as image_url content parts below.",
                "Analyze each frame carefully and reference them by frame_index in your report.",
            ])
        else:
            context_parts.append("=== NO VISUAL FRAMES AVAILABLE (text-only analysis) ===")

        media_type = "video" if is_video else "image"
        context_parts.append(f"\nGenerate a complete AI Investigation Report for this {media_type} evidence. Respond with ONLY the JSON object.")

        text_content = "\n".join(context_parts)

        # ── Build user message content parts (multimodal) ──
        content_parts: List[Dict[str, Any]] = [
            {"type": "text", "text": text_content}
        ]

        for frame in key_frames:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame['base64_jpeg']}"
                }
            })

        return [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": content_parts},
        ]


# ═════════════════════════════════════════════════════════════════════
#  3.  DETERMINISTIC FALLBACK REPORT
# ═════════════════════════════════════════════════════════════════════

def generate_fallback_report(
    structured_evidence: Dict[str, Any],
    crime_detection: Dict[str, Any],
    key_frames: List[Dict[str, Any]],
    is_video: bool = True,
    fallback_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a deterministic structured report when LLM is unavailable."""
    media_meta = structured_evidence.get("media_metadata", {})
    detection_stats = structured_evidence.get("detection_stats", {})
    tracking_results = structured_evidence.get("tracking_results", [])
    events = structured_evidence.get("investigation_events", [])

    # Incident classification from crime detection layer
    crime_class = crime_detection.get("classification", "no_clear_crime_evidence")
    crime_conf = crime_detection.get("confidence", 0.5)
    crime_indicators = crime_detection.get("crime_indicators", [])

    if crime_class == "possible_crime":
        if "weapon_detected" in crime_indicators:
            incident_class = "Possible Weapon Offense"
        elif "aggressive_physical_interaction" in crime_indicators:
            incident_class = "Possible Violent Crime"
        elif "suspicious_movement" in crime_indicators:
            incident_class = "Suspicious Activity"
        else:
            incident_class = "Suspicious Activity"
    else:
        incident_class = "No Criminal Activity Observed"

    # Build executive summary
    file_name = media_meta.get("file_name", "evidence media")
    media_type = "video" if is_video else "image"
    total_dets = detection_stats.get("total_detections", 0)
    breakdown = detection_stats.get("class_breakdown", {})
    breakdown_str = ", ".join(f"{c} {cls}(s)" for cls, c in breakdown.items()) if breakdown else "no objects"

    summary = (
        f"Automated forensic analysis of {media_type} evidence '{file_name}' identified {total_dets} "
        f"detection(s) [{breakdown_str}] across {len(tracking_results)} tracked entities and "
        f"{len(events)} timeline event(s). "
        f"Crime detection layer classification: {crime_class} (confidence: {crime_conf:.0%}). "
        f"All observations are automated computer vision outputs requiring human investigative verification."
    )

    # Observed evidence from events
    observed_evidence = []
    for ev in events:
        observed_evidence.append({
            "observation": ev.get("description", ""),
            "source": "directly_observed",
            "confidence": ev.get("confidence", 0.5) or 0.5,
            "timestamp_seconds": ev.get("start_timestamp_seconds"),
            "tracking_id": ev.get("tracking_id"),
        })

    # Detected objects
    detected_objects = sorted(breakdown.keys()) if breakdown else []

    # Persons / vehicles
    detected_persons_vehicles = []
    for tr in tracking_results:
        entity_type = "person" if tr.get("object_class", "").lower() == "person" else \
                      "vehicle" if tr.get("object_class", "").lower() in ("car", "truck", "bus", "motorcycle", "bicycle") else \
                      "weapon" if tr.get("object_class", "").lower() in ("knife", "gun", "pistol", "rifle") else "object"
        detected_persons_vehicles.append({
            "entity_type": entity_type,
            "description": f"{tr['object_class'].title()} (Track #{tr['tracking_id']}) active for {tr.get('duration_active_seconds', 0)}s",
            "tracking_id": tr.get("tracking_id"),
            "first_seen_seconds": tr.get("start_timestamp_seconds"),
            "last_seen_seconds": tr.get("end_timestamp_seconds"),
            "confidence": tr.get("average_confidence", 0.5),
        })

    # Timeline
    timeline = []
    for ev in events:
        significance = "critical" if ev.get("event_type", "") in (
            "possible_person_down", "posture_falling", "pattern_multi_person_interaction",
            "physical_conflict", "weapon_detected"
        ) else "notable" if ev.get("confidence", 0) and ev["confidence"] > 0.7 else "routine"
        timeline.append({
            "timestamp_seconds": ev.get("start_timestamp_seconds", 0.0),
            "description": ev.get("description", ""),
            "source": "directly_observed",
            "significance": significance,
        })

    # Relevant timestamps from crime detection
    relevant_ts = crime_detection.get("relevant_timestamps", [])

    # Evidence frame references
    frame_refs = []
    for f in key_frames:
        frame_refs.append({
            "frame_index": f["index"],
            "timestamp_seconds": f["timestamp_seconds"],
            "description": f"Key evidence frame captured at {f['timestamp_seconds']}s ({f['width']}x{f['height']}px)",
            "relevant_observations": [
                f"Evaluated key frame #{f['index']} at timestamp {f['timestamp_seconds']}s"
            ],
        })

    reason = fallback_reason or "LLM integration unavailable or unconfigured"
    logger.info("Generated deterministic fallback report. Reason: %s", reason)

    return {
        "incident_classification": incident_class,
        "confidence": crime_conf,
        "executive_summary": summary,
        "observed_evidence": observed_evidence,
        "detected_objects": detected_objects,
        "detected_persons_vehicles": detected_persons_vehicles,
        "chronological_timeline": timeline,
        "relevant_timestamps": relevant_ts,
        "evidence_frame_references": frame_refs,
        "crime_indicators": crime_indicators,
        "uncertainty_notes": [
            "Computer vision detections and tracking bounding boxes are probabilistic automated outputs.",
            "Posture classification heuristics (e.g. lying_down, falling) are approximations requiring human verification.",
            "Low-resolution or partially occluded objects may not be detected or may be misclassified.",
        ],
        "limitations": [
            "Frame sampling interval creates temporal gaps between evaluated video frames.",
            "Tracking ID swaps may occur during object occlusion, bounding box overlap, or fast motion.",
            "Automated heuristics do not constitute legal evidence. Human forensic verification is mandatory.",
            "NEUTRAL FORENSIC NOTICE: Video/image evidence alone does not establish criminal intent, identity, or guilt.",
        ],
        "provider_used": "deterministic_fallback",
        "frames_supplied_to_model": len(key_frames),
        "fallback_reason": reason,
    }


# ═════════════════════════════════════════════════════════════════════
#  4.  AI REPORT GENERATOR (ORCHESTRATOR)
# ═════════════════════════════════════════════════════════════════════

class AIReportGenerator:
    """Orchestrates the full AI Investigation Report generation pipeline.

    Steps:
      1. Gather structured evidence (detections, tracking, events)
      2. Get crime detection results
      3. Extract key frames at relevant timestamps
      4. Build multimodal prompt
      5. Call existing LLM client (chat_completion)
      6. Parse & validate response
      7. Fall back to deterministic report if LLM unavailable
    """

    def generate_report(
        self,
        structured_evidence: Dict[str, Any],
        crime_detection: Dict[str, Any],
        media_file_path: Optional[str] = None,
        is_video: bool = True,
        media_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a complete AI Investigation Report.

        Args:
            structured_evidence: Output from summary_generator.build_structured_evidence
            crime_detection: Output from CrimeDetectionAnalyzer.analyze_video_evidence
            media_file_path: Path to the original media file (for frame extraction)
            is_video: Whether the media is a video
            media_id: Optional media ID for metadata

        Returns:
            Dict matching the AIInvestigationReportResponse schema
        """
        # ── Step 1: Determine key timestamps for frame extraction ──
        key_timestamps = self._select_key_timestamps(crime_detection, structured_evidence)

        # ── Step 2: Extract key frames ──
        key_frames: List[Dict[str, Any]] = []
        if media_file_path:
            if is_video:
                key_frames = KeyFrameExtractor.extract_video_frames(
                    media_file_path, key_timestamps, max_frames=MAX_KEY_FRAMES
                )
            else:
                key_frames = KeyFrameExtractor.extract_image_frame(media_file_path)

        logger.info(
            f"Report generation for media_id={media_id}: "
            f"{len(key_frames)} key frames extracted, is_video={is_video}"
        )

        # ── Step 3: Attempt LLM-powered report ──
        report = self._generate_llm_report(
            structured_evidence, crime_detection, key_frames, is_video
        )

        # ── Step 4: Attach metadata ──
        if media_id is not None:
            report["media_id"] = media_id
        report["frames_supplied_to_model"] = len(key_frames)
        report["created_at"] = datetime.utcnow().isoformat()

        return report

    def _select_key_timestamps(
        self,
        crime_detection: Dict[str, Any],
        structured_evidence: Dict[str, Any],
    ) -> List[float]:
        """Select timestamps for key frame extraction.

        Priority:
          1. Start of each relevant_timestamp range from crime detection
          2. Event timestamps where crime indicators were triggered
          3. First and last event timestamps for context
        """
        timestamps: List[float] = []

        # From crime detection relevant_timestamps
        for ts_range in crime_detection.get("relevant_timestamps", []):
            if isinstance(ts_range, dict):
                timestamps.append(ts_range.get("start", 0.0))
                mid = (ts_range.get("start", 0.0) + ts_range.get("end", 0.0)) / 2
                timestamps.append(mid)

        # From crime detection evidence_events
        for ev in crime_detection.get("evidence_events", []):
            ts = ev.get("timestamp_seconds", 0.0)
            if ts > 0:
                timestamps.append(ts)

        # From investigation events (critical ones)
        events = structured_evidence.get("investigation_events", [])
        critical_event_types = {
            "possible_person_down", "posture_falling", "posture_lying_down",
            "pattern_multi_person_interaction", "physical_conflict",
            "pattern_rapid_movement_chase", "weapon_detected",
        }
        for ev in events:
            if ev.get("event_type", "") in critical_event_types:
                timestamps.append(ev.get("start_timestamp_seconds", 0.0))

        # Add first and last event for context
        if events:
            timestamps.append(events[0].get("start_timestamp_seconds", 0.0))
            timestamps.append(events[-1].get("start_timestamp_seconds", 0.0))

        # Filter out zero/negative and deduplicate
        timestamps = [t for t in timestamps if t >= 0]
        return sorted(set(timestamps))

    def _generate_llm_report(
        self,
        structured_evidence: Dict[str, Any],
        crime_detection: Dict[str, Any],
        key_frames: List[Dict[str, Any]],
        is_video: bool,
    ) -> Dict[str, Any]:
        """Attempt LLM-powered report, fall back to deterministic if unavailable."""
        fallback_reason: Optional[str] = None
        try:
            from app.chat.llm import chat_completion
            from app.core.config import settings

            if not settings.GEMINI_API_KEY:
                fallback_reason = "GEMINI_API_KEY is not set in backend/.env"
                logger.warning("LLM report generation skipped: %s", fallback_reason)
                return generate_fallback_report(
                    structured_evidence, crime_detection, key_frames, is_video, fallback_reason=fallback_reason
                )

            messages = ReportPromptBuilder.build_messages(
                structured_evidence, crime_detection, key_frames, is_video
            )

            logger.info("Calling Gemini API (%s) for multimodal report generation with %d frames...",
                        settings.LLM_REPORT_MODEL, len(key_frames))

            response = chat_completion(
                messages=messages,
                model=settings.LLM_REPORT_MODEL,
                temperature=0.1,
                max_tokens=settings.LLM_REPORT_MAX_TOKENS,
            )

            raw_text = response.choices[0].message.content or ""

            # Clean markdown code blocks if present
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()

            data = json.loads(clean_text)

            # Validate required keys
            required_keys = [
                "incident_classification", "confidence", "executive_summary",
                "observed_evidence", "detected_objects", "chronological_timeline",
                "crime_indicators", "uncertainty_notes", "limitations",
            ]
            if all(k in data for k in required_keys):
                # Safety guardrail: reject accusatory language
                summary_lower = data.get("executive_summary", "").lower()
                if "guilty" in summary_lower or "criminal" in summary_lower or "perpetrator" in summary_lower:
                    fallback_reason = "LLM output violated legal guardrails (contained accusatory language)"
                    logger.warning("%s. Falling back to deterministic report.", fallback_reason)
                    return generate_fallback_report(structured_evidence, crime_detection, key_frames, is_video, fallback_reason=fallback_reason)

                data["provider_used"] = "gemini_vision" if key_frames else "gemini_llm"
                data["fallback_reason"] = None
                data["frames_supplied_to_model"] = len(key_frames)

                # Ensure evidence_frame_references is populated if empty and frames were supplied
                if not data.get("evidence_frame_references") and key_frames:
                    data["evidence_frame_references"] = [
                        {
                            "frame_index": f["index"],
                            "timestamp_seconds": f["timestamp_seconds"],
                            "description": f"Key evidence frame #{f['index']} captured at {f['timestamp_seconds']}s",
                            "relevant_observations": [f"Visually evaluated frame at {f['timestamp_seconds']}s"]
                        }
                        for f in key_frames
                    ]

                return data
            else:
                missing = [k for k in required_keys if k not in data]
                fallback_reason = f"LLM output missing required keys: {missing}"
                logger.warning("%s. Falling back to deterministic report.", fallback_reason)

        except Exception as exc:
            fallback_reason = f"Gemini API call failed: {exc}"
            logger.error("Gemini API call failed during report generation: %s", exc, exc_info=True)

        return generate_fallback_report(structured_evidence, crime_detection, key_frames, is_video, fallback_reason=fallback_reason)



# ═════════════════════════════════════════════════════════════════════
#  5.  STANDALONE FUNCTION (for service layer / tests)
# ═════════════════════════════════════════════════════════════════════

def generate_ai_investigation_report(
    structured_evidence: Dict[str, Any],
    crime_detection: Dict[str, Any],
    media_file_path: Optional[str] = None,
    is_video: bool = True,
    media_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Convenience function wrapping AIReportGenerator.generate_report."""
    generator = AIReportGenerator()
    return generator.generate_report(
        structured_evidence=structured_evidence,
        crime_detection=crime_detection,
        media_file_path=media_file_path,
        is_video=is_video,
        media_id=media_id,
    )
