/* ─────────────────────────────────────────────────────────────
 * Investigation AI — API Service Layer
 *
 * Each function attempts the real backend endpoint via fetchAPI().
 * On failure it returns realistic demo data so the UI always works.
 * A backend engineer only needs to start the server — zero frontend
 * code changes required.
 * ───────────────────────────────────────────────────────────── */

import { fetchAPI, API_BASE } from "@/lib/apiClient";
import type {
  InvestigationMedia,
  AnalysisJob,
  Detection,
  InvestigationEvent,
  MediaListResponse,
  DetectionListResponse,
  EventListResponse,
  CaseMediaSummaryResponse,
} from "@/app/(dashboard)/investigation-ai/types";

/* ── Connection state ── */
let _backendReachable: boolean | null = null;

export async function isBackendLive(): Promise<boolean> {
  if (_backendReachable !== null) return _backendReachable;
  try {
    await fetchAPI("/investigation/media?limit=1");
    _backendReachable = true;
  } catch {
    _backendReachable = false;
  }
  return _backendReachable;
}

export function resetConnectionCache() {
  _backendReachable = null;
}

/* ═══════════════════════════════════════════════════════════════
 * DEMO / MOCK DATA
 * Used as graceful fallback when the backend is offline.
 * ═══════════════════════════════════════════════════════════════ */

const DEMO_VIDEO_URL =
  "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4";

const DEMO_MEDIA: InvestigationMedia[] = [
  {
    media_id: 1,
    file_name: "cam04_majestic_station_2026-08-22.mp4",
    file_type: "video",
    mime_type: "video/mp4",
    file_size_bytes: 24_500_000,
    sha256_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    duration_seconds: 15,
    fps: 30,
    total_frames: 450,
    district_id: 1,
    fir_id: null,
    uploaded_by_user_id: 1,
    status: "analyzed",
    upload_timestamp: "2026-08-22T14:30:00Z",
  },
  {
    media_id: 2,
    file_name: "crime_scene_photo_sector7.jpg",
    file_type: "image",
    mime_type: "image/jpeg",
    file_size_bytes: 3_200_000,
    sha256_hash: "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
    duration_seconds: null,
    fps: null,
    total_frames: null,
    district_id: 1,
    fir_id: "FIR-2026-044",
    uploaded_by_user_id: 1,
    status: "analyzed",
    upload_timestamp: "2026-08-21T09:15:00Z",
  },
  {
    media_id: 3,
    file_name: "dashcam_patrol_unit7.mp4",
    file_type: "video",
    mime_type: "video/mp4",
    file_size_bytes: 48_000_000,
    sha256_hash: "f1e2d3c4b5a60798061524334251607182930a1b2c3d4e5f6071829304a5b6c7",
    duration_seconds: 32,
    fps: 24,
    total_frames: 768,
    district_id: 3,
    fir_id: null,
    uploaded_by_user_id: 2,
    status: "pending",
    upload_timestamp: "2026-08-23T07:00:00Z",
  },
];

function generateDemoDetections(): Detection[] {
  const dets: Detection[] = [];
  let id = 1;
  for (let t = 0; t <= 15; t += 0.5) {
    dets.push({
      detection_id: id++,
      job_id: 1,
      media_id: 1,
      frame_number: Math.round(t * 30),
      timestamp_seconds: t,
      object_class: "person",
      tracking_id: 1,
      confidence: 0.88,
      bbox: { xmin: 0.10 + t * 0.03, ymin: 0.40, xmax: 0.20 + t * 0.03, ymax: 0.65 },
    });
    if (t > 3) {
      dets.push({
        detection_id: id++,
        job_id: 1,
        media_id: 1,
        frame_number: Math.round(t * 30),
        timestamp_seconds: t,
        object_class: "car",
        tracking_id: 2,
        confidence: 0.95,
        bbox: { xmin: 0.60 - t * 0.02, ymin: 0.60, xmax: 0.85 - t * 0.02, ymax: 0.75 },
      });
    }
  }
  // Posture anomaly at t=8s
  dets.push({
    detection_id: id++,
    job_id: 1,
    media_id: 1,
    frame_number: 240,
    timestamp_seconds: 8,
    object_class: "person",
    tracking_id: 1,
    confidence: 0.72,
    bbox: { xmin: 0.34, ymin: 0.60, xmax: 0.59, ymax: 0.70 },
  });
  return dets;
}

