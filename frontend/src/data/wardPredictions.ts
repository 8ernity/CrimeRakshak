// Predictive Hotspots — Realistic Mock Ward Prediction Data
// Labeled as DEMO DATA. Never silently substitute for real predictions.

import type { WardPrediction } from "@/app/(dashboard)/predictive-hotspots/types";

const NOW = new Date().toISOString();

function minutesAgo(m: number): string {
  return new Date(Date.now() - m * 60000).toISOString();
}

function buildTemporalForecast(baseRisk: number): WardPrediction["temporalForecast"] {
  const points: WardPrediction["temporalForecast"] = [];
  for (let h = 0; h < 24; h++) {
    const hour = String(h).padStart(2, "0");
    // Simulate higher risk at night (20:00–03:00)
    const nightBoost = (h >= 20 || h <= 3) ? 15 + Math.random() * 10 : 0;
    const predicted = Math.min(100, Math.round(baseRisk * 0.6 + nightBoost + Math.random() * 20));
    const historical = Math.round(predicted * (0.7 + Math.random() * 0.3));
    points.push({
      timestamp: `${hour}:00`,
      predictedRisk: predicted,
      historicalRisk: historical,
      confidenceLower: Math.max(0, predicted - 12 - Math.round(Math.random() * 8)),
      confidenceUpper: Math.min(100, predicted + 12 + Math.round(Math.random() * 8)),
    });
  }
  return points;
}

function buildDrivers(seed: number): WardPrediction["drivers"] {
  const pool = [
    { factor: "Historical Crime Frequency", contribution: 0.32, direction: "positive" as const },
    { factor: "Recent Crime Increase", contribution: 0.24, direction: "positive" as const },
    { factor: "Time-of-Day Pattern", contribution: 0.18, direction: "positive" as const },
    { factor: "Weekly Pattern", contribution: 0.12, direction: "positive" as const },
    { factor: "Neighboring Ward Activity", contribution: 0.09, direction: "positive" as const },
    { factor: "Population Density", contribution: 0.07, direction: "positive" as const },
    { factor: "Festival/Event Effect", contribution: 0.05, direction: "positive" as const },
    { factor: "Seasonality", contribution: 0.04, direction: "negative" as const },
  ];
  // Shuffle slightly based on seed
  return pool.map((d) => ({
    ...d,
    contribution: Math.round((d.contribution + (seed % 5) * 0.01) * 100) / 100,
  })).sort((a, b) => b.contribution - a.contribution);
}

