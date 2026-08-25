"use client";

import { useEffect, useRef } from "react";
import { Camera, Car, Phone, Zap, Link2 } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { SensorEvent } from "@/lib/sentinelApi";

const SENSOR_ICONS: Record<string, React.ElementType> = {
  cctv_alert: Camera,
  anpr_hit:   Car,
  sos_button: Phone,
  gunshot:    Zap,
};

const TYPE_COLORS: Record<string, string> = {
  cctv_alert: "text-brand-blue",
  anpr_hit:   "text-amber-500",
  sos_button: "text-red-500",
  gunshot:    "text-brand-purple",
};

const TYPE_BG: Record<string, string> = {
  cctv_alert: "bg-brand-blue/10",
  anpr_hit:   "bg-amber-500/10",
  sos_button: "bg-red-500/10",
  gunshot:    "bg-brand-purple/10",
};

const TYPE_LABELS: Record<string, string> = {
  cctv_alert: "CCTV Alert",
  anpr_hit:   "ANPR Hit",
  sos_button: "SOS Button",
  gunshot:    "Gunshot",
};

function relativeTime(iso: string): string {
  const diff = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

interface AlertFeedPanelProps {
  events: SensorEvent[];
}

export function AlertFeedPanel({ events }: AlertFeedPanelProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll to top when new event arrives
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [events.length]);

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-sm font-heading font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Live Alert Feed
        </h2>
        <span className="text-[10px] text-muted-foreground font-semibold bg-muted/50 border border-border/50 px-2 py-0.5 rounded-full">
          {events.length} events
        </span>
      </div>

      <div
        ref={listRef}
        className="flex-1 overflow-y-auto scrollbar-hide divide-y divide-border/20"
      >
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 gap-2 text-muted-foreground">
            <span className="text-2xl">📡</span>
            <span className="text-xs font-medium">Awaiting sensor events…</span>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {events.map((ev) => {
              const Icon = SENSOR_ICONS[ev.sensor_type] ?? Camera;
              const isHigh = ev.priority === "high";

              return (
                <motion.div
                  key={ev.id}
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -24 }}
                  transition={{ duration: 0.25 }}
                  className={`flex items-start gap-3 px-4 py-3 group relative ${
                    isHigh
                      ? "border-l-2 border-red-500 bg-red-500/[0.04] hover:bg-red-500/[0.07]"
                      : "hover:bg-muted/30"
                  } transition-colors duration-150`}
                >
                  {/* Sensor icon */}
                  <div
                    className={`shrink-0 p-2 rounded-xl ${TYPE_BG[ev.sensor_type] ?? "bg-muted"} mt-0.5`}
                  >
                    <Icon className={`h-3.5 w-3.5 ${TYPE_COLORS[ev.sensor_type] ?? "text-foreground"}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`text-xs font-bold truncate ${TYPE_COLORS[ev.sensor_type] ?? "text-foreground"}`}
                      >
                        {TYPE_LABELS[ev.sensor_type] ?? ev.sensor_type}
                      </span>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap font-mono">
                        {relativeTime(ev.timestamp)}
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
                      {ev.ward_name}
                      {ev.district ? ` — ${ev.district}` : ""}
                    </div>

                    {/* Badges row */}
                    <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                      {isHigh && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-red-500/15 text-red-500 border border-red-500/25 uppercase tracking-widest">
                          HIGH
                        </span>
                      )}
                      <span className="text-[9px] font-mono text-muted-foreground">
                        {Math.round(ev.confidence * 100)}% conf
                      </span>
                      {ev.linked_case_id && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-brand-purple/15 text-brand-purple border border-brand-purple/25 flex items-center gap-0.5">
                          <Link2 className="h-2.5 w-2.5" />
                          {ev.linked_case_id}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