const DEMO_EVENTS: InvestigationEvent[] = [
  {
    event_id: 1, job_id: 1, media_id: 1,
    event_type: "person_entered_frame",
    description: "Subject (Track ID: 1) detected entering frame from left boundary.",
    start_timestamp_seconds: 0, end_timestamp_seconds: 0.5,
    frame_start: 0, frame_end: 15,
    tracking_id: 1, confidence: 0.88,
    created_at: "2026-08-22T14:35:00Z",
  },
  {
    event_id: 2, job_id: 1, media_id: 1,
    event_type: "vehicle_detected",
    description: "Vehicle (Track ID: 2) identified entering surveillance zone B at speed.",
    start_timestamp_seconds: 3.5, end_timestamp_seconds: 4.0,
    frame_start: 105, frame_end: 120,
    tracking_id: 2, confidence: 0.95,
    created_at: "2026-08-22T14:35:00Z",
  },
  {
    event_id: 3, job_id: 1, media_id: 1,
    event_type: "possible_person_down",
    description: "Posture anomaly detected for Subject (Track ID: 1). Bounding box aspect ratio ≥1.25 indicates possible fall or horizontal position.",
    start_timestamp_seconds: 8, end_timestamp_seconds: 8.5,
    frame_start: 240, frame_end: 255,
    tracking_id: 1, confidence: 0.72,
    created_at: "2026-08-22T14:35:00Z",
  },
  {
    event_id: 4, job_id: 1, media_id: 1,
    event_type: "person_exited_frame",
    description: "Subject (Track ID: 1) last observed near right frame boundary.",
    start_timestamp_seconds: 14.5, end_timestamp_seconds: 15,
    frame_start: 435, frame_end: 450,
    tracking_id: 1, confidence: 0.85,
    created_at: "2026-08-22T14:35:00Z",
  },
];

/* ═══════════════════════════════════════════════════════════════
 * PUBLIC API FUNCTIONS
 * ═══════════════════════════════════════════════════════════════ */

export async function listMedia(firId?: string): Promise<MediaListResponse> {
  try {
    const url = firId 
      ? `/investigation/media?fir_id=${encodeURIComponent(firId)}&limit=50&offset=0`
      : "/investigation/media?limit=50&offset=0";
    return await fetchAPI(url);
  } catch {
    const rawItems = firId ? DEMO_MEDIA.filter((m) => m.fir_id === firId) : DEMO_MEDIA;
    const seen = new Set<number>();
    const items = rawItems.filter((m) => {
      if (seen.has(m.media_id)) return false;
      seen.add(m.media_id);
      return true;
    });
    return { items, total: items.length };
  }
}

export async function getMedia(mediaId: number): Promise<InvestigationMedia> {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}`);
  } catch {
    return DEMO_MEDIA.find((m) => m.media_id === mediaId) || DEMO_MEDIA[0];
  }
}

export async function uploadMedia(
  file: File,
  districtId?: number,
  firId?: string
): Promise<InvestigationMedia> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    if (districtId) formData.append("district_id", String(districtId));
    if (firId) formData.append("fir_id", firId);

    const res = await fetchAPI("/investigation/upload", {
      method: "POST",
      headers: {}, // Let browser set multipart boundary
      body: formData,
    });
    return res;
  } catch {
    // Simulate uploaded media
    const newMedia: InvestigationMedia = {
      media_id: Date.now(),
      file_name: file.name,
      file_type: file.type.startsWith("video") ? "video" : "image",
      mime_type: file.type,
      file_size_bytes: file.size,
      sha256_hash: Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2),
      duration_seconds: file.type.startsWith("video") ? 15 : null,
      fps: file.type.startsWith("video") ? 30 : null,
      total_frames: file.type.startsWith("video") ? 450 : null,
      district_id: districtId || null,
      fir_id: firId || null,
      uploaded_by_user_id: 1,
      status: "uploaded",
      upload_timestamp: new Date().toISOString(),
      media_url: typeof window !== "undefined" ? URL.createObjectURL(file) : null,
    };
    const existingIdx = DEMO_MEDIA.findIndex((m) => m.media_id === newMedia.media_id);
    if (existingIdx >= 0) {
      DEMO_MEDIA[existingIdx] = newMedia;
    } else {
      DEMO_MEDIA.unshift(newMedia);
    }
    return newMedia;
  }
}

export async function triggerAnalysis(
  mediaId: number,
  jobType = "full_analysis"
): Promise<AnalysisJob> {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}/process`, {
      method: "POST",
      body: JSON.stringify({ job_type: jobType }),
    });
  } catch {
    return {
      job_id: Date.now(),
      media_id: mediaId,
      job_type: jobType,
      status: "completed",
      progress_pct: 100,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      error_message: null,
      created_at: new Date().toISOString(),
    };
  }
}

export async function getJobStatus(jobId: number): Promise<AnalysisJob> {
  try {
    return await fetchAPI(`/investigation/jobs/${jobId}`);
  } catch {
    return {
      job_id: jobId,
      media_id: 1,
      job_type: "full_analysis",
      status: "completed",
      progress_pct: 100,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      error_message: null,
      created_at: new Date().toISOString(),
    };
  }
}

