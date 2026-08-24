"""LLM Investigation Summary Generator.

Gathers structured evidence (detections, tracking, events, authorized FIR metadata),
enforces legal & factual safety guardrails, and invokes the LLM integration
to produce forensic investigation summaries with explicit caveats.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.rbac import User
from app.investigation_ai.models import (
    InvestigationMedia,
    DetectionResult,
    InvestigationEvent,
    InvestigationAnalysisJob,
    InvestigationSummary,
)
from app.graph import csv_graph

logger = get_logger("investigation_ai.summary_generator")

SYSTEM_PROMPT = """You are CrimeRakshak AI Forensic Investigation Assistant for Karnataka State Police.
Your task is to generate a concise, objective, forensic-grade LLM Investigation Summary based strictly on the provided structured evidence.

STRUCTURED EVIDENCE INCLUDES:
1. Media Metadata (file type, duration, fps, frames)
2. Detection Results (object classes, confidence scores, bounding boxes)
3. Object Tracking Results (Track IDs, start/end timestamps, active frame counts)
4. Investigation Events (timeline of motion/posture/entry/exit events)
5. Case/FIR Metadata (linked case details where authorized)

REQUIRED SUMMARY OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object matching the exact structure below:
{
  "summary_text": "A concise 2-4 sentence prose narrative summarizing the evidence observed.",
  "observed_events": [
    "Bullet point describing observed timeline event 1...",
    "Bullet point describing observed timeline event 2..."
  ],
  "relevant_timestamps": [
    "0.0s - 3.5s: Person (Track #1) active in frame",
    "2.0s: Horizontal posture / possible person down detected (Track #2)"
  ],
  "detected_objects_summary": [
    "Person: 2 unique track IDs detected (Track #1, Track #2)",
    "Vehicle (Car): 1 track ID detected (Track #10)"
  ],
  "evidence_references": [
    "Media ID: 101 (cctv_junction_crossroad.mp4)",
    "Detections: 15 bounding boxes across 3 sampled frames",
    "Linked Case: FIR-2026-BLR-089 (Murder / Theft)"
  ],
  "uncertainty_limitations": [
    "Computer vision detection confidence ranges between 85% - 96%.",
    "Frame sampling rate (2 fps) creates 0.5s temporal gaps between evaluated frames.",
    "Tracking ID swaps may occur during bounding box overlap or occlusion.",
    "Camera resolution and lighting conditions may impact object detection quality.",
    "Automated posture heuristics (e.g. possible_person_down) require human forensic verification."
  ]
}

