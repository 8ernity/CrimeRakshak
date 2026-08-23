"use client";

import React from "react";
import { motion } from "motion/react";
import { FileVideo, Image, Clock, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import type { InvestigationMedia } from "./types";

interface MediaLibraryStripProps {
  mediaItems: InvestigationMedia[];
  selectedMediaId: number | null;
  onSelectMedia: (media: InvestigationMedia) => void;
  isLoading: boolean;
}

const STATUS_MAP: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  analyzed: { icon: CheckCircle2, color: "text-emerald-500", label: "Analyzed" },
  processing: { icon: Loader2, color: "text-blue-500", label: "Processing" },
  uploaded: { icon: Clock, color: "text-amber-500", label: "Pending" },
  pending: { icon: Clock, color: "text-amber-500", label: "Pending" },
  failed: { icon: AlertCircle, color: "text-red-500", label: "Failed" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function MediaLibraryStrip({
  mediaItems,
  selectedMediaId,
  onSelectMedia,
  isLoading,
}: MediaLibraryStripProps) {

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        <span className="ml-2 text-sm font-medium text-slate-400">Loading media library…</span>
      </div>
    );
  }

  if (mediaItems.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 border-2 border-dashed border-slate-200 rounded-2xl">
        <span className="text-sm font-medium text-slate-400">
          No media uploaded yet. Click "Upload Evidence" to get started.
        </span>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto scrollbar-hide -mx-1 px-1">
      <div className="flex gap-4 pb-2" style={{ minWidth: "max-content" }}>
        {mediaItems.map((item) => {
          const isSelected = selectedMediaId === item.media_id;
          const statusCfg = STATUS_MAP[item.status] || STATUS_MAP.uploaded;
          const StatusIcon = statusCfg.icon;
          const isVideo = item.file_type === "video";

          return (
            <motion.div
              key={item.media_id}
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onSelectMedia(item)}
              className={`flex-shrink-0 w-[220px] p-4 rounded-2xl border cursor-pointer transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] relative overflow-hidden group ${
                isSelected
                  ? "bg-white border-blue-300 shadow-lg shadow-blue-100/50 ring-2 ring-blue-200"
                  : "bg-white/80 border-slate-100 shadow-sm hover:shadow-md hover:border-slate-200"
              }`}
            >
              {/* Ambient glow on hover */}
              <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full blur-[30px] pointer-events-none transition-all duration-500 ${
                isSelected ? "bg-blue-500/15" : "bg-blue-500/0 group-hover:bg-blue-500/10"
              }`} />

              <div className="relative z-10">
                {/* File type badge */}
                <div className="flex items-center justify-between mb-3">
                  <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                    isVideo ? "bg-purple-50 text-purple-600 border border-purple-100" : "bg-cyan-50 text-cyan-600 border border-cyan-100"
                  }`}>
                    {isVideo ? <FileVideo className="w-3 h-3" /> : <Image className="w-3 h-3" />}
                    {item.file_type}
                  </div>
                  <div className={`flex items-center gap-1 ${statusCfg.color}`}>
                    <StatusIcon className={`w-3.5 h-3.5 ${item.status === "processing" ? "animate-spin" : ""}`} />
                  </div>
                </div>

                {/* Filename */}
                <p className="text-sm font-bold text-slate-800 truncate mb-1" title={item.file_name}>
                  {item.file_name}
                </p>

                {/* Metadata row */}
                <div className="flex items-center gap-2 text-[11px] text-slate-400 font-medium">
                  <span>{formatBytes(item.file_size_bytes)}</span>
                  {item.duration_seconds && (
                    <>
                      <span>·</span>
                      <span>{item.duration_seconds.toFixed(0)}s</span>
                    </>
                  )}
                  {item.fir_id && (
                    <>
                      <span>·</span>
                      <span className="text-emerald-500 font-bold">{item.fir_id}</span>
                    </>
                  )}
                </div>

                {/* Upload time */}
                <span className="block text-[10px] text-slate-300 mt-1.5 font-medium">
                  {formatDate(item.upload_timestamp)}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
