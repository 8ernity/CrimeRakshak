"use client";

import React, { useMemo } from "react";
import { motion } from "motion/react";
import { Crosshair, Eye, EyeOff } from "lucide-react";
import type { Detection } from "./types";

interface TrackInfo {
  trackingId: number;
  objectClass: string;
  firstSeen: number;
  lastSeen: number;
  detectionCount: number;
  avgConfidence: number;
}

interface TrackInspectorProps {
  detections: Detection[];
  highlightedTrackId: number | null;
  onHighlightTrack: (trackId: number | null) => void;
}

const CLASS_COLORS: Record<string, string> = {
  person: "bg-blue-500",
  car: "bg-amber-500",
  truck: "bg-amber-500",
  motorcycle: "bg-emerald-500",
  bicycle: "bg-emerald-500",
};

export function TrackInspector({
  detections,
  highlightedTrackId,
  onHighlightTrack,
}: TrackInspectorProps) {
  const tracks: TrackInfo[] = useMemo(() => {
    const map = new Map<number, TrackInfo>();

    for (const d of detections) {
      if (d.tracking_id === null) continue;
      const existing = map.get(d.tracking_id);
      if (existing) {
        existing.firstSeen = Math.min(existing.firstSeen, d.timestamp_seconds);
        existing.lastSeen = Math.max(existing.lastSeen, d.timestamp_seconds);
        existing.detectionCount++;
        existing.avgConfidence =
          (existing.avgConfidence * (existing.detectionCount - 1) + d.confidence) /
          existing.detectionCount;
      } else {
        map.set(d.tracking_id, {
          trackingId: d.tracking_id,
          objectClass: d.object_class,
          firstSeen: d.timestamp_seconds,
          lastSeen: d.timestamp_seconds,
          detectionCount: 1,
          avgConfidence: d.confidence,
        });
      }
    }

    return Array.from(map.values()).sort((a, b) => a.firstSeen - b.firstSeen);
  }, [detections]);

  const containerVariants = {
    initial: {},
    animate: { transition: { staggerChildren: 0.06 } },
  };
  const itemVariants = {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
  };

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      <div className="absolute bottom-0 left-0 w-40 h-40 bg-emerald-500/5 blur-[50px] rounded-full pointer-events-none" />

      <div className="px-5 pt-5 pb-3 relative z-10">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-slate-900 tracking-tight text-base">Tracked Subjects</h3>
          <span className="px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-100 text-[10px] font-bold text-emerald-600 uppercase tracking-wider">
            {tracks.length} Tracks
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-5 scrollbar-hide relative z-10">
        {tracks.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <span className="text-sm font-medium text-slate-400">No tracked subjects.</span>
          </div>
        ) : (
          <motion.div variants={containerVariants} initial="initial" animate="animate" className="flex flex-col gap-2.5">
            {tracks.map((track) => {
              const isActive = highlightedTrackId === track.trackingId;
              const dotColor = CLASS_COLORS[track.objectClass] || "bg-purple-500";

              return (
                <motion.div
                  key={track.trackingId}
                  variants={itemVariants}
                  whileHover={{ x: 3 }}
                  onClick={() => onHighlightTrack(isActive ? null : track.trackingId)}
                  className={`flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${
                    isActive
                      ? "bg-red-50 border-red-200 shadow-md shadow-red-100/50"
                      : "bg-white border-slate-100 hover:border-slate-200 shadow-sm hover:shadow-md"
                  }`}
                >
                  {/* Class indicator dot */}
                  <div className={`w-3 h-3 rounded-full flex-shrink-0 ${dotColor}`} />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-sm font-bold text-slate-800">
                        Track #{track.trackingId}
                      </span>
                      {isActive ? (
                        <EyeOff className="w-3.5 h-3.5 text-red-400" />
                      ) : (
                        <Eye className="w-3.5 h-3.5 text-slate-300" />
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500">
                      <span className="capitalize font-semibold">{track.objectClass}</span>
                      <span>·</span>
                      <span className="tabular-nums">{track.firstSeen.toFixed(1)}s – {track.lastSeen.toFixed(1)}s</span>
                      <span>·</span>
                      <span className="tabular-nums">{(track.avgConfidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>
    </div>
  );
}
