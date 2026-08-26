// Sentinel Grid — API service layer
// Follows the same pattern as predictiveHotspotsApi.ts:
//   - Try live backend first, fall back to demo data transparently.
//   - WebSocket wrapper with exponential-backoff auto-reconnect.

import { fetchAPI, API_BASE } from "@/lib/apiClient";
import { DEMO_SENSOR_EVENTS, DEMO_SENTINEL_SUMMARY } from "@/data/sentinelDemoData";
import type { DemoSensorEvent } from "@/data/sentinelDemoData";

export type { DemoSensorEvent as SensorEvent };
export type DataSource = "live" | "demo";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface SentinelSummary {
  active_sensors: number;
  events_last_24h: number;
  high_priority_active: number;
  cases_auto_linked: number;
  source: DataSource;
}

export interface SentinelEventsFilters {
  timeWindowHours?: 1 | 6 | 24;
  priority?: "all" | "high" | "normal";
  sensorType?: "all" | "cctv_alert" | "anpr_hit" | "sos_button" | "gunshot";
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────────────────────

export async function getSentinelSummary(): Promise<SentinelSummary> {
  try {
    const data = await fetchAPI("/sentinel/summary");
    return { ...data, source: "live" as DataSource };
  } catch {
    return { ...DEMO_SENTINEL_SUMMARY, source: "demo" };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Events (REST — initial load)
// ─────────────────────────────────────────────────────────────────────────────

export async function getSentinelEvents(
  filters: SentinelEventsFilters = {}
): Promise<{ events: DemoSensorEvent[]; source: DataSource }> {
  try {
    const params = new URLSearchParams({ limit: "200" });
    if (filters.priority && filters.priority !== "all") params.set("priority", filters.priority);
    if (filters.sensorType && filters.sensorType !== "all") params.set("sensor_type", filters.sensorType);
    if (filters.timeWindowHours) {
      const since = new Date(Date.now() - filters.timeWindowHours * 3600_000).toISOString();
      params.set("since", since);
    }
    const data = await fetchAPI(`/sentinel/events?${params}`);
    return { events: data.events ?? [], source: "live" };
  } catch {
    let events = [...DEMO_SENSOR_EVENTS];
    if (filters.priority && filters.priority !== "all") {
      events = events.filter((e) => e.priority === filters.priority);
    }
    if (filters.sensorType && filters.sensorType !== "all") {
      events = events.filter((e) => e.sensor_type === filters.sensorType);
    }
    if (filters.timeWindowHours) {
      const cutoff = Date.now() - filters.timeWindowHours * 3600_000;
      events = events.filter((e) => new Date(e.timestamp).getTime() >= cutoff);
    }
    return { events, source: "demo" };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// WebSocket — real-time stream with auto-reconnect
// ─────────────────────────────────────────────────────────────────────────────

const WS_BASE = API_BASE.replace(/^http/, "ws").replace("/api/v1", "");

export interface SentinelWsHandle {
  close: () => void;
}

export function createSentinelWebSocket(
  onEvent: (event: DemoSensorEvent) => void,
  onStatusChange?: (status: "connected" | "reconnecting" | "failed") => void
): SentinelWsHandle {
  let ws: WebSocket | null = null;
  let retries = 0;
  let closed = false;
  let pingInterval: ReturnType<typeof setInterval> | null = null;

  function clearPing() {
    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }
  }

  function connect() {
    if (closed) return;

    const url = `${WS_BASE}/ws/sentinel-grid`;
    try {
      ws = new WebSocket(url);
    } catch {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      retries = 0;
      onStatusChange?.("connected");
      // Keep-alive ping every 25 s
      pingInterval = setInterval(() => {
        try { ws?.send("ping"); } catch { /* ignore */ }
      }, 25_000);
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "sensor_event" && msg.data) {
          onEvent(msg.data as DemoSensorEvent);
        }
      } catch { /* ignore bad frames */ }
    };

    ws.onerror = () => { /* handled in onclose */ };

    ws.onclose = () => {
      clearPing();
      if (!closed) {
        scheduleReconnect();
      }
    };
  }

  function scheduleReconnect() {
    if (closed) return;
    const maxRetries = 12;
    if (retries >= maxRetries) {
      onStatusChange?.("failed");
      return;
    }
    retries += 1;
    onStatusChange?.("reconnecting");
    const delay = Math.min(1000 * Math.pow(1.5, retries), 30_000);
    setTimeout(connect, delay);
  }

  connect();

  return {
    close() {
      closed = true;
      clearPing();
      ws?.close();
    },
  };
}
