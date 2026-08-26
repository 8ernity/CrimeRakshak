"use client";

import React, { useRef, useCallback, useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Upload, Camera, Settings, Activity, Loader2, Wifi, WifiOff,
  Video, Zap, Shield, Crosshair, Sparkles, RefreshCw, AlertTriangle, FileText, Link2, Clock, Target
} from "lucide-react";
import { VideoCanvasSync } from "./VideoCanvasSync";
import { InteractiveTimeline } from "./InteractiveTimeline";
import { TrackInspector } from "./TrackInspector";
import { EntityStatsChart } from "./EntityStatsChart";
import { MediaMetadataPanel } from "./MediaMetadataPanel";
import { MediaLibraryStrip } from "./MediaLibraryStrip";
import { UploadEvidenceModal } from "./UploadEvidenceModal";
import { ConfigureModal } from "./ConfigureModal";
import { CrimeDetectionPanel } from "./CrimeDetectionPanel";
import type { InvestigationMedia, Detection, InvestigationEvent, AnalysisJob, InvestigationSummary, CrimeVideoDetection } from "./types";
import {
  listMedia, getDetections, getEvents, isBackendLive, triggerAnalysis, getSummary,
  getMediaUrl, DEMO_VIDEO_SRC, getJobStatus, getCrimeDetection,
} from "@/lib/investigationApi";

/* ═══════════════════════════════════════════════════════════════
 * RIGHT PANEL TABS
 * ═══════════════════════════════════════════════════════════════ */
type RightTab = "detection" | "timeline" | "tracks" | "summary" | "details";

const TAB_CONFIG: { id: RightTab; label: string; icon: React.ElementType }[] = [
  { id: "detection", label: "Crime Evidence", icon: Shield },
  { id: "timeline", label: "Timeline", icon: Activity },
  { id: "tracks", label: "Tracks", icon: Crosshair },
  { id: "summary", label: "LLM Summary", icon: Sparkles },
  { id: "details", label: "Details", icon: Settings },
];


/* ═══════════════════════════════════════════════════════════════
 * MAIN PAGE COMPONENT
 * ═══════════════════════════════════════════════════════════════ */
