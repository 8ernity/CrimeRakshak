"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { motion, type Variants } from "motion/react";
import { Antenna, ChevronRight, Radio, AlertTriangle, Wifi } from "lucide-react";
import { useLanguage } from "@/components/LanguageContext";
import {
  getSentinelSummary,
  getSentinelEvents,
  createSentinelWebSocket,
  type SentinelSummary,
  type SensorEvent,
  type SentinelEventsFilters,
} from "@/lib/sentinelApi";
import {
  SentinelKPIRow,
  SentinelMap,
  AlertFeedPanel,
  SentinelFilters,
  type SensorTypeFilter,
  type PriorityFilter,
  type TimeWindowHours,
} from "./_components";

export default function SentinelGridPage() {
  const { t } = useLanguage();

  /* ── Filter state ─────────────────────────────────────────────────── */
  const [sensorType, setSensorType] = useState<SensorTypeFilter>("all");
  const [priority, setPriority] = useState<PriorityFilter>("all");
  const [timeWindow, setTimeWindow] = useState<TimeWindowHours>(24);

  /* ── Data state ───────────────────────────────────────────────────── */
  const [events, setEvents] = useState<SensorEvent[]>([]);
  const [summary, setSummary] = useState<SentinelSummary | null>(null);
  const [dataSource, setDataSource] = useState<"live" | "demo">("demo");
  const [wsStatus, setWsStatus] = useState<"connected" | "reconnecting" | "failed" | "idle">("idle");
  const [isLoading, setIsLoading] = useState(true);

  const wsHandleRef = useRef<{ close: () => void } | null>(null);

  /* ── Initial data fetch ───────────────────────────────────────────── */
  const fetchInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters: SentinelEventsFilters = {
        timeWindowHours: timeWindow,
        priority: priority === "all" ? undefined : priority,
        sensorType: sensorType === "all" ? undefined : sensorType,
      };
      const [evRes, sumRes] = await Promise.all([
        getSentinelEvents(filters),
        getSentinelSummary(),
      ]);
      setEvents(evRes.events);
      setDataSource(evRes.source);
      setSummary(sumRes);
    } finally {
      setIsLoading(false);
    }
  }, [sensorType, priority, timeWindow]);

  useEffect(() => { fetchInitialData(); }, [fetchInitialData]);

  /* ── WebSocket real-time stream ───────────────────────────────────── */
  useEffect(() => {
    const handle = createSentinelWebSocket(
      (newEvent) => {
        // Apply current filters client-side
        if (priority !== "all" && newEvent.priority !== priority) return;
        if (sensorType !== "all" && newEvent.sensor_type !== sensorType) return;
        const cutoff = Date.now() - timeWindow * 3600_000;
        if (new Date(newEvent.timestamp).getTime() < cutoff) return;

        setEvents((prev) => {
          // Prepend and cap at 200 events
          const next = [newEvent, ...prev].slice(0, 200);
          return next;
        });

        // Bump KPI counts
        setSummary((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            events_last_24h: prev.events_last_24h + 1,
            high_priority_active:
              newEvent.priority === "high"
                ? prev.high_priority_active + 1
                : prev.high_priority_active,
            cases_auto_linked:
              newEvent.linked_case_id
                ? prev.cases_auto_linked + 1
                : prev.cases_auto_linked,
          };
        });
      },
      (status) => setWsStatus(status)
    );
    wsHandleRef.current = handle;
    return () => handle.close();
  }, [sensorType, priority, timeWindow]);

  /* ── Filtered view (for map + feed) ──────────────────────────────── */
  const filteredEvents = useMemo(() => {
    let out = events;
    if (sensorType !== "all") out = out.filter((e) => e.sensor_type === sensorType);
    if (priority !== "all") out = out.filter((e) => e.priority === priority);
    return out;
  }, [events, sensorType, priority]);

  /* ── Derived KPI (single source of truth) ────────────────────────── */
  const derivedSummary = useMemo<SentinelSummary>(() => {
    const base = summary ?? { active_sensors: 0, events_last_24h: 0, high_priority_active: 0, cases_auto_linked: 0, source: "demo" as const };
    return {
      ...base,
      // Always show counts consistent with current filter
      events_last_24h: filteredEvents.length,
      high_priority_active: filteredEvents.filter((e) => e.priority === "high").length,
      cases_auto_linked: filteredEvents.filter((e) => e.linked_case_id !== null).length,
    };
  }, [summary, filteredEvents]);

  /* ── Animation variants ───────────────────────────────────────────── */
  const container: Variants = {
    initial: {},
    animate: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
  };
  const item: Variants = {
    initial: { opacity: 0, y: 28 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.7, ease: "easeOut" } },
  };

  return (
    <div className="relative p-4 md:p-6 lg:p-8 space-y-8 min-h-[100dvh] z-0">
      {/* Ambient glows */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-blue/5 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-red-500/5 blur-[100px] rounded-full pointer-events-none -z-10" />

      <motion.div
        variants={container}
        initial="initial"
        animate="animate"
        className="flex flex-col space-y-8 relative z-10"
      >
        {/* ── HEADER ─────────────────────────────────────────────────── */}
        <motion.div
          variants={item}
          className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2 border-b border-border/30"
        >
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest">
                {t("AI & Prediction")} <ChevronRight className="inline h-3 w-3 -mt-0.5 mx-0.5" /> Sentinel Grid
              </span>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <h1 className="text-3xl md:text-[2.5rem] font-heading font-bold italic tracking-tight leading-[1.05] hero-headline text-foreground flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-brand-blue/10 border border-brand-blue/20">
                  <Radio className="h-7 w-7 text-brand-blue" />
                </div>
                Sentinel Grid
              </h1>
              <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-brand-blue/10 text-brand-blue border border-brand-blue/20 flex items-center gap-1.5 shadow-sm">
                <Wifi className="h-3 w-3" /> Live Simulation
              </span>
            </div>
            <p className="text-muted-foreground mt-3 text-sm md:text-base max-w-xl leading-relaxed">
              Real-time IoT sensor fusion — CCTV, ANPR, SOS, and acoustic alerts cross-referenced against predictive hotspots
            </p>
          </div>

          {/* Status badges */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-wrap">
            {dataSource === "demo" && (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs shadow-xs">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span className="font-semibold">Demo Data</span>
                <span className="text-emerald-600/40 dark:text-emerald-400/40 text-[10px]">•</span>
                <span className="text-[11px] font-medium">Live service offline</span>
              </div>
            )}
            {dataSource === "live" && (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-blue/10 border border-brand-blue/20 text-brand-blue text-xs font-semibold shadow-xs">
                <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse" />
                Live Sensor Stream
              </div>
            )}
            {wsStatus === "reconnecting" && (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                Reconnecting…
              </div>
            )}
          </div>
        </motion.div>

        {/* ── FILTERS ────────────────────────────────────────────────── */}
        <motion.div variants={item}>
          <SentinelFilters
            sensorType={sensorType}
            priority={priority}
            timeWindow={timeWindow}
            onSensorTypeChange={setSensorType}
            onPriorityChange={setPriority}
            onTimeWindowChange={setTimeWindow}
          />
        </motion.div>

        {/* ── KPI STRIP ──────────────────────────────────────────────── */}
        <motion.div variants={item}>
          <SentinelKPIRow summary={derivedSummary} isLoading={isLoading} />
        </motion.div>

        {/* ── MAP + ALERT FEED ────────────────────────────────────────── */}
        <motion.div variants={item} className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8 pb-8">
          {/* Map — 2/3 width */}
          <div className="xl:col-span-2 glass-card overflow-hidden flex flex-col group/map">
            <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-sm font-heading font-bold uppercase tracking-wider flex items-center gap-2 text-foreground">
                <div className="p-1.5 rounded-lg bg-brand-blue/10 text-brand-blue">
                  <Antenna className="h-4 w-4" />
                </div>
                GIS Fusion Map
              </h2>
              <span className="px-2.5 py-1 rounded-full bg-muted/50 border border-border/50 text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
                {filteredEvents.length} events shown
              </span>
            </div>
            <div className="flex-1 relative z-0">
              <SentinelMap events={filteredEvents} isLoading={isLoading} />
            </div>
          </div>

          {/* Alert Feed — 1/3 width */}
          <div className="min-h-[480px] xl:min-h-0">
            <AlertFeedPanel events={filteredEvents} />
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
