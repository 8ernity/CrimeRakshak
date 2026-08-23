"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion, AnimatePresence, type Variants } from "motion/react";
import {
  Radar, ChevronRight, TrendingUp, TrendingDown,
  AlertTriangle, Shield, Crosshair, Clock, Download,
  Minus, Brain, Database, History, Sparkles,
} from "lucide-react";
import { brandColors, riskTierBg, riskTierColors, chartPalette, type RiskTier } from "@/lib/design-tokens";
import { useLanguage } from "@/components/LanguageContext";
import { getPredictedWards, getHotspots } from "@/lib/predictiveHotspotsApi";
import { CRIME_CATEGORIES } from "@/data/crimeCategories";
import {
  PredictionControlBar,
  PredictiveKPIRow,
  HotspotRankingTable,
  PredictiveHotspotMap,
  TemporalForecastChart,
  EmergingHotspotCards,
  DataQualityIndicator,
  WardDetailDrawer,
} from "./_components";
import type {
  WardPrediction, PredictionFilters,
  ForecastHorizon, GeoLevel, ViewMode,
  FORECAST_HORIZONS,
} from "./types";

export default function PredictiveHotspotsPage() {
  const { t } = useLanguage();

  /* ── UI State (local, not fetched) ── */
  const [filters, setFilters] = useState<PredictionFilters>({
    crimeCategory: "all",
    forecastHorizon: "24h",
    geoLevel: "ward",
    confidenceThreshold: 0,
  });
  const [viewMode, setViewMode] = useState<ViewMode>("predicted");
  const [selectedWardId, setSelectedWardId] = useState<string | null>(null);
  const [comparisonWardIds, setComparisonWardIds] = useState<string[]>([]);

  /* ── Remote Data (fetched via API layer) ── */
  const [predictions, setPredictions] = useState<WardPrediction[]>([]);
  const [dataSource, setDataSource] = useState<"live" | "demo">("demo");
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  /* ── Fetch predictions when filters change ── */
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getPredictedWards(filters);
      setPredictions(res.wards);
      setDataSource(res.source);
      setLastUpdated(res.generatedAt);
    } catch {
      setPredictions([]);
      setDataSource("demo");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Derived values ── */
  const highRiskWards = useMemo(() => predictions.filter((w) => w.riskScore >= 70), [predictions]);
  const emergingHotspots = useMemo(() => predictions.filter((w) => w.hotspotStatus === "emerging"), [predictions]);
  const totalExpectedIncidents = useMemo(() => predictions.reduce((s, w) => s + w.expectedIncidents, 0), [predictions]);
  const avgConfidence = useMemo(() => {
    if (predictions.length === 0) return 0;
    return Math.round(predictions.reduce((s, w) => s + w.confidence, 0) / predictions.length);
  }, [predictions]);

  const selectedWard = useMemo(() => predictions.find((w) => w.wardId === selectedWardId) ?? null, [predictions, selectedWardId]);

  /* ── Handlers ── */
  const handleFilterChange = (patch: Partial<PredictionFilters>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  };
  const handleSelectWard = (wardId: string) => {
    setSelectedWardId(wardId);
  };
  const handleCloseDrawer = () => setSelectedWardId(null);

  /* ── Horizon label for map header ── */
  const horizonLabel = useMemo(() => {
    const map: Record<ForecastHorizon, string> = {
      "6h": "Next 6 Hours", "12h": "Next 12 Hours", "24h": "Next 24 Hours",
      "7d": "Next 7 Days", "30d": "Next 30 Days",
    };
    return map[filters.forecastHorizon];
  }, [filters.forecastHorizon]);

  /* ── Staggered Animation Config ── */
  const containerVariants: Variants = {
    initial: {},
    animate: {
      transition: { staggerChildren: 0.1, delayChildren: 0.05 },
    },
  };

  const itemVariants: Variants = {
    initial: { opacity: 0, y: 30 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.8, ease: "easeOut" }
    },
  };

  return (
    <div className="relative p-4 md:p-6 lg:p-8 space-y-8 min-h-[100dvh] z-0">
      {/* Ambient glows behind the dashboard */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-purple/5 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-brand-blue/5 blur-[100px] rounded-full pointer-events-none -z-10" />

      <motion.div variants={containerVariants} initial="initial" animate="animate" className="flex flex-col space-y-8 relative z-10">
        
        {/* ── HEADER ── */}
        <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2 border-b border-border/30">
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest">
                {t("AI & Prediction")} <ChevronRight className="inline h-3 w-3 -mt-0.5 mx-0.5" /> {t("Predictive Hotspots")}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <h1 className="text-3xl md:text-[2.5rem] font-heading font-bold italic tracking-tight leading-[1.05] hero-headline text-foreground flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-brand-blue/10 border border-brand-blue/20">
                  <Radar className="h-7 w-7 text-brand-blue" />
                </div>
                {t("Predictive Hotspots")}
              </h1>
              <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-brand-purple/10 text-brand-purple border border-brand-purple/20 flex items-center gap-1.5 shadow-sm">
                <Brain className="h-3 w-3" /> ML Pipeline
              </span>
            </div>
            <p className="text-muted-foreground mt-3 text-sm md:text-base max-w-xl leading-relaxed">
              {t("Fine-grained spatial and temporal crime risk forecasting")}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 flex-wrap">
            {/* Data Source Indicator */}
            {dataSource === "demo" && (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs shadow-xs">
                <AlertTriangle className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span className="font-semibold tracking-tight">{t("Demo Data")}</span>
                <span className="text-emerald-600/40 dark:text-emerald-400/40 text-[10px]">•</span>
                <span className="text-[11px] text-emerald-600/80 dark:text-emerald-400/80 font-medium">{t("Live service offline")}</span>
              </div>
            )}
            {dataSource === "live" && (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-semibold shadow-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Live Engine</span>
              </div>
            )}

            {/* Clean Anti-Slop Segmented Control */}
            <div className="p-1 rounded-full bg-slate-200/60 dark:bg-slate-800/60 backdrop-blur-md border border-slate-300/40 dark:border-slate-700/50 flex items-center gap-1 shadow-inner">
              <button
                onClick={() => setViewMode("historical")}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                  viewMode === "historical"
                    ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm border border-slate-200/80 dark:border-slate-700/80"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                {t("Historical")}
              </button>

              <button
                onClick={() => setViewMode("predicted")}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                  viewMode === "predicted"
                    ? "bg-blue-600 text-white shadow-sm border border-blue-500/30"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Sparkles className="h-3.5 w-3.5" />
                {t("Predicted")}
              </button>
            </div>
          </div>
        </motion.div>

        {/* ── PREDICTION CONTROL BAR ── */}
        <motion.div variants={itemVariants}>
          <PredictionControlBar
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        </motion.div>

        {/* ── KPI ROW ── */}
        <motion.div variants={itemVariants}>
          <PredictiveKPIRow
            highRiskCount={highRiskWards.length}
            totalExpectedIncidents={totalExpectedIncidents}
            emergingCount={emergingHotspots.length}
            avgConfidence={avgConfidence}
            isLoading={isLoading}
          />
        </motion.div>

        {/* ── MAP + HOTSPOT RANKING ── */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8">
          <motion.div variants={itemVariants} className="xl:col-span-2">
            <div className="glass-card overflow-hidden h-full flex flex-col group/map">
              <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between relative z-10">
                <h2 className="text-sm font-heading font-bold uppercase tracking-wider flex items-center gap-2 text-foreground">
                  <div className="p-1.5 rounded-lg bg-brand-blue/10 text-brand-blue">
                    <Crosshair className="h-4 w-4" />
                  </div>
                  {t("Predicted Risk")} — <span className="text-brand-blue">{horizonLabel}</span>
                </h2>
                <span className="px-2.5 py-1 rounded-full bg-muted/50 border border-border/50 text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
                  {viewMode === "predicted" ? "Model-estimated" : "Observed incidents"}
                </span>
              </div>
              <div className="flex-1 relative z-0 p-1">
                <div className="rounded-b-2xl overflow-hidden h-full">
                  <PredictiveHotspotMap
                    predictions={predictions}
                    selectedWardId={selectedWardId}
                    onSelectWard={handleSelectWard}
                    viewMode={viewMode}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants}>
            <HotspotRankingTable
              predictions={predictions}
              selectedWardId={selectedWardId}
              onSelectWard={handleSelectWard}
              isLoading={isLoading}
            />
          </motion.div>
        </div>

        {/* ── TEMPORAL FORECAST ── */}
        <motion.div variants={itemVariants}>
          <TemporalForecastChart
            ward={selectedWard}
            allPredictions={predictions}
            viewMode={viewMode}
          />
        </motion.div>

        {/* ── EMERGING HOTSPOTS + DATA QUALITY ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 pb-8">
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <EmergingHotspotCards
              predictions={predictions}
              onSelectWard={handleSelectWard}
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <DataQualityIndicator predictions={predictions} />
          </motion.div>
        </div>
      </motion.div>

      {/* ── WARD DETAIL DRAWER ── */}
      <AnimatePresence>
        {selectedWard && (
          <WardDetailDrawer
            ward={selectedWard}
            dataSource={dataSource}
            onClose={handleCloseDrawer}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
