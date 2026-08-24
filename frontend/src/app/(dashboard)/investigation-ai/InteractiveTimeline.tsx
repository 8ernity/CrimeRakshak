"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { Clock, Activity, AlertTriangle, Car, LogOut, Shield } from "lucide-react";
import type { InvestigationEvent } from "./types";

const EVENT_CONFIG: Record<string, { icon: React.ElementType; bg: string; border: string; iconColor: string; badge: string; label?: string }> = {
  person_entered_frame: { icon: Activity, bg: "bg-blue-50", border: "border-blue-100 hover:border-blue-300", iconColor: "text-blue-500", badge: "Entry", label: "PERSON ENTERED" },
  person_detected: { icon: Activity, bg: "bg-blue-50", border: "border-blue-100 hover:border-blue-300", iconColor: "text-blue-500", badge: "Detected", label: "PERSON DETECTED" },
  possible_person_down: { icon: AlertTriangle, bg: "bg-red-50", border: "border-red-100 hover:border-red-300", iconColor: "text-red-500", badge: "Anomaly", label: "POSSIBLE PERSON DOWN" },
  posture_falling: { icon: AlertTriangle, bg: "bg-red-50", border: "border-red-100 hover:border-red-300", iconColor: "text-red-500", badge: "Falling", label: "FALLING" },
  posture_lying_down: { icon: AlertTriangle, bg: "bg-red-50", border: "border-red-100 hover:border-red-300", iconColor: "text-red-500", badge: "Lying Down", label: "LYING DOWN" },
  posture_sitting: { icon: Activity, bg: "bg-indigo-50", border: "border-indigo-100 hover:border-indigo-300", iconColor: "text-indigo-500", badge: "Sitting", label: "SITTING" },
  posture_standing: { icon: Activity, bg: "bg-emerald-50", border: "border-emerald-100 hover:border-emerald-300", iconColor: "text-emerald-500", badge: "Standing", label: "STANDING" },
  posture_running: { icon: Activity, bg: "bg-amber-50", border: "border-amber-100 hover:border-amber-300", iconColor: "text-amber-500", badge: "Running", label: "RUNNING" },
  pattern_fall_lying_down: { icon: AlertTriangle, bg: "bg-red-50", border: "border-red-100 hover:border-red-300", iconColor: "text-red-500", badge: "Fall-Lie", label: "FALL → LYING DOWN" },
  pattern_approach_interaction_leave: { icon: Activity, bg: "bg-purple-50", border: "border-purple-100 hover:border-purple-300", iconColor: "text-purple-500", badge: "Sequence", label: "APPROACH-INTERACT-LEAVE" },
  pattern_person_following: { icon: Activity, bg: "bg-amber-50", border: "border-amber-100 hover:border-amber-300", iconColor: "text-amber-500", badge: "Sequence", label: "PERSON FOLLOWING" },
  pattern_rapid_movement_chase: { icon: AlertTriangle, bg: "bg-orange-50", border: "border-orange-100 hover:border-orange-300", iconColor: "text-orange-500", badge: "Rapid", label: "RAPID MOVEMENT / CHASE" },
  pattern_multi_person_interaction: { icon: Activity, bg: "bg-purple-50", border: "border-purple-100 hover:border-purple-300", iconColor: "text-purple-500", badge: "Interaction", label: "MULTI-PERSON INTERACTION" },
  pattern_person_vehicle_interaction: { icon: Car, bg: "bg-amber-50", border: "border-amber-100 hover:border-amber-300", iconColor: "text-amber-500", badge: "Vehicle", label: "PERSON-VEHICLE INTERACTION" },
  pattern_entry_activity_exit: { icon: Activity, bg: "bg-blue-50", border: "border-blue-100 hover:border-blue-300", iconColor: "text-blue-500", badge: "Sequence", label: "ENTRY-ACTIVITY-EXIT" },
  vehicle_detected: { icon: Car, bg: "bg-amber-50", border: "border-amber-100 hover:border-amber-300", iconColor: "text-amber-500", badge: "Vehicle", label: "VEHICLE DETECTED" },
  person_exited_frame: { icon: LogOut, bg: "bg-slate-50", border: "border-slate-200 hover:border-slate-300", iconColor: "text-slate-400", badge: "Exit", label: "PERSON EXITED" },
};

const DEFAULT_CONFIG = { icon: Clock, bg: "bg-slate-50", border: "border-slate-200 hover:border-slate-300", iconColor: "text-slate-400", badge: "Event" };

interface InteractiveTimelineProps {
  events: InvestigationEvent[];
  onJumpToTimestamp: (timeSeconds: number) => void;
}