export default function InvestigationAIPage() {
  const videoRef = useRef<HTMLVideoElement>(null);

  /* ── State ── */
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [mediaItems, setMediaItems] = useState<InvestigationMedia[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<InvestigationMedia | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [summaryData, setSummaryData] = useState<InvestigationSummary | null>(null);
  const [crimeDetection, setCrimeDetection] = useState<CrimeVideoDetection | null>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState<boolean>(false);
  const [activeJobs, setActiveJobs] = useState<(AnalysisJob & { fileName?: string })[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [highlightedTrackId, setHighlightedTrackId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<RightTab>("detection");

  const [backendLive, setBackendLive] = useState<boolean | null>(null);

  const [firFilter, setFirFilter] = useState<string>("");

  /* ── Backend Liveness Check ── */
  useEffect(() => {
    isBackendLive().then(setBackendLive);
  }, []);

  /* ── Load Media Library ── */
  const fetchMediaList = useCallback(async (filterFir?: string) => {
    const targetFir = filterFir !== undefined ? filterFir : firFilter;
    const res = await listMedia(targetFir.trim() || undefined);
    
    // Deduplicate items by media_id
    const seen = new Set<number>();
    const uniqueItems: InvestigationMedia[] = [];
    for (const item of res.items) {
      if (!seen.has(item.media_id)) {
        seen.add(item.media_id);
        uniqueItems.push(item);
      }
    }

    setMediaItems(uniqueItems);
    if (uniqueItems.length > 0) {
      if (!selectedMedia || !uniqueItems.find((m) => m.media_id === selectedMedia.media_id)) {
        setSelectedMedia(uniqueItems[0]);
      }
    } else {
      setSelectedMedia(null);
    }
  }, [firFilter, selectedMedia]);

  useEffect(() => {
    fetchMediaList();
  }, [fetchMediaList]);

  /* ── Load Detections, Events & Summary for Selected Media ── */
  const fetchSummary = useCallback(async (mediaId: number, forceRefresh = false) => {
    setIsGeneratingSummary(true);
    try {
      const data = await getSummary(mediaId, forceRefresh);
      setSummaryData(data);
    } catch {
      setSummaryData(null);
    } finally {
      setIsGeneratingSummary(false);
    }
  }, []);

  useEffect(() => {
    // Immediately clear stale state from previous media
    setDetections([]);
    setEvents([]);
    setSummaryData(null);
    setCrimeDetection(null);
    setHighlightedTrackId(null);

    if (!selectedMedia) return;

    let isCancelled = false;
    const mId = selectedMedia.media_id;

    getDetections(mId).then((res) => {
      if (!isCancelled && res.media_id === mId) {
        setDetections(res.detections || []);
      }
    });

    getEvents(mId).then((res) => {
      if (!isCancelled && res.media_id === mId) {
        setEvents(res.events || []);
      }
    });

    getCrimeDetection(mId).then((res) => {
      if (!isCancelled) {
        setCrimeDetection(res);
      }
    });


    setIsGeneratingSummary(true);
    getSummary(mId)
      .then((data) => {
        if (!isCancelled) setSummaryData(data);
      })
      .catch(() => {
        if (!isCancelled) setSummaryData(null);
      })
      .finally(() => {
        if (!isCancelled) setIsGeneratingSummary(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedMedia]);

  /* ── Jump To Timestamp Handler ── */
  const handleJumpToTimestamp = useCallback((sec: number) => {
    setCurrentTime(sec);
    if (videoRef.current) {
      videoRef.current.currentTime = sec;
    }
  }, []);

  /* ── Poll Active Jobs ── */
  useEffect(() => {
    const pendingJobs = activeJobs.filter(j => j.status === 'queued' || j.status === 'processing');
    if (pendingJobs.length === 0) return;

    const interval = setInterval(async () => {
      let changed = false;
      const updatedJobs = await Promise.all(
        activeJobs.map(async (job) => {
          if (job.status === 'queued' || job.status === 'processing') {
            try {
              const res = await getJobStatus(job.job_id);
              if (res.status !== job.status) {
                changed = true;
                // If it just completed, refresh data if it's the selected media
                if (res.status === 'completed' && selectedMedia && selectedMedia.media_id === res.media_id) {
                  getDetections(res.media_id).then(d => setDetections(d.detections || []));
                  getEvents(res.media_id).then(e => setEvents(e.events || []));
                  fetchSummary(res.media_id);
                }
                return { ...job, ...res, fileName: job.fileName };
              }
            } catch (e) {
              // ignore
            }
          }
          return job;
        })
      );
      if (changed) {
        setActiveJobs(updatedJobs);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeJobs, selectedMedia, fetchSummary]);

  /* ── Select Media Item ── */
  const handleSelectMedia = useCallback((media: InvestigationMedia) => {
    setSelectedMedia(media);
  }, []);

  /* ── Upload Complete Callback ── */
  const handleUploadComplete = useCallback(
    async (newMedia: InvestigationMedia) => {
      setDetections([]);
      setEvents([]);
      setSummaryData(null);
      setHighlightedTrackId(null);

      setMediaItems((prev) => {
        const filtered = prev.filter((m) => m.media_id !== newMedia.media_id);
        return [newMedia, ...filtered];
      });
      setSelectedMedia(newMedia);

      const job = await triggerAnalysis(newMedia.media_id);
      setActiveJobs((prev) => [
        { ...job, fileName: newMedia.file_name },
        ...prev,
      ]);

      const [detsRes, evtsRes] = await Promise.all([
        getDetections(newMedia.media_id),
        getEvents(newMedia.media_id),
      ]);
      setDetections(detsRes.detections || []);
      setEvents(evtsRes.events || []);
      fetchSummary(newMedia.media_id);
    },
    [fetchSummary]
  );

  /* ── Animation Variants ── */
  const stagger = { animate: { transition: { staggerChildren: 0.08 } } };
  const fadeUp = {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  };

  return (
    <div className="min-h-screen pb-16 font-sans antialiased text-slate-800 selection:bg-blue-500 selection:text-white">
      {/* Dynamic ambient backdrop light */}
      <div className="fixed top-0 left-0 right-0 h-[400px] bg-gradient-to-b from-blue-500/5 via-indigo-500/3 to-transparent pointer-events-none z-0" />

      <div className="max-w-[1700px] mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pt-4 relative z-10">

        {/* ═══════════════════════════════════════════════════════
         * SECTION 1: TOP HEADER BAR
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-2 border-b border-slate-200/60"
        >
          {/* Title & Badge */}
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-md shadow-blue-500/20">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                  AI Video & Image Investigation
                </h1>
                <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/60 text-[11px] font-bold tracking-wide uppercase">
                  YOLOv8 + ByteTrack
                </span>
              </div>
              <p className="text-xs font-medium text-slate-500 mt-0.5">
                Forensic multi-object tracking, automated event detection & chain of custody
              </p>
            </div>
          </div>

          {/* Controls & Connection Status */}
          <div className="flex items-center gap-2.5">
            {/* Liveness pill */}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[11px] font-semibold transition-all ${
                backendLive
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : backendLive === false
                  ? "bg-amber-50 text-amber-700 border-amber-200"
                  : "bg-slate-50 text-slate-500 border-slate-200"
              }`}
              title={
                backendLive
                  ? "Backend API Connected (PostgreSQL/SQLite)"
                  : "Offline Demo Mode Active"
              }
            >
              {backendLive ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>API Live</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-amber-500" />
                  <span>Demo Mode</span>
                </>
              )}
            </div>

            {/* Config Button */}
            <button
              onClick={() => setIsConfigModalOpen(true)}
              className="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:border-slate-300 shadow-2xs hover:shadow-xs transition-all duration-200"
              title="Configure Detection Thresholds"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Upload CTA */}
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:to-indigo-800 text-white font-bold text-xs tracking-wide shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Evidence</span>
            </button>
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 2: MEDIA LIBRARY STRIP & FIR FILTER
         * ═══════════════════════════════════════════════════════ */}
        <motion.div variants={fadeUp} initial="initial" animate="animate" className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white/80 p-3 rounded-2xl border border-slate-200/60 shadow-2xs backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                <Link2 className="w-3.5 h-3.5" />
              </div>
              <span>Filter Media by Case / FIR:</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={firFilter}
                onChange={(e) => {
                  setFirFilter(e.target.value);
                  fetchMediaList(e.target.value);
                }}
                placeholder="Search by FIR (e.g. FIR-2026-044)"
                className="px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-800 placeholder:text-slate-400 focus:bg-white focus:border-blue-400 outline-none transition-all w-full sm:w-64"
              />
              {firFilter && (
                <button
                  onClick={() => {
                    setFirFilter("");
                    fetchMediaList("");
                  }}
                  className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <MediaLibraryStrip
            mediaItems={mediaItems}
            selectedMedia={selectedMedia}
            onSelectMedia={handleSelectMedia}
            onOpenUploadModal={() => setIsUploadModalOpen(true)}
          />
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 3: MAIN WORKSPACE (2-COLUMN GRID)
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6"
        >
          {/* ── LEFT COLUMN: CANVAS PLAYER & METRICS (7 COLS) ── */}
          <motion.div variants={fadeUp} className="lg:col-span-7 space-y-4">
            <div className="glass-card p-2 sm:p-3 relative overflow-hidden">
              <VideoCanvasSync
                videoRef={videoRef}
                detections={detections}
                highlightedTrackId={highlightedTrackId}
                isImage={selectedMedia?.file_type === "image"}
                mediaSrc={getMediaUrl(selectedMedia)}
              />
            </div>
          </motion.div>

          {/* ── RIGHT COLUMN: INSPECTOR & TIMELINE TABS (5 COLS) ── */}
          <motion.div variants={fadeUp} className="lg:col-span-5 flex flex-col h-[520px]">
            <div className="glass-card flex flex-col h-full overflow-hidden">
              {/* Tab Header Bar */}
              <div className="flex border-b border-slate-200/60 bg-slate-50/50 p-1 rounded-t-2xl gap-1">
                {TAB_CONFIG.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold uppercase tracking-wider rounded-t-xl transition-all duration-300 ${
                        isActive
                          ? "bg-white text-slate-800 shadow-xs border-b-2 border-blue-500"
                          : "text-slate-400 hover:text-slate-600 hover:bg-white/50"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                <AnimatePresence mode="wait">
                  {activeTab === "detection" && (
                    <motion.div key="detection" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-4 overflow-y-auto">
                      <CrimeDetectionPanel
                        detection={crimeDetection}
                        onSeek={handleJumpToTimestamp}
                      />
                    </motion.div>
                  )}
                  {activeTab === "timeline" && (
                    <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                      <InteractiveTimeline events={events} onJumpToTimestamp={handleJumpToTimestamp} />
                    </motion.div>
                  )}
                  {activeTab === "tracks" && (
                    <motion.div key="tracks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                      <TrackInspector
                        detections={detections}
                        highlightedTrackId={highlightedTrackId}
                        onHighlightTrack={setHighlightedTrackId}
                      />
                    </motion.div>
                  )}
                  {activeTab === "summary" && (
                    <motion.div key="summary" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-4 overflow-y-auto space-y-4">
                      <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-purple-600" />
                          <span className="font-bold text-xs uppercase tracking-wider text-slate-800">
                            LLM Investigation Summary
                          </span>
                        </div>
                        {selectedMedia && (
                          <button
                            onClick={() => fetchSummary(selectedMedia.media_id, true)}
                            disabled={isGeneratingSummary}
                            className="px-2.5 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 font-semibold text-[11px] flex items-center gap-1 transition-colors"
                          >
                            <RefreshCw className={`w-3 h-3 ${isGeneratingSummary ? "animate-spin" : ""}`} />
                            Refresh
                          </button>
                        )}
                      </div>

                      {summaryData ? (
                        <div className="space-y-3 text-xs">
                          <div className="p-3 rounded-xl bg-purple-50/70 border border-purple-100 text-slate-800 font-medium leading-relaxed">
                            {summaryData.summary_text}
                          </div>

                          <div className="p-3 rounded-xl bg-white border border-slate-100 space-y-1.5 shadow-2xs">
                            <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400">Observed Events</div>
                            <ul className="space-y-1">
                              {summaryData.observed_events.map((ev, idx) => (
                                <li key={idx} className="flex items-start gap-1.5 text-slate-700">
                                  <span className="text-purple-600 font-bold">•</span>
                                  <span>{ev}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="p-3 rounded-xl bg-white border border-slate-100 space-y-1.5 shadow-2xs">
                            <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400">Relevant Timestamps</div>
                            <ul className="space-y-1 font-mono text-[11px]">
                              {summaryData.relevant_timestamps.map((ts, idx) => (
                                <li key={idx} className="flex items-start gap-1.5 text-amber-700">
                                  <span>⏱</span>
                                  <span>{ts}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="p-3 rounded-xl bg-white border border-slate-100 space-y-1.5 shadow-2xs">
                            <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400">Detected Objects</div>
                            <ul className="space-y-1 text-slate-700">
                              {summaryData.detected_objects_summary.map((obj, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-emerald-600 font-bold">🎯</span>
                                  <span>{obj}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="p-3 rounded-xl bg-white border border-slate-100 space-y-1.5 shadow-2xs">
                            <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400">Evidence References</div>
                            <ul className="space-y-1 text-slate-700">
                              {summaryData.evidence_references.map((ref, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-blue-600 font-bold">🔗</span>
                                  <span>{ref}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="p-3 rounded-xl bg-amber-50 border border-amber-200/60 space-y-1.5">
                            <div className="flex items-center gap-1 font-bold text-[10px] uppercase tracking-wider text-amber-700">
                              <AlertTriangle className="w-3 h-3 text-amber-600" />
                              Uncertainty & Non-Accusation Policy
                            </div>
                            <ul className="space-y-1 text-[11px] text-amber-900/80">
                              {summaryData.uncertainty_limitations.map((lim, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-amber-600 font-bold">•</span>
                                  <span>{lim}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-48 text-slate-400 text-xs font-medium">
                          No LLM summary available.
                        </div>
                      )}
                    </motion.div>
                  )}
                  {activeTab === "details" && (
                    <motion.div key="details" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-5">
                      <MediaMetadataPanel
                        media={selectedMedia}
                        onMediaUpdated={(updated) => {
                          setSelectedMedia(updated);
                          fetchMediaList();
                        }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 4: ANALYTICS ROW
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="grid grid-cols-1 md:grid-cols-3 gap-5 lg:gap-6"
        >
          {/* Entity Demographics */}
          <motion.div variants={fadeUp}>
            <div className="glass-card p-5 h-[300px]">
              <EntityStatsChart detections={detections} />
            </div>
          </motion.div>

          {/* Job Queue */}
          <motion.div variants={fadeUp}>
            <div className="glass-card p-5 h-[300px] flex flex-col relative group overflow-hidden">
              <div className="absolute top-8 right-8 w-32 h-32 bg-amber-500/8 blur-[40px] rounded-full pointer-events-none group-hover:bg-amber-500/15 transition-all duration-700" />

              <div className="flex items-center gap-3 mb-4 relative z-10">
                <div className="p-2 rounded-xl bg-amber-50 border border-amber-100/50 shadow-xs">
                  <Zap className="w-4 h-4 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 tracking-tight text-base leading-tight">Processing Queue</h3>
                  <span className="text-[11px] font-medium text-slate-500">{activeJobs.length} jobs</span>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto scrollbar-hide flex flex-col gap-2.5 relative z-10">
                {activeJobs.length === 0 ? (
                  <div className="flex-1 flex items-center justify-center">
                    <span className="text-sm font-medium text-slate-400">No active jobs.</span>
                  </div>
                ) : (
                  activeJobs.map((job, idx) => (
                    <div
                      key={`job-${job.job_id}-${idx}`}
                      className="flex flex-col gap-2 p-3 rounded-xl bg-white border border-slate-100 shadow-xs"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-[12px] font-bold text-slate-800 truncate pr-3">
                          {job.fileName || `Job #${job.job_id}`}
                        </span>
                        {job.status === "processing" || job.status === "queued" ? (
                          <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin flex-shrink-0" />
                        ) : job.status === "completed" ? (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-700 text-[9px] font-bold uppercase tracking-wider flex-shrink-0">Done</span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-600 text-[9px] font-bold uppercase tracking-wider flex-shrink-0">Failed</span>
                        )}
                      </div>
                      {(job.status === "processing" || job.status === "queued") && (
                        <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <motion.div
                            initial={{ width: "0%" }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 5, ease: "linear" }}
                            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-1.5 rounded-full"
                          />
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </motion.div>

          {/* Detection Stats Summary */}
          <motion.div variants={fadeUp}>
            <div className="glass-card p-5 h-[300px] flex flex-col relative group overflow-hidden">
              <div className="absolute bottom-0 left-0 w-40 h-40 bg-cyan-500/8 blur-[50px] rounded-full pointer-events-none group-hover:bg-cyan-500/15 transition-all duration-700" />

              <div className="flex items-center gap-3 mb-4 relative z-10">
                <div className="p-2 rounded-xl bg-cyan-50 border border-cyan-100/50 shadow-xs">
                  <Crosshair className="w-4 h-4 text-cyan-600" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 tracking-tight text-base leading-tight">Detection Summary</h3>
                  <span className="text-[11px] font-medium text-slate-500">Confidence distribution</span>
                </div>
              </div>

              <div className="flex-1 flex flex-col justify-center gap-4 relative z-10">
                {/* Total detections */}
                <div className="flex items-end gap-2">
                  <span className="text-4xl font-black text-slate-900 tabular-nums leading-none">{detections.length}</span>
                  <span className="text-sm font-semibold text-slate-400 pb-0.5">total detections</span>
                </div>

                {/* Confidence breakdown */}
                <div className="flex flex-col gap-2">
                  {[
                    { label: "High (>90%)", count: detections.filter((d) => d.confidence > 0.9).length, color: "bg-emerald-500" },
                    { label: "Medium (70–90%)", count: detections.filter((d) => d.confidence > 0.7 && d.confidence <= 0.9).length, color: "bg-blue-500" },
                    { label: "Low (<70%)", count: detections.filter((d) => d.confidence <= 0.7).length, color: "bg-amber-500" },
                  ].map((tier) => (
                    <div key={tier.label} className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${tier.color}`} />
                      <span className="text-[12px] font-semibold text-slate-600 flex-1">{tier.label}</span>
                      <span className="text-[12px] font-black text-slate-800 tabular-nums">{tier.count}</span>
                    </div>
                  ))}
                </div>

                {/* Average confidence bar */}
                {detections.length > 0 && (
                  <div className="mt-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Avg. Confidence</span>
                      <span className="text-[12px] font-black text-slate-800 tabular-nums">
                        {(detections.reduce((s, d) => s + d.confidence, 0) / detections.length * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-emerald-500 h-2 rounded-full transition-all duration-700"
                        style={{ width: `${(detections.reduce((s, d) => s + d.confidence, 0) / detections.length * 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 5: AUDIT FOOTER
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-between gap-3 py-4 border-t border-slate-200/30 relative z-10"
        >
          <div className="flex items-center gap-4 text-[11px] font-medium text-slate-400">
            <span>Chain of Custody • Immutable Audit Log</span>
            {selectedMedia && (
              <>
                <span className="text-slate-300">|</span>
                <span>Uploaded: {new Date(selectedMedia.upload_timestamp).toLocaleString("en-IN")}</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <Shield className="w-3 h-3" />
            RBAC-Scoped • District-Isolated Evidence
          </div>
        </motion.div>

      </div>

      {/* ── Modals ── */}
      <UploadEvidenceModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadComplete={handleUploadComplete}
      />
      <ConfigureModal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
      />
    </div>
  );
}
