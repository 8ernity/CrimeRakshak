"use client";

import React, { useState } from "react";
import {
  FileText, AlertTriangle, CheckCircle2, Clock, Eye, Users, Car,
  Shield, Crosshair, HelpCircle, AlertOctagon, ChevronDown, ChevronUp,
  Zap, Target, ImageIcon, RefreshCw,
} from "lucide-react";
import type { AIInvestigationReport, EvidenceObservation, DetectedEntity, TimelineEntry, EvidenceFrameRef } from "./types";

interface AIReportPanelProps {
  report: AIInvestigationReport | null;
  isLoading?: boolean;
  onSeek?: (timeSeconds: number) => void;
  onRefresh?: () => void;
}

/* ── Source Badge ── */
function SourceBadge({ source }: { source: string }) {
  const cfg: Record<string, { bg: string; text: string; label: string }> = {
    directly_observed: { bg: "bg-emerald-50 dark:bg-emerald-950/50", text: "text-emerald-700 dark:text-emerald-300", label: "Observed" },
    ai_inference: { bg: "bg-blue-50 dark:bg-blue-950/50", text: "text-blue-700 dark:text-blue-300", label: "AI Inference" },
    uncertain: { bg: "bg-amber-50 dark:bg-amber-950/50", text: "text-amber-700 dark:text-amber-300", label: "Uncertain" },
  };
  const c = cfg[source] || cfg.uncertain;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${c.bg} ${c.text} border border-current/10`}>
      {c.label}
    </span>
  );
}

/* ── Significance Dot ── */
function SignificanceDot({ significance }: { significance: string }) {
  const color = significance === "critical" ? "bg-rose-500" : significance === "notable" ? "bg-amber-400" : "bg-slate-300";
  return <span className={`inline-block w-2 h-2 rounded-full ${color}`} />;
}

/* ── Collapsible Section ── */
function Section({ title, icon: Icon, count, children, defaultOpen = true }: {
  title: string; icon: React.ElementType; count?: number; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-2xs overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          <Icon className="w-3.5 h-3.5" />
          <span>{title}</span>
          {count !== undefined && <span className="font-mono text-slate-400">({count})</span>}
        </div>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
      </button>
      {open && <div className="px-3.5 pb-3 space-y-2">{children}</div>}
    </div>
  );
}

export function AIReportPanel({ report, isLoading, onSeek, onRefresh }: AIReportPanelProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-56 text-slate-400 text-xs font-medium space-y-2">
        <FileText className="w-8 h-8 text-slate-300 animate-pulse" />
        <p>Generating AI Investigation Report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-56 text-slate-400 text-xs font-medium space-y-2">
        <FileText className="w-8 h-8 text-slate-300" />
        <p>No AI report available. Upload and analyze media first.</p>
      </div>
    );
  }

  const confPct = Math.round(report.confidence * 100);
  const isCrime = report.incident_classification !== "No Criminal Activity Observed" &&
                  report.incident_classification !== "Insufficient Evidence for Classification";

  return (
    <div className="space-y-3 text-xs font-sans">
      {/* ── Header: Refresh + Provider ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-600" />
          <span className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
            AI Investigation Report
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400">
            {report.provider_used === "gemini_vision" ? "🤖 Gemini Vision" : "📐 Deterministic"}
          </span>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-2 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-[10px] flex items-center gap-1 transition-colors"
            >
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          )}
        </div>
      </div>

      {/* ── Classification Banner ── */}
      <div className={`p-4 rounded-2xl border transition-all ${
        isCrime
          ? "bg-rose-50/90 border-rose-200 text-rose-950 dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-200"
          : "bg-emerald-50/90 border-emerald-200 text-emerald-950 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-200"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-sm">
            {isCrime ? <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" /> : <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />}
            <span>{report.incident_classification}</span>
          </div>
          <span className={`px-3 py-1 rounded-full font-extrabold text-xs tracking-wide shadow-2xs ${
            isCrime ? "bg-rose-600 text-white" : "bg-emerald-600 text-white"
          }`}>
            {confPct}%
          </span>
        </div>
      </div>

      {/* ── Executive Summary ── */}
      <div className="p-3.5 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900 text-slate-800 dark:text-slate-200 font-medium leading-relaxed text-xs">
        {report.executive_summary || "No summary available."}
      </div>

      {/* ── Frames Supplied ── */}
      <div className="flex items-center gap-2 px-1">
        <ImageIcon className="w-3.5 h-3.5 text-purple-500" />
        <span className="text-[11px] text-slate-500 font-medium">
          {report.frames_supplied_to_model} evidence frame(s) supplied to vision model
        </span>
      </div>

      {/* ── Observed Evidence ── */}
      <Section title="Observed Evidence" icon={Eye} count={report.observed_evidence.length}>
        {report.observed_evidence.length > 0 ? (
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {report.observed_evidence.map((ev: EvidenceObservation, i: number) => (
              <div key={i} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700 space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] text-slate-700 dark:text-slate-300 leading-snug flex-1">{ev.observation}</span>
                  <SourceBadge source={ev.source} />
                </div>
                {ev.timestamp_seconds != null && (
                  <button onClick={() => onSeek?.(ev.timestamp_seconds!)} className="text-[10px] text-blue-600 font-mono hover:underline">
                    ⏱ {ev.timestamp_seconds.toFixed(1)}s
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No observed evidence recorded.</p>
        )}
      </Section>

      {/* ── Detected Objects ── */}
      <Section title="Detected Objects" icon={Crosshair} count={report.detected_objects.length} defaultOpen={false}>
        {report.detected_objects.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {report.detected_objects.map((obj: string, i: number) => (
              <span key={i} className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/70 dark:border-slate-700">
                {obj}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No objects detected.</p>
        )}
      </Section>

      {/* ── Persons & Vehicles ── */}
      <Section title="Persons & Vehicles" icon={Users} count={report.detected_persons_vehicles.length} defaultOpen={false}>
        {report.detected_persons_vehicles.length > 0 ? (
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {report.detected_persons_vehicles.map((ent: DetectedEntity, i: number) => (
              <div key={i} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700 flex items-center justify-between gap-2">
                <div>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase mr-2 ${
                    ent.entity_type === "weapon" ? "bg-rose-100 text-rose-700" :
                    ent.entity_type === "person" ? "bg-blue-100 text-blue-700" :
                    ent.entity_type === "vehicle" ? "bg-amber-100 text-amber-700" :
                    "bg-slate-100 text-slate-600"
                  }`}>{ent.entity_type}</span>
                  <span className="text-[11px] text-slate-700 dark:text-slate-300">{ent.description}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">{Math.round(ent.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No persons or vehicles detected.</p>
        )}
      </Section>

      {/* ── Chronological Timeline ── */}
      <Section title="Chronological Timeline" icon={Clock} count={report.chronological_timeline.length}>
        {report.chronological_timeline.length > 0 ? (
          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {report.chronological_timeline.map((entry: TimelineEntry, i: number) => (
              <div key={i} className="flex items-start gap-2 p-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                   onClick={() => onSeek?.(entry.timestamp_seconds)}>
                <SignificanceDot significance={entry.significance} />
                <button className="text-[10px] font-mono text-blue-600 min-w-[3.5rem] text-left">{entry.timestamp_seconds.toFixed(1)}s</button>
                <span className="text-[11px] text-slate-700 dark:text-slate-300 flex-1 leading-snug">{entry.description}</span>
                <SourceBadge source={entry.source} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No timeline entries.</p>
        )}
      </Section>

      {/* ── Evidence Frame References ── */}
      <Section title="Evidence Frame References" icon={ImageIcon} count={report.evidence_frame_references.length} defaultOpen={false}>
        {report.evidence_frame_references.length > 0 ? (
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {report.evidence_frame_references.map((ref: EvidenceFrameRef, i: number) => (
              <div key={i} className="p-2 rounded-lg bg-purple-50/60 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900 space-y-1 cursor-pointer"
                   onClick={() => onSeek?.(ref.timestamp_seconds)}>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-purple-700 dark:text-purple-400">Frame #{ref.frame_index}</span>
                  <span className="text-[10px] font-mono text-purple-500">{ref.timestamp_seconds.toFixed(1)}s</span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">{ref.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No frame references.</p>
        )}
      </Section>

      {/* ── Crime Indicators ── */}
      <Section title="Crime Indicators" icon={AlertOctagon} count={report.crime_indicators.length} defaultOpen={false}>
        {report.crime_indicators.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {report.crime_indicators.map((ind: string, i: number) => (
              <span key={i} className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200/70 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800">
                🚨 {ind.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic py-1">No crime indicators flagged.</p>
        )}
      </Section>

      {/* ── Uncertainty Notes ── */}
      <Section title="Uncertainty Notes" icon={HelpCircle} count={report.uncertainty_notes.length} defaultOpen={false}>
        <ul className="list-disc pl-4 space-y-1">
          {report.uncertainty_notes.map((note: string, i: number) => (
            <li key={i} className="text-[11px] text-amber-700 dark:text-amber-400 leading-snug">{note}</li>
          ))}
        </ul>
      </Section>

      {/* ── Limitations ── */}
      <Section title="Limitations" icon={Shield} count={report.limitations.length} defaultOpen={false}>
        <ul className="list-disc pl-4 space-y-1">
          {report.limitations.map((lim: string, i: number) => (
            <li key={i} className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">{lim}</li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