CRITICAL LEGAL AND SAFETY GUARDRAILS:
1. DO NOT INVENT FACTS or speculate beyond the provided evidence.
2. DO NOT IDENTIFY ANY PERSON AS A CRIMINAL, SUSPECT, PERPETRATOR, OR GUILTY PARTY based only on video/image evidence or detection heuristics.
3. Maintain neutral, objective, forensic analytical language (e.g., 'Individual corresponding to Track #1 observed...' instead of 'The perpetrator entered...').
4. Do not state legal conclusions or make accusations. Frame automated detections as technical observations requiring human investigative verification.
"""


def build_structured_evidence(
    db: Session,
    media: InvestigationMedia,
    user: User,
) -> Dict[str, Any]:
    """Gather structured evidence from detections, tracking, events, and authorized FIR metadata."""
    # 1. Media Metadata
    media_meta = {
        "media_id": media.media_id,
        "file_name": media.file_name,
        "file_type": media.file_type,
        "duration_seconds": media.duration_seconds,
        "fps": media.fps,
        "total_frames": media.total_frames,
        "district_id": media.district_id,
        "fir_id": media.fir_id,
        "status": media.status,
        "upload_timestamp": media.upload_timestamp.isoformat() if media.upload_timestamp else None,
    }

    # 2. Detections
    raw_detections = db.execute(
        select(DetectionResult)
        .where(DetectionResult.media_id == media.media_id)
        .order_by(DetectionResult.frame_number.asc())
    ).scalars().all()

    total_detections = len(raw_detections)
    class_counts: Dict[str, int] = defaultdict(int)
    class_confidences: Dict[str, List[float]] = defaultdict(list)
    tracks: Dict[int, Dict[str, Any]] = {}

    for d in raw_detections:
        class_counts[d.object_class] += 1
        class_confidences[d.object_class].append(d.confidence)
        
        if d.tracking_id is not None:
            tid = d.tracking_id
            if tid not in tracks:
                tracks[tid] = {
                    "tracking_id": tid,
                    "object_class": d.object_class,
                    "first_frame": d.frame_number,
                    "last_frame": d.frame_number,
                    "start_time": d.timestamp_seconds,
                    "end_time": d.timestamp_seconds,
                    "detection_count": 0,
                    "confidences": [],
                }
            tracks[tid]["last_frame"] = d.frame_number
            tracks[tid]["end_time"] = d.timestamp_seconds
            tracks[tid]["detection_count"] += 1
            tracks[tid]["confidences"].append(d.confidence)

    detection_stats = {
        "total_detections": total_detections,
        "class_breakdown": dict(class_counts),
        "class_confidence_summary": {
            cls: {
                "min": round(min(confs), 2),
                "max": round(max(confs), 2),
                "avg": round(sum(confs) / len(confs), 2),
            }
            for cls, confs in class_confidences.items()
        },
    }

    # 3. Tracking Results
    tracking_results = []
    for tid, info in sorted(tracks.items(), key=lambda x: x[0]):
        avg_conf = sum(info["confidences"]) / len(info["confidences"]) if info["confidences"] else 0.0
        duration_sec = round(info["end_time"] - info["start_time"], 2)
        tracking_results.append({
            "tracking_id": tid,
            "object_class": info["object_class"],
            "start_timestamp_seconds": round(info["start_time"], 2),
            "end_timestamp_seconds": round(info["end_time"], 2),
            "duration_active_seconds": duration_sec,
            "active_frames": f"{info['first_frame']} - {info['last_frame']}",
            "detection_count": info["detection_count"],
            "average_confidence": round(avg_conf, 2),
        })

    # 4. Investigation Events
    raw_events = db.execute(
        select(InvestigationEvent)
        .where(InvestigationEvent.media_id == media.media_id)
        .order_by(InvestigationEvent.start_timestamp_seconds.asc())
    ).scalars().all()

    events_summary = []
    for ev in raw_events:
        events_summary.append({
            "event_id": ev.event_id,
            "event_type": ev.event_type,
            "description": ev.description,
            "start_timestamp_seconds": round(ev.start_timestamp_seconds, 2),
            "end_timestamp_seconds": round(ev.end_timestamp_seconds, 2),
            "frame_range": f"{ev.frame_start} - {ev.frame_end}",
            "tracking_id": ev.tracking_id,
            "confidence": round(ev.confidence, 2) if ev.confidence else None,
        })

    # 5. Authorized Case/FIR Metadata
    fir_metadata: Dict[str, Any] = {"status": "No linked FIR case number."}
    
    # Check authorization: user is superuser or media district matches user district or media has no district constraint
    is_authorized = (
        user.is_superuser
        or media.district_id is None
        or (user.district_id is not None and user.district_id == media.district_id)
    )

    if media.fir_id:
        if is_authorized:
            try:
                profile = csv_graph.get_fir_profile(media.fir_id)
                if profile and "fir" in profile:
                    props = profile["fir"].get("properties", {})
                    fir_metadata = {
                        "authorized": True,
                        "fir_id": media.fir_id,
                        "crime_type": props.get("crime_type"),
                        "modus_operandi": props.get("modus_operandi"),
                        "sections": props.get("sections"),
                        "status": props.get("status"),
                        "date": props.get("date"),
                        "district": props.get("district"),
                        "accused_count": len(profile.get("accused", [])),
                        "victim_count": len(profile.get("victims", [])),
                    }
                else:
                    fir_metadata = {
                        "authorized": True,
                        "fir_id": media.fir_id,
                        "status": f"FIR case number '{media.fir_id}' recorded; full case profile pending graph ingestion.",
                    }
            except Exception as e:
                fir_metadata = {
                    "authorized": True,
                    "fir_id": media.fir_id,
                    "status": f"FIR '{media.fir_id}' linked.",
                    "lookup_note": str(e),
                }
        else:
            fir_metadata = {
                "authorized": False,
                "fir_id": media.fir_id,
                "status": "FIR metadata access restricted due to district scope authorization policies.",
            }

    return {
        "media_metadata": media_meta,
        "detection_stats": detection_stats,
        "tracking_results": tracking_results,
        "investigation_events": events_summary,
        "fir_metadata": fir_metadata,
    }


def generate_fallback_summary(structured_evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a deterministic, grounded fallback summary adhering to all safety guardrails."""
    media_meta = structured_evidence.get("media_metadata", {})
    detection_stats = structured_evidence.get("detection_stats", {})
    tracking_results = structured_evidence.get("tracking_results", [])
    events = structured_evidence.get("investigation_events", [])
    fir_meta = structured_evidence.get("fir_metadata", {})

    media_id = media_meta.get("media_id", 0)
    file_name = media_meta.get("file_name", "evidence media")
    file_type = media_meta.get("file_type", "media")
    total_dets = detection_stats.get("total_detections", 0)
    breakdown = detection_stats.get("class_breakdown", {})

    # Prose Summary
    breakdown_str = ", ".join([f"{count} {cls}(s)" for cls, count in breakdown.items()]) if breakdown else "no objects"
    fir_str = f"Linked to Case FIR '{fir_meta.get('fir_id')}'." if fir_meta.get("fir_id") else "No FIR linked."
    
    summary_text = (
        f"Forensic evaluation of {file_type} media '{file_name}' (ID: {media_id}) identified a total of {total_dets} "
        f"object detection(s) [{breakdown_str}] across {len(tracking_results)} tracked trajectory paths and {len(events)} "
        f"timeline event(s). {fir_str} All observed detections represent automated computer vision outputs requiring officer verification."
    )

    # Observed Events
    observed_events = []
    for ev in events:
        t_str = f"At {ev['start_timestamp_seconds']}s" if ev['start_timestamp_seconds'] == ev['end_timestamp_seconds'] else f"From {ev['start_timestamp_seconds']}s to {ev['end_timestamp_seconds']}s"
        track_str = f" (Track #{ev['tracking_id']})" if ev.get('tracking_id') is not None else ""
        observed_events.append(f"{t_str}: {ev['description']}{track_str}")
    if not observed_events:
        observed_events = ["No discrete timeline events extracted from media detections."]

    # Relevant Timestamps
    relevant_timestamps = []
    for tr in tracking_results:
        relevant_timestamps.append(
            f"{tr['start_timestamp_seconds']}s - {tr['end_timestamp_seconds']}s: {tr['object_class'].title()} (Track #{tr['tracking_id']}) active across frames {tr['active_frames']}."
        )
    if not relevant_timestamps:
        relevant_timestamps = ["0.0s: Single frame / static image analysis."]

    # Detected Objects
    detected_objects_summary = []
    for cls, count in breakdown.items():
        tracks_for_cls = [str(tr['tracking_id']) for tr in tracking_results if tr['object_class'] == cls]
        track_info = f" [Track IDs: #{', #'.join(tracks_for_cls)}]" if tracks_for_cls else ""
        detected_objects_summary.append(f"{cls.title()}: {count} bounding box detection(s){track_info}.")
    if not detected_objects_summary:
        detected_objects_summary = ["No objects detected above confidence threshold."]

    # Evidence References
    evidence_references = [
        f"Media File: {file_name} (Media ID: {media_id})",
        f"Detections: {total_dets} bounding box record(s)",
    ]
    if fir_meta.get("fir_id"):
        crime_info = f" ({fir_meta.get('crime_type')})" if fir_meta.get("crime_type") else ""
        evidence_references.append(f"Linked FIR Case: {fir_meta['fir_id']}{crime_info}")

    # Uncertainty & Limitations
    uncertainty_limitations = [
        "Computer vision detections and tracking bounding boxes are probabilistic automated outputs.",
        "Frame sampling interval creates temporal gaps between evaluated video frames.",
        "Tracking ID swaps may occur during object occlusion, bounding box overlap, or fast motion.",
        "Automated heuristics (such as posture or entry/exit flags) require human forensic verification.",
        "NEUTRAL FORENSIC NOTICE: Video evidence alone does not establish criminal intent, identity, or guilt."
    ]

    return {
        "summary_text": summary_text,
        "observed_events": observed_events,
        "relevant_timestamps": relevant_timestamps,
        "detected_objects_summary": detected_objects_summary,
        "evidence_references": evidence_references,
        "uncertainty_limitations": uncertainty_limitations,
        "provider_used": "deterministic_fallback",
    }


