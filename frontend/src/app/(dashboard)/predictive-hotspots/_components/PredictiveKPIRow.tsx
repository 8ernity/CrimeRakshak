"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useLanguage } from "@/components/LanguageContext";
import { AlertTriangle, Crosshair, TrendingUp, ShieldCheck, Loader2 } from "lucide-react";
import { motion } from "motion/react";

interface PredictiveKPIRowProps {
  highRiskCount: number;
  totalExpectedIncidents: number;
  emergingCount: number;
  avgConfidence: number;
  isLoading: boolean;
}

export function PredictiveKPIRow({
  highRiskCount,
  totalExpectedIncidents,
  emergingCount,
  avgConfidence,
  isLoading,
}: PredictiveKPIRowProps) {
  const { t } = useLanguage();

  const kpis = [
    {
      title: t("High-Risk Wards"),
      value: highRiskCount,
      icon: AlertTriangle,
      color: "text-red-500",
      bg: "bg-red-500/10",
      border: "border-red-500/20",
    },
    {
      title: t("Predicted Incidents"),
      value: totalExpectedIncidents.toFixed(1),
      icon: Crosshair,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
    },
    {
      title: t("Emerging Hotspots"),
      value: emergingCount,
      icon: TrendingUp,
      color: "text-brand-purple",
      bg: "bg-brand-purple/10",
      border: "border-brand-purple/20",
    },
    {
      title: t("Avg. Confidence"),
      value: `${avgConfidence}%`,
      icon: ShieldCheck,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
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
          {/* Ambient Glow */}
          <div className={`absolute -right-12 -top-12 w-32 h-32 rounded-full blur-[40px] opacity-20 group-hover:opacity-40 transition-opacity duration-500 ${kpi.bg.replace('/10', '')}`} />
          
          <div className="p-5 sm:p-6 flex items-center gap-4 relative z-10">
            <div className={`shrink-0 p-3.5 rounded-2xl ${kpi.bg} ${kpi.border} border shadow-inner transition-transform duration-300 group-hover:scale-110`}>
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
