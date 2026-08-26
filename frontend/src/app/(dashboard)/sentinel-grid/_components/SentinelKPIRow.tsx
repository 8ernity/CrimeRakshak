"use client";

import { Card } from "@/components/ui/card";
import { motion } from "motion/react";
import { Wifi, Activity, AlertOctagon, Link2, Loader2 } from "lucide-react";
import type { SentinelSummary } from "@/lib/sentinelApi";

interface SentinelKPIRowProps {
  summary: SentinelSummary | null;
  isLoading: boolean;
}

export function SentinelKPIRow({ summary, isLoading }: SentinelKPIRowProps) {
  const kpis = [
    {
      title: "Active Sensors",
      value: summary?.active_sensors ?? 0,
      icon: Wifi,
      color: "text-brand-blue",
      bg: "bg-brand-blue/10",
      border: "border-brand-blue/20",
      glow: "bg-brand-blue",
    },
    {
      title: "Events (24h)",
      value: summary?.events_last_24h ?? 0,
      icon: Activity,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      glow: "bg-amber-500",
    },
    {
      title: "High-Priority Active",
      value: summary?.high_priority_active ?? 0,
      icon: AlertOctagon,
      color: "text-red-500",
      bg: "bg-red-500/10",
      border: "border-red-500/20",
      glow: "bg-red-500",
    },
    {
      title: "Cases Auto-Linked",
      value: summary?.cases_auto_linked ?? 0,
      icon: Link2,
      color: "text-brand-purple",
      bg: "bg-brand-purple/10",
      border: "border-brand-purple/20",
      glow: "bg-brand-purple",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
      {kpis.map((kpi, i) => (
        <motion.div
          key={i}
          whileHover={{ y: -4, scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="glass-card overflow-hidden group cursor-pointer relative"
        >
          {/* Ambient glow */}
          <div
            className={`absolute -right-12 -top-12 w-32 h-32 rounded-full blur-[40px] opacity-20 group-hover:opacity-40 transition-opacity duration-500 ${kpi.glow}`}
          />
          <div className="p-5 sm:p-6 flex items-center gap-4 relative z-10">
            <div
              className={`shrink-0 p-3.5 rounded-2xl ${kpi.bg} ${kpi.border} border shadow-inner transition-transform duration-300 group-hover:scale-110`}
            >
              <kpi.icon className={`h-6 w-6 ${kpi.color}`} />
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest truncate mb-1">
                {kpi.title}
              </span>
              <div className="flex items-center gap-2">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <motion.span
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    key={kpi.value}
                    className="text-2xl sm:text-4xl font-heading font-black text-foreground tracking-tight"
                  >
                    {kpi.value}
                  </motion.span>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
