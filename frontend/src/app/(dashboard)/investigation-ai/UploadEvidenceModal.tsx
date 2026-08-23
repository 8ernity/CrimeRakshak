"use client";

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, UploadCloud, FileVideo, Image, CheckCircle } from "lucide-react";
import { uploadMedia } from "@/lib/investigationApi";
import type { InvestigationMedia } from "./types";

interface UploadEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: (media: InvestigationMedia) => void;
}

export function UploadEvidenceModal({ isOpen, onClose, onUploadComplete }: UploadEvidenceModalProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [firId, setFirId] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate progress while uploading
    const interval = setInterval(() => {
      setUploadProgress((prev) => Math.min(prev + 15, 90));
    }, 300);

    try {
      const media = await uploadMedia(selectedFile, undefined, firId.trim() || undefined);
      setUploadProgress(100);
      clearInterval(interval);

      setTimeout(() => {
        onUploadComplete(media);
        resetState();
        onClose();
      }, 500);
    } catch {
      clearInterval(interval);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const resetState = () => {
    setSelectedFile(null);
    setFirId("");
    setIsUploading(false);
    setUploadProgress(0);
  };

  const isVideo = selectedFile?.type.startsWith("video");
  const isImage = selectedFile?.type.startsWith("image");

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={!isUploading ? onClose : undefined}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10 w-full max-w-lg bg-white/95 backdrop-blur-xl rounded-3xl border border-white/40 shadow-[0_24px_80px_rgba(0,0,0,0.12)] p-6 overflow-hidden"
          >
            {/* Ambient glow */}
            <div className="absolute -top-20 -right-20 w-60 h-60 bg-blue-500/10 blur-[60px] rounded-full pointer-events-none" />

            {/* Close button */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                if (!isUploading) onClose();
              }}
              className="absolute top-4 right-4 z-30 p-2.5 rounded-full hover:bg-slate-100 active:scale-95 transition-all text-slate-400 hover:text-slate-700 cursor-pointer"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-1 relative z-10">Upload Evidence</h3>
            <p className="text-sm font-medium text-slate-500 mb-5 relative z-10">
              Supported: MP4, AVI, JPEG, PNG — max 200 MB.
            </p>

            {/* Drop Zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById("evidence-file-input")?.click()}
              className={`relative w-full h-44 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${
                isDragging
                  ? "border-blue-400 bg-blue-50/50 scale-[1.01]"
                  : selectedFile
                    ? "border-emerald-300 bg-emerald-50/30"
                    : "border-slate-300 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-400"
              }`}
            >
              <input
                id="evidence-file-input"
                type="file"
                accept="video/*,image/*"
                onChange={handleFileInput}
                className="hidden"
              />

              {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 rounded-full bg-emerald-100 text-emerald-600">
                    <CheckCircle className="w-7 h-7" />
                  </div>
                  <span className="text-sm font-bold text-slate-800 max-w-[300px] truncate">{selectedFile.name}</span>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                    {isVideo && <FileVideo className="w-3 h-3" />}
                    {isImage && <Image className="w-3 h-3" />}
                    <span>{(selectedFile.size / (1024 * 1024)).toFixed(1)} MB</span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="p-4 rounded-full bg-white shadow-sm text-blue-500 border border-blue-100/50">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-sm font-bold text-slate-700">Drag & drop evidence</span>
                    <span className="text-[11px] text-slate-400 mt-0.5">or click to browse files</span>
                  </div>
                </>
              )}
            </div>

            {/* FIR / Case Link Input */}
            <div className="mt-3">
              <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                Link Case / FIR Number (Optional)
              </label>
              <input
                type="text"
                value={firId}
                onChange={(e) => setFirId(e.target.value)}
                placeholder="e.g. FIR-2026-044"
                disabled={isUploading}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-800 placeholder:text-slate-400 focus:bg-white focus:border-blue-400 focus:ring-1 focus:ring-blue-300 outline-none transition-all"
              />
            </div>

            {/* Progress bar */}
            {isUploading && (
              <div className="mt-4 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: "0%" }}
                  animate={{ width: `${uploadProgress}%` }}
                  className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full"
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}

            {/* Actions */}
            <div className="mt-5 flex justify-end gap-3 relative z-10">
              <button
                onClick={() => { resetState(); onClose(); }}
                disabled={isUploading}
                className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-40"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: 1.03, y: -1 }} whileTap={{ scale: 0.97 }}
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="px-5 py-2.5 rounded-xl bg-slate-900 text-white font-bold shadow-lg hover:bg-slate-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 relative overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-white/15 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                {isUploading ? (
                  <>
                    <span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
                    Uploading…
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    Start Analysis
                  </>
                )}
              </motion.button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
