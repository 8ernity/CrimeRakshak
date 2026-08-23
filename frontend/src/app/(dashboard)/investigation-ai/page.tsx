"use client";

import React, { useRef, useCallback, useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Upload, Camera, Settings, Activity, Loader2, Wifi, WifiOff,
  Video, Zap, Shield, Crosshair,
} from "lucide-react";
import { VideoCanvasSync } from "./VideoCanvasSync";
import { InteractiveTimeline } from "./InteractiveTimeline";
import { TrackInspector } from "./TrackInspector";
import { EntityStatsChart } from "./EntityStatsChart";
import { MediaMetadataPanel } from "./MediaMetadataPanel";
import { MediaLibraryStrip } from "./MediaLibraryStrip";
import { UploadEvidenceModal } from "./UploadEvidenceModal";
import { ConfigureModal } from "./ConfigureModal";
import type { InvestigationMedia, Detection, InvestigationEvent, AnalysisJob } from "./types";
import {
  listMedia, getDetections, getEvents, isBackendLive, triggerAnalysis,
  DEMO_VIDEO_SRC,
} from "@/lib/investigationApi";

/* ═══════════════════════════════════════════════════════════════
 * RIGHT PANEL TABS
 * ═══════════════════════════════════════════════════════════════ */
type RightTab = "timeline" | "tracks" | "details";

