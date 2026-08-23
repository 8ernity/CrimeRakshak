"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { HardDrive, Hash, Clock, FileVideo, Link2, CheckCircle2, Image } from "lucide-react";
import type { InvestigationMedia } from "./types";
import { linkFIR } from "@/lib/investigationApi";

interface MediaMetadataPanelProps {
  media: InvestigationMedia | null;
  onMediaUpdated?: (updated: InvestigationMedia) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MediaMetadataPanel({ media, onMediaUpdated }: MediaMetadataPanelProps) {
  const [firInput, setFirInput] = useState("");
  const [linkedFir, setLinkedFir] = useState<string | null>(media?.fir_id || null);
  const [isLinking, setIsLinking] = useState(false);

  const handleLinkFIR = async () => {
    if (!media || !firInput.trim()) return;
    setIsLinking(true);
    try {
      const updated = await linkFIR(media.media_id, firInput.trim());
      setLinkedFir(firInput.trim());
      setFirInput("");
      if (onMediaUpdated) onMediaUpdated(updated);
    } finally {
      setIsLinking(false);
    }
  };

  const handleUnlinkFIR = async () => {
    if (!media) return;
    setIsLinking(true);
    try {
      const updated = await linkFIR(media.media_id, null);
      setLinkedFir(null);
      if (onMediaUpdated) onMediaUpdated(updated);
    } finally {
      setIsLinking(false);
    }
  };

  if (!media) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-sm font-medium text-slate-400">Select media to view details.</span>
      </div>
    );
  }

  const isVideo = media.file_type === "video";

  return (
    <div className="flex flex-col h-full relative group">
      <div className="absolute -top-10 -left-10 w-40 h-40 bg-purple-500/10 blur-[50px] rounded-full pointer-events-none group-hover:bg-purple-500/20 transition-all duration-700" />

      <div className="flex items-center gap-3 mb-4 relative z-10">
        <div className="p-2 rounded-xl bg-purple-50 border border-purple-100/50 shadow-sm">
          <HardDrive className="w-4 h-4 text-purple-600" />
        </div>
        <div>
          <h3 className="font-bold text-slate-900 tracking-tight text-base leading-tight">Evidence Integrity</h3>
          <span className="text-[11px] font-medium text-slate-500">Chain of custody metadata</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-3 relative z-10 overflow-y-auto scrollbar-hide">
        {/* SHA256 Hash */}
        <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-slate-50/80 border border-slate-200/60 shadow-sm">
          <div className="flex items-center gap-1.5">
            <Hash className="w-3 h-3 text-slate-400" />
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">SHA256</span>
          </div>
          <code className="text-[10px] font-mono text-slate-700 break-all bg-white p-1.5 rounded-lg border border-slate-200/50 leading-tight">
            {media.sha256_hash}
          </code>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-2.5">
          <div className="flex flex-col gap-0.5 p-2.5 rounded-xl bg-white border border-slate-100 shadow-sm">
            <div className="flex items-center gap-1 mb-0.5">
              {isVideo ? <FileVideo className="w-3 h-3 text-indigo-400" /> : <Image className="w-3 h-3 text-cyan-400" />}
              <span className="text-[9px] font-bold text-slate-400 uppercase">{isVideo ? "Duration" : "Type"}</span>
            </div>
            <span className="text-sm font-black text-slate-800">
              {isVideo ? `${media.duration_seconds?.toFixed(0)}s` : "Static Image"}
            </span>
          </div>
          <div className="flex flex-col gap-0.5 p-2.5 rounded-xl bg-white border border-slate-100 shadow-sm">
            <div className="flex items-center gap-1 mb-0.5">
              <Clock className="w-3 h-3 text-emerald-400" />
              <span className="text-[9px] font-bold text-slate-400 uppercase">Size</span>
            </div>
            <span className="text-sm font-black text-slate-800">{formatBytes(media.file_size_bytes)}</span>
          </div>
        </div>
        {isVideo && media.fps && (
          <div className="p-2.5 rounded-xl bg-white border border-slate-100 shadow-sm">
            <span className="text-[9px] font-bold text-slate-400 uppercase">Resolution</span>
            <span className="block text-sm font-black text-slate-800 mt-0.5">
              {media.total_frames} frames @ {media.fps}FPS
            </span>
          </div>
        )}

        {/* FIR Link */}
        <div className="mt-auto pt-1">
          {linkedFir || media.fir_id ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              className="w-full flex items-center justify-between p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-bold text-emerald-700">{linkedFir || media.fir_id}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-emerald-500/70 font-bold uppercase tracking-wider">Linked</span>
                <button
                  onClick={handleUnlinkFIR}
                  disabled={isLinking}
                  className="text-[10px] font-bold text-red-500 hover:text-red-700 underline transition-colors"
                >
                  Unlink
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="flex gap-2">
              <input
                type="text"
                value={firInput}
                onChange={(e) => setFirInput(e.target.value)}
                placeholder="FIR-2026-XXX"
                className="flex-1 px-3 py-2 rounded-xl bg-white border border-slate-200 text-sm text-slate-800 placeholder:text-slate-300 focus:border-blue-300 focus:ring-1 focus:ring-blue-200 outline-none transition-all"
              />
              <motion.button
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                onClick={handleLinkFIR}
                disabled={!firInput.trim() || isLinking}
                className="px-3 py-2 rounded-xl bg-slate-900 text-white font-bold text-sm shadow-sm hover:bg-slate-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
              >
                <Link2 className="w-3.5 h-3.5" />
                Link
              </motion.button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
