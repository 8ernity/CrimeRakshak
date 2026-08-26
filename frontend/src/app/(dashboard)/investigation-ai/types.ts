/* ─────────────────────────────────────────────────────────────
 * Investigation AI — TypeScript Interfaces
 * Maps 1:1 to backend Pydantic schemas (schemas.py)
 * ───────────────────────────────────────────────────────────── */

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface Detection {
  detection_id: number;
  job_id: number;
  media_id: number;
  frame_number: number;
  timestamp_seconds: number;
  object_class: string;
  tracking_id: number | null;
  confidence: number;
  bbox: BoundingBox;
  crop_image_path?: string | null;
}

export interface InvestigationEvent {
  event_id: number;
  job_id: number;
  media_id: number;
  event_type: string;
  description: string;
  start_timestamp_seconds: number;
  end_timestamp_seconds: number;
  frame_start: number;
  frame_end: number;
  tracking_id: number | null;
  confidence: number | null;
  linked_person_id?: string | null;
  linked_fir_id?: string | null;
  created_at: string;
}

export interface InvestigationMedia {
  media_id: number;
  file_name: string;
  file_type: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  duration_seconds: number | null;
  fps: number | null;
  total_frames: number | null;
  district_id: number | null;
  fir_id: string | null;
  uploaded_by_user_id: number | null;
  status: string;
  upload_timestamp: string;
  media_url?: string | null;
}

export interface AnalysisJob {
  job_id: number;
  media_id: number;
  job_type: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress_pct: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

/* ── Aggregate Response Wrappers ── */

export interface DetectionListResponse {
  media_id: number;
  detections: Detection[];
  total_detections: number;
}

export interface EventListResponse {
  media_id: number;
  events: InvestigationEvent[];
  total_events: number;
}

export interface MediaListResponse {
  items: InvestigationMedia[];
  total: number;
}

export interface CaseMediaSummaryResponse {
  fir_id: string;
  district_id: number | null;
  total_media: number;
  media_items: InvestigationMedia[];
  total_detections: number;
  total_events: number;
}

export interface InvestigationSummary {
  summary_id?: number | null;
  media_id: number;
  job_id?: number | null;
  summary_text: string;
  observed_events: string[];
  relevant_timestamps: string[];
  detected_objects_summary: string[];
  evidence_references: string[];
  uncertainty_limitations: string[];
  provider_used: string;
  created_at: string;
}

export interface TimestampRange {
  start: number;
  end: number;
}

export interface CrimeVideoDetection {
  classification: "possible_crime" | "no_clear_crime_evidence";
  confidence: number;
  crime_indicators: string[];
  relevant_timestamps: TimestampRange[];
  evidence_events: any[];
}


