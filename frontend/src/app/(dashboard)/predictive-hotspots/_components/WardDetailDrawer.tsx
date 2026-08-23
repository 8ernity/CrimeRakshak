"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { X, MapPin, Activity, BrainCircuit, AlertTriangle, Info } from "lucide-react";
import { getCategoryLabel } from "@/data/crimeCategories";
import { riskTierColors } from "@/lib/design-tokens";
import { PredictionDriversBars } from "./PredictionDriversBars";
import { getWardExplanation } from "@/lib/predictiveHotspotsApi";
import type { WardPrediction } from "../types";

interface WardDetailDrawerProps {
  ward: WardPrediction;
  dataSource: "live" | "demo";
  onClose: () => void;
}

export function WardDetailDrawer({ ward, dataSource, onClose }: WardDetailDrawerProps) {
  const [drivers, setDrivers] = useState<WardPrediction["drivers"] | null>(null);
  const [isLoadingExpl, setIsLoadingExpl] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadExplanation() {
      setIsLoadingExpl(true);
      const res = await getWardExplanation(ward.wardId);
      if (mounted) {
        setDrivers(res.drivers);
        setIsLoadingExpl(false);
      }
    }
    loadExplanation();
    return () => { mounted = false; };
  }, [ward.wardId]);

  const riskColor = riskTierColors[ward.riskLevel];

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-background/60 backdrop-blur-md z-[500]"
      />
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed top-0 right-0 h-full w-full max-w-md bg-card/80 backdrop-blur-2xl border-l border-white/10 shadow-2xl z-[510] flex flex-col"
      >
        <div className="flex items-center justify-between p-6 border-b border-white/10 bg-black/10">
          <div>
            <h2 className="text-2xl font-heading font-black italic tracking-tight text-foreground flex items-center gap-2">
              <div className="p-2 rounded-xl bg-brand-purple/10 border border-brand-purple/20">
                <MapPin className="h-5 w-5 text-brand-purple" />
              </div>
              {ward.wardName}
            </h2>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-2 font-bold">
              {ward.adminArea} | {ward.district}
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-10 w-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-muted-foreground hover:bg-white/10 hover:text-foreground transition-colors hover:scale-110 active:scale-95 shadow-sm"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide bg-black/5">
          
          {/* Main Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="glass-card p-5 relative overflow-hidden group">
              <div className="absolute -right-4 -bottom-4 w-24 h-24 rounded-full blur-[20px] opacity-20" style={{ backgroundColor: riskColor }} />
              <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold flex items-center gap-1.5 mb-2 relative z-10">
                <Activity className="h-3.5 w-3.5" />
                Risk Score
              </span>
              <div className="flex items-baseline gap-1.5 relative z-10 mt-2">
                <span className="text-4xl font-heading font-black" style={{ color: riskColor }}>
                  {ward.riskScore}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">/ 100</span>
              </div>
              <div 
                className="mt-3 text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded-full inline-block shadow-inner relative z-10"
                style={{ backgroundColor: `${riskColor}15`, color: riskColor, border: `1px solid ${riskColor}30` }}
              >
                {ward.riskLevel}
              </div>
            </div>

            <div className="glass-card p-5 relative overflow-hidden">
              <div className="absolute -right-4 -bottom-4 w-24 h-24 rounded-full blur-[20px] opacity-20 bg-brand-blue" />
              <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold flex items-center gap-1.5 mb-2 relative z-10">
                <BrainCircuit className="h-3.5 w-3.5 text-brand-blue" />
                Model Confidence
              </span>
              <div className="flex items-baseline gap-1.5 relative z-10 mt-2">
                <span className="text-4xl font-heading font-black text-foreground">
                  {ward.confidence}%
                </span>
              </div>
              <div className="mt-3 text-[10px] font-bold text-muted-foreground relative z-10 uppercase tracking-widest">
                Prob: <strong className="text-foreground">{(ward.probability * 100).toFixed(1)}%</strong>
              </div>
            </div>
          </div>

          {/* Model Meta */}
          <div className="glass-card p-5 border border-brand-purple/20 bg-brand-purple/5 relative overflow-hidden">
            <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay pointer-events-none" />
            <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-brand-purple mb-4 relative z-10">
              <Info className="h-4 w-4" />
              Prediction Meta
            </div>
            <div className="grid grid-cols-2 gap-y-4 gap-x-4 relative z-10">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">Category</span>
                <span className="text-xs font-bold text-foreground mt-1">{getCategoryLabel(ward.crimeCategory)}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">Horizon</span>
                <span className="text-xs font-bold text-foreground mt-1">{ward.predictionHorizon}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">Model</span>
                <span className="text-xs font-bold text-foreground mt-1">{ward.modelName} ({ward.modelVersion})</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">Generated</span>
                <span className="text-xs font-bold text-foreground mt-1">
                  {ward.predictionAgeMinutes} mins ago
                </span>
              </div>
            </div>
          </div>

          {/* Feature Importance */}
          <div>
            <h3 className="text-sm font-heading font-bold text-foreground border-b border-border/50 pb-2 mb-4">
              Key Risk Drivers
            </h3>
            {isLoadingExpl ? (
              <div className="h-32 flex items-center justify-center text-muted-foreground text-sm">
                Loading model explanation...
              </div>
            ) : (
              <PredictionDriversBars drivers={drivers ?? ward.drivers} />
            )}
            {dataSource === "demo" && (
              <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-500/90 leading-tight">
                  This explanation is based on demo data because the live ML backend is unreachable.
                </p>
              </div>
            )}
          </div>
          
        </div>
      </motion.div>
    </>
  );
}
