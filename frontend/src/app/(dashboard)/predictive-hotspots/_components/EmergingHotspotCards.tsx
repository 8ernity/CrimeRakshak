"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/components/LanguageContext";
import { TrendingUp, ArrowUpRight, Flame } from "lucide-react";
import type { WardPrediction } from "../types";

interface EmergingHotspotCardsProps {
  predictions: WardPrediction[];
  onSelectWard: (id: string) => void;
}

export function EmergingHotspotCards({ predictions, onSelectWard }: EmergingHotspotCardsProps) {
  const { t } = useLanguage();

  const emergingWards = predictions
    .filter((w) => w.hotspotStatus === "emerging")
    .sort((a, b) => b.riskChange - a.riskChange)
    .slice(0, 3); // Show top 3 emerging

  return (
    <div className="glass-card flex flex-col h-full relative group">
      <div className="absolute top-0 right-0 w-48 h-48 bg-red-500/5 blur-[50px] rounded-full pointer-events-none" />
      <div className="p-4 sm:p-5 border-b border-white/10 relative z-10">
        <h2 className="text-sm font-heading font-bold flex items-center gap-2 text-foreground">
          <div className="p-1.5 rounded-lg bg-red-500/10 text-red-500">
            <Flame className="h-4 w-4" />
          </div>
          {t("Emerging Risk Zones")}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          {t("Wards with fastest growing predicted risk velocity")}
        </p>
      </div>
      
      <CardContent className="p-4 sm:p-5">
        {emergingWards.length === 0 ? (
          <div className="h-full min-h-[100px] flex flex-col items-center justify-center text-muted-foreground">
            <TrendingUp className="h-6 w-6 mb-2 opacity-50" />
            <p className="text-xs">No emerging hotspots detected</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {emergingWards.map((ward) => (
              <button
                key={ward.wardId}
                onClick={() => onSelectWard(ward.wardId)}
                className="text-left p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-red-500/30 transition-all duration-300 group/emerging shadow-[0_4px_20px_rgba(0,0,0,0.05)] relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover/emerging:opacity-100 transition-opacity" />
                <div className="flex items-start justify-between relative z-10">
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-foreground">{ward.wardName}</span>
                    <span className="text-[10px] text-muted-foreground font-medium">{ward.district}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs font-black text-red-500 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/20 shadow-sm">
                    <TrendingUp className="h-3 w-3" />
                    +{ward.riskChange}%
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between relative z-10">
                  <div className="flex flex-col">
                    <span className="text-[9px] uppercase tracking-widest text-muted-foreground/70">Est. Score</span>
                    <span className="text-lg font-black text-foreground leading-none mt-1">{ward.riskScore}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[9px] uppercase tracking-widest text-muted-foreground/70">Confidence</span>
                    <span className="text-sm font-bold text-muted-foreground mt-1">{ward.confidence}%</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </div>
  );
}