def generate_llm_summary(structured_evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM integration to generate summary or fallback cleanly if unconfigured/error."""
    try:
        from app.chat.llm import chat_completion, LLMConfigError
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Please generate an investigation summary for this structured evidence:\n\n{json.dumps(structured_evidence, indent=2)}"}
        ]

        response = chat_completion(messages=messages, temperature=0.1)
        raw_text = response.choices[0].message.content or ""
        
        # Clean markdown codeblocks if present
        clean_text = raw_text.strip()
        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()

        data = json.loads(clean_text)
        
        # Verify required keys present
        required_keys = ["summary_text", "observed_events", "relevant_timestamps", "detected_objects_summary", "evidence_references", "uncertainty_limitations"]
        if all(k in data for k in required_keys):
            # Sanity guardrail check: ensure no criminal accusation language introduced
            summary_prose = data["summary_text"].lower()
            if "guilty" in summary_prose or "criminal" in summary_prose:
                logger.warning("LLM generated output violating non-accusation policy. Reverting to fallback summary.")
                return generate_fallback_summary(structured_evidence)

            data["provider_used"] = "llm"
            return data
            
    except Exception as exc:
        logger.info(f"LLM summary generation unavailable or failed ({exc}). Using structured fallback summary.")

    return generate_fallback_summary(structured_evidence)


def get_or_create_investigation_summary(
    db: Session,
    media: InvestigationMedia,
    user: User,
    force_refresh: bool = False,
) -> InvestigationSummary:
    """Retrieve existing summary or generate and persist a new LLM Investigation Summary."""
    if not force_refresh:
        existing = (
            db.execute(
                select(InvestigationSummary)
                .where(InvestigationSummary.media_id == media.media_id)
                .order_by(InvestigationSummary.created_at.desc())
            )
            .scalars()
            .first()
        )
        if existing:
            return existing

    structured_evidence = build_structured_evidence(db, media, user)
    summary_data = generate_llm_summary(structured_evidence)

    # Latest completed job if any
    latest_job = (
        db.execute(
            select(InvestigationAnalysisJob)
            .where(InvestigationAnalysisJob.media_id == media.media_id)
            .order_by(InvestigationAnalysisJob.created_at.desc())
        )
        .scalars()
        .first()
    )
    job_id = latest_job.job_id if latest_job else None

    summary_rec = InvestigationSummary(
        media_id=media.media_id,
        job_id=job_id,
        summary_text=summary_data.get("summary_text", ""),
        observed_events=json.dumps(summary_data.get("observed_events", [])),
        relevant_timestamps=json.dumps(summary_data.get("relevant_timestamps", [])),
        detected_objects_summary=json.dumps(summary_data.get("detected_objects_summary", [])),
        evidence_references=json.dumps(summary_data.get("evidence_references", [])),
        uncertainty_limitations=json.dumps(summary_data.get("uncertainty_limitations", [])),
        provider_used=summary_data.get("provider_used", "llm"),
    )
    db.add(summary_rec)
    db.commit()
    db.refresh(summary_rec)

    return summary_rec
