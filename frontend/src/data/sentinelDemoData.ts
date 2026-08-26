// Sentinel Grid — static demo data (Bengaluru ward centroids only).
// Used as fallback when the backend WebSocket / REST endpoints are offline.

export type SensorTypeName = "cctv_alert" | "anpr_hit" | "sos_button" | "gunshot";
export type PriorityName = "high" | "normal";

export interface DemoSensorEvent {
  id: number;
  sensor_id: string;
  sensor_type: SensorTypeName;
  lat: number;
  lng: number;
  ward_id: string;
  ward_name: string;
  district: string;
  confidence: number;
  priority: PriorityName;
  metadata: Record<string, unknown>;
  linked_case_id: string | null;
  timestamp: string;
}

const now = Date.now();
const ago = (seconds: number) => new Date(now - seconds * 1000).toISOString();

export const DEMO_SENSOR_EVENTS: DemoSensorEvent[] = [
  {
    id: 1001, sensor_id: "CCTV-BLR-W17-04", sensor_type: "cctv_alert",
    lat: 12.9248, lng: 77.5940, ward_id: "BLR-W17", ward_name: "Jayanagar", district: "South",
    confidence: 0.93, priority: "high",
    metadata: { object_detected: "person", camera_model: "Hikvision DS-2CD" },
    linked_case_id: null, timestamp: ago(45),
  },
  {
    id: 1002, sensor_id: "ANPR-BLR-W04-02", sensor_type: "anpr_hit",
    lat: 12.9769, lng: 77.5711, ward_id: "BLR-W04", ward_name: "Majestic", district: "Central",
    confidence: 0.97, priority: "high",
    metadata: { plate_number: "KA01AB1234", vehicle_color: "white" },
    linked_case_id: "CASE-2024-00441", timestamp: ago(112),
  },
  {
    id: 1003, sensor_id: "SOS-BLR-W22-07", sensor_type: "sos_button",
    lat: 12.9636, lng: 77.5782, ward_id: "BLR-W22", ward_name: "KR Market", district: "Central",
    confidence: 0.99, priority: "high",
    metadata: { phone_number: "+91 98450 11111", activation_method: "button_press" },
    linked_case_id: null, timestamp: ago(230),
  },
  {
    id: 1004, sensor_id: "ACUS-BLR-W11-01", sensor_type: "gunshot",
    lat: 12.9354, lng: 77.6243, ward_id: "BLR-W11", ward_name: "Koramangala", district: "South",
    confidence: 0.82, priority: "high",
    metadata: { decibels: 132.4, bearing_degrees: 217 },
    linked_case_id: null, timestamp: ago(390),
  },
  {
    id: 1005, sensor_id: "CCTV-BLR-W08-09", sensor_type: "cctv_alert",
    lat: 12.9786, lng: 77.6410, ward_id: "BLR-W08", ward_name: "Indiranagar", district: "East",
    confidence: 0.78, priority: "normal",
    metadata: { object_detected: "vehicle", camera_model: "Axis P3245" },
    linked_case_id: null, timestamp: ago(520),
  },
  {
    id: 1006, sensor_id: "ANPR-BLR-W09-03", sensor_type: "anpr_hit",
    lat: 12.9749, lng: 77.6096, ward_id: "BLR-W09", ward_name: "MG Road", district: "Central",
    confidence: 0.91, priority: "normal",
    metadata: { plate_number: "KA03CD5678", vehicle_color: "silver" },
    linked_case_id: null, timestamp: ago(680),
  },
  {
    id: 1007, sensor_id: "CCTV-BLR-W60-05", sensor_type: "cctv_alert",
    lat: 12.8453, lng: 77.6641, ward_id: "BLR-W60", ward_name: "Electronic City", district: "South",
    confidence: 0.72, priority: "normal",
    metadata: { object_detected: "crowd", camera_model: "Dahua IPC-HFW" },
    linked_case_id: null, timestamp: ago(810),
  },
  {
    id: 1008, sensor_id: "CCTV-BLR-W02-11", sensor_type: "cctv_alert",
    lat: 13.0349, lng: 77.5987, ward_id: "BLR-W02", ward_name: "Hebbal", district: "North",
    confidence: 0.85, priority: "normal",
    metadata: { object_detected: "person", camera_model: "Hikvision DS-2CD" },
    linked_case_id: null, timestamp: ago(1100),
  },
  {
    id: 1009, sensor_id: "ANPR-BLR-W45-06", sensor_type: "anpr_hit",
    lat: 13.1007, lng: 77.5961, ward_id: "BLR-W45", ward_name: "Yelahanka", district: "North",
    confidence: 0.88, priority: "normal",
    metadata: { plate_number: "KA51EF7890", vehicle_color: "black" },
    linked_case_id: null, timestamp: ago(1350),
  },
  {
    id: 1010, sensor_id: "SOS-BLR-W55-02", sensor_type: "sos_button",
    lat: 12.9118, lng: 77.6471, ward_id: "BLR-W55", ward_name: "HSR Layout", district: "South",
    confidence: 0.99, priority: "high",
    metadata: { phone_number: "+91 80765 22222", activation_method: "shake_gesture" },
    linked_case_id: null, timestamp: ago(1680),
  },
];

export const DEMO_SENTINEL_SUMMARY = {
  active_sensors: 7,
  events_last_24h: DEMO_SENSOR_EVENTS.length,
  high_priority_active: DEMO_SENSOR_EVENTS.filter((e) => e.priority === "high").length,
  cases_auto_linked: DEMO_SENSOR_EVENTS.filter((e) => e.linked_case_id !== null).length,
};