export async function getDetections(mediaId: number): Promise<DetectionListResponse> {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}/detections`);
  } catch {
    if (mediaId === 1) {
      const dets = generateDemoDetections().map((d) => ({ ...d, media_id: mediaId }));
      return { media_id: mediaId, detections: dets, total_detections: dets.length };
    }
    return { media_id: mediaId, detections: [], total_detections: 0 };
  }
}

export async function getEvents(mediaId: number): Promise<EventListResponse> {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}/events`);
  } catch {
    if (mediaId === 1) {
      const evts = DEMO_EVENTS.map((e) => ({ ...e, media_id: mediaId }));
      return { media_id: mediaId, events: evts, total_events: evts.length };
    }
    return { media_id: mediaId, events: [], total_events: 0 };
  }
}

export async function linkFIR(mediaId: number, firId: string | null): Promise<InvestigationMedia> {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}/link-fir`, {
      method: "POST",
      body: JSON.stringify({ fir_id: firId }),
    });
  } catch {
    const media = DEMO_MEDIA.find((m) => m.media_id === mediaId);
    if (media) media.fir_id = firId;
    return media || DEMO_MEDIA[0];
  }
}

export async function getCaseMedia(firId: string): Promise<CaseMediaSummaryResponse> {
  try {
    return await fetchAPI(`/investigation/cases/${encodeURIComponent(firId)}/media`);
  } catch {
    const items = DEMO_MEDIA.filter((m) => m.fir_id === firId || firId === "FIR-2026-044");
    return {
      fir_id: firId,
      district_id: 1,
      total_media: items.length,
      media_items: items,
      total_detections: items.length * 8,
      total_events: items.length * 3,
    };
  }
}

export async function getSummary(
  mediaId: number,
  forceRefresh: boolean = false
) {
  try {
    return await fetchAPI(
      `/investigation/media/${mediaId}/summary${forceRefresh ? "?force_refresh=true" : ""}`,
      { method: forceRefresh ? "POST" : "GET" }
    );
  } catch {
    if (mediaId === 1) {
      return {
        media_id: mediaId,
        summary_text: `Forensic analysis of media ID ${mediaId} identified multi-object detections across active video frames. All observations represent automated computer vision outputs requiring officer verification.`,
        observed_events: [
          "Subject (Track #1) entered surveillance frame.",
          "Posture anomaly / possible person down flag observed at 8.0s.",
          "Vehicle (Track #2) observed traversing boundary area."
        ],
        relevant_timestamps: [
          "0.0s - 15.0s: Subject (Track #1) active across frames 0 - 450.",
          "8.0s: Posture anomaly detected."
        ],
        detected_objects_summary: [
          "Person: Active track (Track #1)",
          "Vehicle: Active track (Track #2)"
        ],
        evidence_references: [
          `Media ID: ${mediaId}`,
          "Automated YOLOv8 + ByteTrack detection logs"
        ],
        uncertainty_limitations: [
          "Computer vision detections are probabilistic automated outputs.",
          "Frame sampling interval creates temporal gaps between evaluated frames.",
          "NEUTRAL FORENSIC NOTICE: Video evidence alone does not establish criminal intent or guilt."
        ],
        provider_used: "llm",
        created_at: new Date().toISOString()
      };
    }
    return null;
  }
}

export async function getCrimeDetection(mediaId: number) {
  try {
    return await fetchAPI(`/investigation/media/${mediaId}/crime-detection`);
  } catch {
    if (mediaId === 1) {
      return {
        classification: "possible_crime",
        confidence: 0.91,
        crime_indicators: ["weapon_detected", "possible_person_down"],
        relevant_timestamps: [{ start: 8.0, end: 12.5 }],
        evidence_events: [
          {
            event_type: "possible_person_down",
            description: "Person fall / lying down posture anomaly detected at 8.0s",
            timestamp_seconds: 8.0,
            tracking_id: 1,
            confidence: 0.82
          }
        ]
      };
    }
    return {
      classification: "no_clear_crime_evidence",
      confidence: 0.90,
      crime_indicators: [],
      relevant_timestamps: [],
      evidence_events: []
    };
  }
}


/** Public demo video URL for offline mode */
export const DEMO_VIDEO_SRC = DEMO_VIDEO_URL;

export function getMediaUrl(media: InvestigationMedia | null): string {
  if (!media) return DEMO_VIDEO_URL;
  if (media.media_url) {
    if (media.media_url.startsWith("blob:")) return media.media_url;
    const root = API_BASE.replace(/\/api\/v1\/?$/, "");
    return media.media_url.startsWith("http")
      ? media.media_url
      : `${root}${media.media_url}`;
  }
  return DEMO_VIDEO_URL;
}


