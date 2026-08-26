"use client";

import React from "react";
import { Shield, AlertTriangle, CheckCircle2, Clock, Activity, Zap, Eye } from "lucide-react";
import type { CrimeVideoDetection } from "./types";

interface CrimeDetectionPanelProps {
  detection: CrimeVideoDetection | null;
  onSeek?: (timeSeconds: number) => void;
}

export function CrimeDetectionPanel({ detection, onSeek }: CrimeDetectionPanelProps) {
  if (!detection) {
    return (
      <div className="flex flex-col items-center justify-center h-56 text-slate-400 text-xs font-medium space-y-2">
        <Shield className="w-8 h-8 text-slate-300 animate-pulse" />
        <p>Evaluating video crime detection layer...</p>
      </div>
    );
  }

  const isPossibleCrime = detection.classification === "possible_crime";
  const formattedConfidence = Math.round(detection.confidence * 100);

  return (
    <div className="space-y-4 text-xs font-sans">
      {/* ── Classification Banner ── */}
      <div
        className={`p-4 rounded-2xl border transition-all ${
          isPossibleCrime
            ? "bg-rose-50/90 border-rose-200 text-rose-950 dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-200"
            : "bg-emerald-50/90 border-emerald-200 text-emerald-950 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-200"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-sm">
            {isPossibleCrime ? (
              <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            )}
            <span>
              {isPossibleCrime ? "Possible Crime Evidence" : "No Clear Crime Evidence"}
            </span>
          </div>

          <span
            className={`px-3 py-1 rounded-full font-extrabold text-xs tracking-wide shadow-2xs ${
              isPossibleCrime
                ? "bg-rose-600 text-white"
                : "bg-emerald-600 text-white"
            }`}
          >
            {formattedConfidence}% Confidence
          </span>
        </div>

        <p className="mt-2 text-xs opacity-80 leading-relaxed font-medium">
          {isPossibleCrime
            ? "Automated rule evaluation identified potential investigative evidence. Requires law enforcement review."
            : "No structured violent posture, weapon, or conflict indicators observed in evaluated frames."}
        </p>
      </div>

      {/* ── Detected Crime Indicators ── */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-2 shadow-2xs">
        <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center justify-between">
          <span>Crime Indicators Detected</span>
          <span className="font-mono text-slate-500">{detection.crime_indicators.length} Active</span>
        </div>

        {detection.crime_indicators.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {detection.crime_indicators.map((indicator, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200/70 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800"
              >
                🚨 {indicator.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-xs italic py-1">No crime indicators flagged.</p>
        )}
      </div>

      {/* ── Relevant Timestamps Range ── */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-2 shadow-2xs">
        <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-blue-500" />
          <span>Relevant Timestamps</span>
        </div>

        {detection.relevant_timestamps.length > 0 ? (
          <div className="flex flex-wrap gap-2 pt-1">
            {detection.relevant_timestamps.map((range, idx) => (
              <button
                key={idx}
                onClick={() => onSeek && onSeek(range.start)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-800 text-xs font-mono font-bold transition-all dark:bg-blue-950/60 dark:border-blue-800 dark:text-blue-300"
                title={`Jump to ${range.start}s`}
              >
                <span>⏱ {range.start.toFixed(1)}s – {range.end.toFixed(1)}s</span>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-xs italic py-1">No specific crime interval ranges flagged.</p>
        )}
      </div>

      {/* ── Evidence Events Breakdown ── */}
      <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-2 shadow-2xs">
        <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center justify-between">
          <span>Corroborating Evidence Events</span>
          <span className="font-mono text-slate-500">{detection.evidence_events.length} Events</span>
        </div>

        {detection.evidence_events.length > 0 ? (
          <div className="space-y-2 pt-1 max-h-48 overflow-y-auto pr-1">
            {detection.evidence_events.map((ev, idx) => (
              <div
                key={idx}
                onClick={() => onSeek && onSeek(ev.timestamp_seconds || 0)}
                className="p-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700 cursor-pointer transition-colors space-y-1"
              >
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-800 dark:text-slate-200">
                  <span className="uppercase text-purple-700 dark:text-purple-400">
                    {ev.event_type?.replace(/_/g, " ")}
                  </span>
                  <span className="font-mono text-slate-500">
                    {Number(ev.timestamp_seconds || 0).toFixed(1)}s
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                  {ev.description}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-xs italic py-1">No corroborating events recorded.</p>
        )}
      </div>
    </div>
  );
}
