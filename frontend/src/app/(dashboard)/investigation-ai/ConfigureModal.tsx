"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Settings, Sliders, Cpu, ShieldCheck, Check } from "lucide-react";

interface ConfigureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ConfigureModal({ isOpen, onClose }: ConfigureModalProps) {
  const [tracker, setTracker] = useState<"bytetrack" | "botsort">("bytetrack");
  const [confidence, setConfidence] = useState(0.35);
  const [sampleRate, setSampleRate] = useState(2);
  const [aspectRatio, setAspectRatio] = useState(1.25);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 1000);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10 w-full max-w-lg bg-white/95 backdrop-blur-xl rounded-3xl border border-white/40 shadow-[0_24px_80px_rgba(0,0,0,0.12)] p-6 overflow-hidden"
          >
            {/* Ambient glow */}
            <div className="absolute -top-20 -right-20 w-60 h-60 bg-indigo-500/10 blur-[60px] rounded-full pointer-events-none" />

            {/* Close button */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              className="absolute top-4 right-4 z-30 p-2.5 rounded-full hover:bg-slate-100 active:scale-95 transition-all text-slate-400 hover:text-slate-700 cursor-pointer"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-1 relative z-10">
              <div className="p-2.5 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-sm">
                <Settings className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-900 tracking-tight">Vision Engine Settings</h3>
                <p className="text-xs font-medium text-slate-500">Configure YOLOv8 and tracking parameters</p>
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-5 relative z-10">
              {/* Tracker algorithm */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                  Multi-Object Tracking Algorithm
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setTracker("bytetrack")}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      tracker === "bytetrack"
                        ? "bg-indigo-50/80 border-indigo-300 ring-2 ring-indigo-200 text-indigo-950 font-bold"
                        : "bg-slate-50/50 border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                    }`}
                  >
                    <div className="text-sm font-bold">ByteTrack</div>
                    <div className="text-[11px] opacity-75">High-speed motion trajectory</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTracker("botsort")}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      tracker === "botsort"
                        ? "bg-indigo-50/80 border-indigo-300 ring-2 ring-indigo-200 text-indigo-950 font-bold"
                        : "bg-slate-50/50 border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                    }`}
                  >
                    <div className="text-sm font-bold">BoT-SORT</div>
                    <div className="text-[11px] opacity-75">Camera motion compensation</div>
                  </button>
                </div>
              </div>

              {/* Confidence Threshold */}
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5 text-indigo-500" />
                    Detection Confidence Threshold
                  </label>
                  <span className="text-xs font-extrabold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                    {(confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.95"
                  step="0.05"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>

              {/* Posture Anomaly Ratio */}
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                    Person-Down Aspect Ratio Threshold
                  </label>
                  <span className="text-xs font-extrabold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                    ≥ {aspectRatio.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="2.0"
                  step="0.05"
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(parseFloat(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 flex items-center justify-end gap-3 relative z-10">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors text-sm"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: 1.03, y: -1 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSave}
                className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold shadow-lg hover:bg-slate-800 transition-colors text-sm flex items-center gap-2"
              >
                {saved ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-400" />
                    Saved!
                  </>
                ) : (
                  "Save Parameters"
                )}
              </motion.button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