export const DEMO_WARD_PREDICTIONS: WardPrediction[] = [
  // ── Bengaluru City Wards ──
  {
    wardId: "BLR-W17", wardName: "Ward 17 (Jayanagar)", district: "Bengaluru City",
    adminArea: "Jayanagar PS", lat: 12.9250, lng: 77.5938,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 91, riskLevel: "Critical", probability: 0.87, expectedIncidents: 8.4,
    confidence: 89, riskChange: 27, trend: "increasing", hotspotStatus: "emerging",
    peakWindow: "22:00–02:00",
    drivers: buildDrivers(17), dataQuality: { historicalCoverage: 94, locationCompleteness: 87, categoryCompleteness: 91, dataFreshnessDays: 1 },
    temporalForecast: buildTemporalForecast(91),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(12), baselinePeriod: "previous_30_days", predictionAgeMinutes: 12,
  },
  {
    wardId: "BLR-W04", wardName: "Ward 04 (Majestic)", district: "Bengaluru City",
    adminArea: "Upparpet PS", lat: 12.9767, lng: 77.5713,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 88, riskLevel: "Critical", probability: 0.82, expectedIncidents: 7.2,
    confidence: 92, riskChange: 18, trend: "increasing", hotspotStatus: "persistent",
    peakWindow: "19:00–23:00",
    drivers: buildDrivers(4), dataQuality: { historicalCoverage: 97, locationCompleteness: 93, categoryCompleteness: 95, dataFreshnessDays: 0 },
    temporalForecast: buildTemporalForecast(88),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(8), baselinePeriod: "previous_30_days", predictionAgeMinutes: 8,
  },
  {
    wardId: "BLR-W22", wardName: "Ward 22 (KR Market)", district: "Bengaluru City",
    adminArea: "City Market PS", lat: 12.9634, lng: 77.5780,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 84, riskLevel: "High", probability: 0.76, expectedIncidents: 6.9,
    confidence: 86, riskChange: 12, trend: "increasing", hotspotStatus: "persistent",
    peakWindow: "16:00–20:00",
    drivers: buildDrivers(22), dataQuality: { historicalCoverage: 91, locationCompleteness: 82, categoryCompleteness: 88, dataFreshnessDays: 1 },
    temporalForecast: buildTemporalForecast(84),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(15), baselinePeriod: "previous_30_days", predictionAgeMinutes: 15,
  },
  {
    wardId: "BLR-W11", wardName: "Ward 11 (Koramangala)", district: "Bengaluru City",
    adminArea: "Koramangala PS", lat: 12.9352, lng: 77.6245,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 79, riskLevel: "High", probability: 0.71, expectedIncidents: 5.8,
    confidence: 91, riskChange: -3, trend: "stable", hotspotStatus: "declining",
    peakWindow: "23:00–03:00",
    drivers: buildDrivers(11), dataQuality: { historicalCoverage: 96, locationCompleteness: 94, categoryCompleteness: 93, dataFreshnessDays: 0 },
    temporalForecast: buildTemporalForecast(79),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(5), baselinePeriod: "previous_30_days", predictionAgeMinutes: 5,
  },
  {
    wardId: "BLR-W31", wardName: "Ward 31 (Whitefield)", district: "Bengaluru City",
    adminArea: "Whitefield PS", lat: 12.9698, lng: 77.7500,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 72, riskLevel: "High", probability: 0.64, expectedIncidents: 4.6,
    confidence: 84, riskChange: 8, trend: "increasing", hotspotStatus: "emerging",
    peakWindow: "20:00–00:00",
    drivers: buildDrivers(31), dataQuality: { historicalCoverage: 88, locationCompleteness: 79, categoryCompleteness: 85, dataFreshnessDays: 2 },
    temporalForecast: buildTemporalForecast(72),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(22), baselinePeriod: "previous_30_days", predictionAgeMinutes: 22,
  },
  {
    wardId: "BLR-W08", wardName: "Ward 08 (Indiranagar)", district: "Bengaluru City",
    adminArea: "HAL PS", lat: 12.9784, lng: 77.6408,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 67, riskLevel: "Moderate", probability: 0.58, expectedIncidents: 3.9,
    confidence: 88, riskChange: 5, trend: "stable", hotspotStatus: "stable",
    peakWindow: "21:00–01:00",
    drivers: buildDrivers(8), dataQuality: { historicalCoverage: 95, locationCompleteness: 91, categoryCompleteness: 90, dataFreshnessDays: 0 },
    temporalForecast: buildTemporalForecast(67),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(10), baselinePeriod: "previous_30_days", predictionAgeMinutes: 10,
  },
  {
    wardId: "BLR-W45", wardName: "Ward 45 (Yelahanka)", district: "Bengaluru City",
    adminArea: "Yelahanka PS", lat: 13.1005, lng: 77.5963,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 58, riskLevel: "Moderate", probability: 0.48, expectedIncidents: 3.1,
    confidence: 82, riskChange: -7, trend: "decreasing", hotspotStatus: "declining",
    peakWindow: "18:00–22:00",
    drivers: buildDrivers(45), dataQuality: { historicalCoverage: 84, locationCompleteness: 76, categoryCompleteness: 82, dataFreshnessDays: 3 },
    temporalForecast: buildTemporalForecast(58),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(30), baselinePeriod: "previous_30_days", predictionAgeMinutes: 30,
  },
  {
    wardId: "BLR-W52", wardName: "Ward 52 (JP Nagar)", district: "Bengaluru City",
    adminArea: "JP Nagar PS", lat: 12.9063, lng: 77.5857,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 44, riskLevel: "Moderate", probability: 0.36, expectedIncidents: 2.2,
    confidence: 85, riskChange: 2, trend: "stable", hotspotStatus: "stable",
    peakWindow: "20:00–00:00",
    drivers: buildDrivers(52), dataQuality: { historicalCoverage: 90, locationCompleteness: 88, categoryCompleteness: 87, dataFreshnessDays: 1 },
    temporalForecast: buildTemporalForecast(44),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(18), baselinePeriod: "previous_30_days", predictionAgeMinutes: 18,
  },
  // ── Mysuru City Wards ──
  {
    wardId: "MYS-W03", wardName: "Ward 03 (Devaraja Mohalla)", district: "Mysuru City",
    adminArea: "Devaraja PS", lat: 12.3051, lng: 76.6551,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 74, riskLevel: "High", probability: 0.66, expectedIncidents: 4.8,
    confidence: 83, riskChange: 14, trend: "increasing", hotspotStatus: "emerging",
    peakWindow: "19:00–23:00",
    drivers: buildDrivers(3), dataQuality: { historicalCoverage: 86, locationCompleteness: 78, categoryCompleteness: 84, dataFreshnessDays: 2 },
    temporalForecast: buildTemporalForecast(74),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(25), baselinePeriod: "previous_30_days", predictionAgeMinutes: 25,
  },
  {
    wardId: "MYS-W12", wardName: "Ward 12 (Nazarbad)", district: "Mysuru City",
    adminArea: "Nazarbad PS", lat: 12.3140, lng: 76.6356,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 62, riskLevel: "Moderate", probability: 0.52, expectedIncidents: 3.5,
    confidence: 80, riskChange: 6, trend: "stable", hotspotStatus: "stable",
    peakWindow: "17:00–21:00",
    drivers: buildDrivers(12), dataQuality: { historicalCoverage: 82, locationCompleteness: 74, categoryCompleteness: 80, dataFreshnessDays: 3 },
    temporalForecast: buildTemporalForecast(62),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(35), baselinePeriod: "previous_30_days", predictionAgeMinutes: 35,
  },
  // ── Hubli-Dharwad City Wards ──
  {
    wardId: "HDC-W07", wardName: "Ward 07 (Station Road)", district: "Hubli-Dharwad City",
    adminArea: "Hubli Old PS", lat: 15.3518, lng: 75.1385,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 69, riskLevel: "Moderate", probability: 0.60, expectedIncidents: 4.1,
    confidence: 78, riskChange: 9, trend: "increasing", hotspotStatus: "stable",
    peakWindow: "18:00–22:00",
    drivers: buildDrivers(7), dataQuality: { historicalCoverage: 79, locationCompleteness: 71, categoryCompleteness: 77, dataFreshnessDays: 2 },
    temporalForecast: buildTemporalForecast(69),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(40), baselinePeriod: "previous_30_days", predictionAgeMinutes: 40,
  },
  {
    wardId: "HDC-W15", wardName: "Ward 15 (Keshwapur)", district: "Hubli-Dharwad City",
    adminArea: "Keshwapur PS", lat: 15.3738, lng: 75.1056,
    crimeCategory: "all", predictionHorizon: "24h",
    riskScore: 35, riskLevel: "Safe", probability: 0.24, expectedIncidents: 1.4,
    confidence: 76, riskChange: -12, trend: "decreasing", hotspotStatus: "declining",
    peakWindow: "14:00–18:00",
    drivers: buildDrivers(15), dataQuality: { historicalCoverage: 75, locationCompleteness: 68, categoryCompleteness: 72, dataFreshnessDays: 4 },
    temporalForecast: buildTemporalForecast(35),
    modelName: "XGBoost", modelVersion: "v2.3", predictionGeneratedAt: minutesAgo(55), baselinePeriod: "previous_30_days", predictionAgeMinutes: 55,
  },
];
