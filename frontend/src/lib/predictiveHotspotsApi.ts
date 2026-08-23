// Predictive Hotspots — API Service Layer
// Uses the project's existing fetchAPI() pattern.
// NEVER silently falls back to mock data. Always reports source as "live" or "demo".

import { fetchAPI } from "@/lib/apiClient";
import { DEMO_WARD_PREDICTIONS } from "@/data/wardPredictions";
import type {
  PredictedWardsResponse,
  HotspotsResponse,
  WardPrediction,
  PredictionFilters,
} from "@/app/(dashboard)/predictive-hotspots/types";

/* ═══════════════════════════════════════════════════════════════
 * BACKEND STATUS
 * ═══════════════════════════════════════════════════════════════ */

type DataSource = "live" | "demo";

/**
 * Check if the prediction backend is reachable.
 * This is NOT a page-level state indicator — it drives whether
 * we show "Demo Data" or "Live" on the page.
 */
async function probeBackend(): Promise<boolean> {
  try {
    await fetchAPI("/predictions/categories");
    return true;
  } catch {
    return false;
  }
}

/* ═══════════════════════════════════════════════════════════════
 * WARD PREDICTIONS
 * ═══════════════════════════════════════════════════════════════ */

function filterDemoWards(filters: PredictionFilters): WardPrediction[] {
  let wards = [...DEMO_WARD_PREDICTIONS];

  if (filters.crimeCategory !== "all") {
    // In demo mode, all wards have category "all" — return all
    // When live, the backend filters by category
  }

  if (filters.confidenceThreshold > 0) {
    wards = wards.filter((w) => w.confidence >= filters.confidenceThreshold);
  }

  // Update prediction horizon label on demo data
  wards = wards.map((w) => ({ ...w, predictionHorizon: filters.forecastHorizon }));

  return wards.sort((a, b) => b.riskScore - a.riskScore);
}

export async function getPredictedWards(
  filters: PredictionFilters
): Promise<PredictedWardsResponse> {
  try {
    const params = new URLSearchParams({
      category: filters.crimeCategory,
      horizon: filters.forecastHorizon,
      level: filters.geoLevel,
      min_confidence: String(filters.confidenceThreshold),
    });
    const data = await fetchAPI(`/predictions/wards?${params}`);
    return { ...data, source: "live" as DataSource };
  } catch {
    // Backend unavailable — return DEMO data with explicit source label
    return {
      wards: filterDemoWards(filters),
      generatedAt: new Date().toISOString(),
      modelName: "XGBoost (Demo)",
      modelVersion: "v2.3-demo",
      source: "demo",
    };
  }
}

/* ═══════════════════════════════════════════════════════════════
 * HOTSPOTS (EMERGING / PERSISTENT / DECLINING)
 * ═══════════════════════════════════════════════════════════════ */

export async function getHotspots(
  filters: PredictionFilters
): Promise<HotspotsResponse> {
  try {
    const params = new URLSearchParams({
      category: filters.crimeCategory,
      horizon: filters.forecastHorizon,
      min_risk: "60",
    });
    const data = await fetchAPI(`/predictions/hotspots?${params}`);
    return { ...data, source: "live" as DataSource };
  } catch {
    const allWards = filterDemoWards(filters);
    const hotspots = allWards.filter((w) => w.riskScore >= 60);
    return {
      hotspots,
      emergingCount: hotspots.filter((w) => w.hotspotStatus === "emerging").length,
      persistentCount: hotspots.filter((w) => w.hotspotStatus === "persistent").length,
      decliningCount: hotspots.filter((w) => w.hotspotStatus === "declining").length,
      source: "demo",
    };
  }
}

/* ═══════════════════════════════════════════════════════════════
 * WARD DETAIL
 * ═══════════════════════════════════════════════════════════════ */

export async function getWardDetail(wardId: string): Promise<{
  ward: WardPrediction | null;
  source: DataSource;
}> {
  try {
    const data = await fetchAPI(`/predictions/wards/${wardId}`);
    return { ward: data, source: "live" };
  } catch {
    const ward = DEMO_WARD_PREDICTIONS.find((w) => w.wardId === wardId) ?? null;
    return { ward, source: "demo" };
  }
}

/* ═══════════════════════════════════════════════════════════════
 * WARD EXPLANATION (Feature Importance)
 * ═══════════════════════════════════════════════════════════════ */

export async function getWardExplanation(wardId: string): Promise<{
  drivers: WardPrediction["drivers"];
  source: DataSource;
}> {
  try {
    const data = await fetchAPI(`/predictions/wards/${wardId}/explanation`);
    return { drivers: data.drivers, source: "live" };
  } catch {
    const ward = DEMO_WARD_PREDICTIONS.find((w) => w.wardId === wardId);
    return {
      drivers: ward?.drivers ?? [],
      source: "demo",
    };
  }
}

/* ═══════════════════════════════════════════════════════════════
 * CRIME CATEGORIES (from backend or fallback)
 * ═══════════════════════════════════════════════════════════════ */

export async function fetchCrimeCategories(): Promise<{
  categories: { id: string; label: string }[];
  source: DataSource;
}> {
  try {
    const data = await fetchAPI("/predictions/categories");
    return { categories: data, source: "live" };
  } catch {
    // Fall back to static list
    const { CRIME_CATEGORIES } = await import("@/data/crimeCategories");
    return {
      categories: CRIME_CATEGORIES.map((c) => ({ id: c.id, label: c.label })),
      source: "demo",
    };
  }
}
