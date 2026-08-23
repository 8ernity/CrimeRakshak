// Predictive Hotspots — TypeScript Interfaces
// Maps to future FastAPI prediction endpoints.

import type { RiskTier } from "@/lib/design-tokens";

/* ── Prediction Driver (feature importance, NOT labeled as SHAP unless backend confirms) ── */
export interface PredictionDriver {
  factor: string;
  contribution: number; // 0–1 normalized weight
  direction: "positive" | "negative";
}

/* ── Data Quality ── */
export interface DataQuality {
  historicalCoverage: number; // 0–100
  locationCompleteness: number;
  categoryCompleteness: number;
  dataFreshnessDays: number;
}

/* ── Temporal Point (for time-series chart) ── */
export interface TemporalPoint {
  timestamp: string;
  predictedRisk: number;
  historicalRisk: number;
  confidenceLower: number;
  confidenceUpper: number;
}

/* ── Core Ward Prediction ── */
export interface WardPrediction {
  wardId: string;           // e.g. "BLR-W17"
  wardName: string;         // e.g. "Ward 17 (Jayanagar)"
  district: string;         // e.g. "Bengaluru City"
  adminArea: string;        // e.g. "Jayanagar PS"
  lat: number;
  lng: number;
  crimeCategory: string;
  predictionHorizon: ForecastHorizon;
  riskScore: number;        // 0–100 (composite score)
  riskLevel: RiskTier;      // "Safe" | "Moderate" | "High" | "Critical"
  probability: number;      // 0–1 (estimated probability of incident)
  expectedIncidents: number; // model-estimated count
  confidence: number;       // 0–100 (model confidence, distinct from probability)
  riskChange: number;       // % change from baseline
  trend: "increasing" | "decreasing" | "stable";
  hotspotStatus: "persistent" | "emerging" | "declining" | "stable";
  peakWindow: string;       // e.g. "22:00–02:00"
  drivers: PredictionDriver[];
  dataQuality: DataQuality;
  temporalForecast: TemporalPoint[];

  // Model metadata (for auditability)
  modelName?: string;       // e.g. "XGBoost"
  modelVersion?: string;    // e.g. "v2.3"
  predictionGeneratedAt: string; // ISO timestamp of when prediction was generated
  baselinePeriod?: string;  // e.g. "previous_30_days"
  predictionAgeMinutes: number; // how stale is this prediction
}

/* ── Forecast Horizon ── */
export type ForecastHorizon = "6h" | "12h" | "24h" | "7d" | "30d";

export const FORECAST_HORIZONS: { id: ForecastHorizon; label: string }[] = [
  { id: "6h", label: "6 Hours" },
  { id: "12h", label: "12 Hours" },
  { id: "24h", label: "24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
];

/* ── Geographic Level ── */
export type GeoLevel = "ward" | "district";

export const GEO_LEVELS: { id: GeoLevel; label: string }[] = [
  { id: "ward", label: "Ward" },
  { id: "district", label: "District" },
];

/* ── View Mode ── */
export type ViewMode = "historical" | "predicted";

/* ── API Response Wrappers ── */
export interface PredictedWardsResponse {
  wards: WardPrediction[];
  generatedAt: string;
  modelName: string;
  modelVersion: string;
  source: "live" | "demo";
}

export interface HotspotsResponse {
  hotspots: WardPrediction[];
  emergingCount: number;
  persistentCount: number;
  decliningCount: number;
  source: "live" | "demo";
}

/* ── Filter State ── */
export interface PredictionFilters {
  crimeCategory: string;
  forecastHorizon: ForecastHorizon;
  geoLevel: GeoLevel;
  confidenceThreshold: number;
}