export function InteractiveTimeline({ events, onJumpToTimestamp }: InteractiveTimelineProps) {
  const [filterType, setFilterType] = useState<string | null>(null);

  const filtered = filterType ? events.filter(e => e.event_type === filterType) : events;
  const uniqueTypes = Array.from(new Set(events.map(e => e.event_type)));

  const getEventTitle = (event: InvestigationEvent): string => {
    if (event.event_type === "posture_falling") return "FALLING";
    if (event.event_type === "posture_lying_down") return "LYING DOWN";
    if (event.event_type === "posture_sitting") return "SITTING";
    if (event.event_type === "posture_standing") return "STANDING";
    if (event.event_type === "posture_running") return "RUNNING";
    if (event.event_type === "possible_person_down") {
      const descUpper = (event.description || "").toUpperCase();
      if (descUpper.includes("LYING_DOWN") || descUpper.includes("LYING DOWN")) return "LYING DOWN";
      if (descUpper.includes("FALLING") || descUpper.includes("FALL")) return "FALLING";
      return "POSSIBLE PERSON DOWN";
    }
    const cfg = EVENT_CONFIG[event.event_type];
    if (cfg?.label) return cfg.label;
    return event.event_type.replace(/^posture_/, "").replace(/^pattern_/, "").replace(/_/g, " ").toUpperCase();
  };

  const containerVariants = {
    initial: {},
    animate: { transition: { staggerChildren: 0.08, delayChildren: 0.15 } },
  };
  const itemVariants = {
    initial: { opacity: 0, x: 16 },
    animate: { opacity: 1, x: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
  };

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      {/* Ambient glow */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 blur-[60px] rounded-full pointer-events-none" />

      {/* Header */}
      <div className="px-5 pt-5 pb-3 relative z-10">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-slate-900 tracking-tight text-base">Event Timeline</h3>
          <span className="px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-bold text-indigo-600 uppercase tracking-wider">
            {filtered.length} {filtered.length === 1 ? "Event" : "Events"}
          </span>
        </div>

        {/* Filter Pills */}
        {uniqueTypes.length > 1 && (
          <div className="flex gap-1.5 flex-wrap">
            <button
              onClick={() => setFilterType(null)}
              className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all duration-300 ${
                filterType === null
                  ? "bg-slate-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-500 hover:bg-slate-200"
              }`}
            >
              All
            </button>
            {uniqueTypes.map(type => {
              const cfg = EVENT_CONFIG[type] || DEFAULT_CONFIG;
              return (
                <button
                  key={type}
                  onClick={() => setFilterType(type === filterType ? null : type)}
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all duration-300 ${
                    filterType === type
                      ? "bg-slate-900 text-white shadow-sm"
                      : `${cfg.bg} ${cfg.iconColor} hover:opacity-80`
                  }`}
                >
                  {cfg.badge}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto px-5 pb-5 scrollbar-hide relative z-10">
        <motion.div
          variants={containerVariants}
          initial="initial"
          animate="animate"
          className="flex flex-col gap-3 relative"
        >
          {/* Vertical connector */}
          {filtered.length > 0 && (
            <div className="absolute left-5 top-3 bottom-3 w-px bg-gradient-to-b from-slate-200 via-slate-200 to-transparent" />
          )}

          {filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center px-4">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                <Shield className="w-6 h-6 text-slate-400" />
              </div>
              <span className="text-sm font-bold text-slate-700 mb-1">
                No significant events detected
              </span>
              <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                Automated pose estimation and object tracking detected no critical timeline events for this media.
              </p>
            </div>
          )}

          {filtered.map((event) => {
            const cfg = EVENT_CONFIG[event.event_type] || DEFAULT_CONFIG;
            const Icon = cfg.icon;
            const titleText = getEventTitle(event);

            return (
              <motion.div
                key={event.event_id}
                variants={itemVariants}
                whileHover={{ x: 4 }}
                onClick={() => onJumpToTimestamp(event.start_timestamp_seconds)}
                className="flex gap-3 cursor-pointer group"
              >
                {/* Timeline node */}
                <div className="relative z-10 mt-1 flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-white shadow-sm border border-slate-100 flex items-center justify-center group-hover:scale-110 group-hover:shadow-md transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]">
                    <Icon className={`w-4 h-4 ${cfg.iconColor}`} />
                  </div>
                </div>

                {/* Event card */}
                <div className={`flex-1 p-3.5 rounded-xl border shadow-sm transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:shadow-md ${cfg.bg} ${cfg.border}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-extrabold text-slate-800 uppercase tracking-wide">
                      {titleText}
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 tabular-nums">
                      {event.start_timestamp_seconds.toFixed(1)}s
                    </span>
                  </div>
                  <p className="text-[12px] leading-relaxed text-slate-600">{event.description}</p>
                  {event.tracking_id !== null && event.tracking_id !== undefined && (
                    <span className="inline-block mt-1.5 px-2 py-0.5 rounded-md bg-white/80 border border-slate-200/60 text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                      Track #{event.tracking_id}
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}