const TAB_CONFIG: { id: RightTab; label: string; icon: React.ElementType }[] = [
  { id: "timeline", label: "Timeline", icon: Activity },
  { id: "tracks", label: "Tracks", icon: Crosshair },
  { id: "details", label: "Details", icon: Shield },
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
  const [highlightedTrackId, setHighlightedTrackId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<RightTab>("timeline");
  const [isMediaLoading, setIsMediaLoading] = useState(true);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [backendLive, setBackendLive] = useState<boolean | null>(null);
  const [activeJobs, setActiveJobs] = useState<(AnalysisJob & { fileName?: string })[]>([]);

  /* ── Initial Data Load ── */
  useEffect(() => {
    (async () => {
      const live = await isBackendLive();
      setBackendLive(live);

      const result = await listMedia();
      setMediaItems(result.items);
      setIsMediaLoading(false);

      // Auto-select first item
      if (result.items.length > 0) {
        handleSelectMedia(result.items[0]);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Media Selection ── */
  const handleSelectMedia = useCallback(async (media: InvestigationMedia) => {
    setSelectedMedia(media);
    setHighlightedTrackId(null);
    setIsAnalysisLoading(true);

    const [detsRes, evtsRes] = await Promise.all([
      getDetections(media.media_id),
      getEvents(media.media_id),
    ]);
    setDetections(detsRes.detections);
    setEvents(evtsRes.events);
    setIsAnalysisLoading(false);
  }, []);

  /* ── Timestamp Jump ── */
  const handleJumpToTimestamp = useCallback((timeSeconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeSeconds;
      videoRef.current.play().catch(() => {});
    }
  }, []);

  /* ── Upload Complete ── */
  const handleUploadComplete = useCallback((media: InvestigationMedia) => {
    setMediaItems((prev) => [media, ...prev]);
    handleSelectMedia(media);

    // Trigger analysis job
    (async () => {
      const job = await triggerAnalysis(media.media_id);
      setActiveJobs((prev) => [{ ...job, fileName: media.file_name }, ...prev]);

      // Simulate job completion
      setTimeout(async () => {
        setActiveJobs((prev) =>
          prev.map((j) =>
            j.job_id === job.job_id ? { ...j, status: "completed" as const, progress_pct: 100 } : j
          )
        );
        // Re-fetch detections after "analysis"
        const [detsRes, evtsRes] = await Promise.all([
          getDetections(media.media_id),
          getEvents(media.media_id),
        ]);
        setDetections(detsRes.detections);
        setEvents(evtsRes.events);
      }, 5000);
    })();
  }, [handleSelectMedia]);

  /* ── Media Source ── */
  const mediaSrc = selectedMedia
    ? backendLive
      ? `/api/v1/investigation/media/${selectedMedia.media_id}/file`
      : DEMO_VIDEO_SRC
    : undefined;

  const isImage = selectedMedia?.file_type === "image";

  /* ── Framer Motion Variants ── */
  const stagger = {
    initial: {},
    animate: { transition: { staggerChildren: 0.12, delayChildren: 0.05 } },
  };
  const fadeUp = {
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] } },
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* ── Background decorators ── */}
      <div className="absolute top-[-8%] right-[-4%] w-[600px] h-[600px] bg-blue-400/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-8%] left-[-4%] w-[500px] h-[500px] bg-purple-400/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] left-[50%] w-[400px] h-[400px] bg-emerald-400/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-[1600px] mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 lg:py-8 flex flex-col gap-6 lg:gap-8">

        {/* ═══════════════════════════════════════════════════════
         * SECTION 1: COMMAND HEADER
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 relative z-10"
        >
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl lg:text-[2.75rem] font-black text-slate-900 tracking-tight hero-headline not-italic">
                Investigation{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600">
                  AI Support
                </span>
              </h1>

              {/* Connection badge */}
              {backendLive !== null && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider border shadow-sm ${
                    backendLive
                      ? "bg-emerald-50 border-emerald-200 text-emerald-600"
                      : "bg-amber-50 border-amber-200 text-amber-600"
                  }`}
                >
                  {backendLive ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                  {backendLive ? "Live" : "Demo"}
                </motion.div>
              )}
            </div>
            <p className="text-slate-500 font-medium text-sm max-w-xl">
              Computer vision tracking, anomaly detection, and event extraction — powered by YOLOv8 & ByteTrack.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setIsConfigModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/80 border border-slate-200/60 shadow-sm backdrop-blur-md text-slate-600 font-semibold hover:bg-white hover:border-slate-300 transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]"
            >
              <Settings className="w-4 h-4" />
              Configure
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold shadow-[0_8px_24px_rgba(15,23,42,0.2)] hover:shadow-[0_12px_30px_rgba(15,23,42,0.3)] hover:bg-slate-800 transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-white/15 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
              <Upload className="w-4 h-4" />
              Upload Evidence
            </motion.button>
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 2: MEDIA LIBRARY STRIP
         * ═══════════════════════════════════════════════════════ */}
        <motion.div variants={fadeUp} initial="initial" animate="animate">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-slate-400" />
              <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Evidence Library</h2>
            </div>
            <span className="text-[11px] font-semibold text-slate-400">{mediaItems.length} items</span>
          </div>
          <MediaLibraryStrip
            mediaItems={mediaItems}
            selectedMediaId={selectedMedia?.media_id ?? null}
            onSelectMedia={handleSelectMedia}
            isLoading={isMediaLoading}
          />
        </motion.div>

        {/* ═══════════════════════════════════════════════════════
         * SECTION 3: ANALYSIS STAGE (Video + Right Panel)
         * ═══════════════════════════════════════════════════════ */}
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:gap-6"
        >
          {/* Left: Video/Image Canvas */}
          <motion.div variants={fadeUp} className="lg:col-span-2">
            <div className="glass-card w-full flex flex-col p-2 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/8 blur-[80px] rounded-full pointer-events-none group-hover:bg-blue-500/15 transition-all duration-700" />

              {/* Source Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200/30 mb-1 relative z-10">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-indigo-50 border border-indigo-100/60 shadow-sm">
                    <Camera className="w-3.5 h-3.5 text-indigo-600" />
                  </div>
                  <span className="font-bold text-slate-800 tracking-tight text-sm truncate max-w-[300px]">
                    {selectedMedia ? selectedMedia.file_name : "No media selected"}
                  </span>
                </div>
                <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-100/60 shadow-sm">
                  <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[9px] font-bold text-emerald-700 uppercase tracking-wider">
                    {isAnalysisLoading ? "Loading" : "Sync Active"}
                  </span>
                </div>
              </div>

              {/* Canvas Area */}
              <div className="w-full aspect-video relative rounded-xl overflow-hidden border border-slate-200/20 shadow-inner bg-slate-950">
                {selectedMedia && mediaSrc ? (
                  <VideoCanvasSync
                    videoRef={videoRef}
                    detections={detections}
                    highlightedTrackId={highlightedTrackId}
                    isImage={isImage}
                    mediaSrc={mediaSrc}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="text-sm font-medium text-slate-500">Select evidence from the library above.</span>
                  </div>
                )}

                {isAnalysisLoading && (
                  <div className="absolute inset-0 bg-slate-950/60 flex items-center justify-center z-20">
                    <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-white/90 backdrop-blur-md shadow-xl border border-white/40">
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      <span className="text-sm font-bold text-slate-800">Loading analysis data…</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Right: Tabbed Panel */}
          <motion.div variants={fadeUp} className="lg:col-span-1">
            <div className="glass-card w-full h-full flex flex-col overflow-hidden min-h-[400px] lg:min-h-0">
              {/* Tab bar */}
              <div className="flex border-b border-slate-200/30 px-2 pt-2 relative z-10">
                {TAB_CONFIG.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold uppercase tracking-wider rounded-t-xl transition-all duration-300 ${
                        isActive
                          ? "bg-white/60 text-slate-800 shadow-sm border-b-2 border-blue-500"
                          : "text-slate-400 hover:text-slate-600 hover:bg-white/30"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab content */}
              <div className="flex-1 overflow-hidden">
                <AnimatePresence mode="wait">
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
                  {activeTab === "details" && (
                    <motion.div key="details" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-5">
                      <MediaMetadataPanel media={selectedMedia} />
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
                <div className="p-2 rounded-xl bg-amber-50 border border-amber-100/50 shadow-sm">
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
                  activeJobs.map((job) => (
                    <div
                      key={job.job_id}
                      className="flex flex-col gap-2 p-3 rounded-xl bg-white border border-slate-100 shadow-sm"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-[12px] font-bold text-slate-800 truncate pr-3">
                          {job.fileName || `Job #${job.job_id}`}
                        </span>
                        {job.status === "processing" ? (
                          <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin flex-shrink-0" />
                        ) : job.status === "completed" ? (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-700 text-[9px] font-bold uppercase tracking-wider flex-shrink-0">Done</span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-600 text-[9px] font-bold uppercase tracking-wider flex-shrink-0">Failed</span>
                        )}
                      </div>
                      {job.status === "processing" && (
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
                <div className="p-2 rounded-xl bg-cyan-50 border border-cyan-100/50 shadow-sm">
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
