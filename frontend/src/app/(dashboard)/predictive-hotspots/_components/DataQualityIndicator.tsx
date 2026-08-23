"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";
import type { WardPrediction } from "../types";

interface DataQualityIndicatorProps {
  predictions: WardPrediction[];
}

export function DataQualityIndicator({ predictions }: DataQualityIndicatorProps) {
  const aggregatedQuality = useMemo(() => {
    if (predictions.length === 0) return null;
    let histCov = 0;
    let locComp = 0;
    let catComp = 0;
    let maxFresh = 0;
    
    predictions.forEach((w) => {
      histCov += w.dataQuality.historicalCoverage;
      locComp += w.dataQuality.locationCompleteness;
      catComp += w.dataQuality.categoryCompleteness;
      if (w.dataQuality.dataFreshnessDays > maxFresh) {
        maxFresh = w.dataQuality.dataFreshnessDays;
      }
    });

    const len = predictions.length;
    const overall = Math.round(((histCov + locComp + catComp) / (len * 3)));

    return {
      historicalCoverage: Math.round(histCov / len),
      locationCompleteness: Math.round(locComp / len),
      categoryCompleteness: Math.round(catComp / len),
      dataFreshnessDays: maxFresh,
      overall,
    };
  }, [predictions]);

  if (!aggregatedQuality) {
    return (
      <Card className="h-full border-border/50">
        <CardContent className="h-full flex items-center justify-center text-muted-foreground p-6">
          No data quality metrics available
        </CardContent>
      </Card>
    );
  }

  const getQualityColor = (val: number) => {
    if (val >= 90) return "text-emerald-500 bg-emerald-500/10";
    if (val >= 80) return "text-brand-blue bg-brand-blue/10";
    if (val >= 70) return "text-amber-500 bg-amber-500/10";
    return "text-red-500 bg-red-500/10";
  };

  const getProgressColor = (val: number) => {
    if (val >= 90) return "bg-emerald-500";
    if (val >= 80) return "bg-brand-blue";
    if (val >= 70) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="glass-card flex flex-col h-full relative group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-[40px] rounded-full pointer-events-none" />
      <div className="p-4 sm:p-5 border-b border-white/10 relative z-10">
        <h2 className="text-sm font-heading font-bold flex items-center gap-2 text-foreground">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-500">
            <ShieldCheck className="h-4 w-4" />
          </div>
          Data Quality & Coverage
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Model confidence based on historical data availability
        </p>
      </div>

      <div className="p-4 sm:p-5 flex-1 flex flex-col justify-center relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground/70">Overall Quality</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-3xl font-heading font-black text-foreground">{aggregatedQuality.overall}%</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-500 uppercase tracking-widest">
                {aggregatedQuality.overall >= 90 ? "Excellent" : "Good"}
              </span>
            </div>
          </div>
          <div className="w-16 h-16 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 flex items-center justify-center shrink-0 shadow-inner">
            <Database className="h-5 w-5 text-emerald-500" />
          </div>
        </div>

        <div className="space-y-4">
          {[
            { label: "Historical Coverage", val: aggregatedQuality.historicalCoverage },
            { label: "Location Completeness", val: aggregatedQuality.locationCompleteness },
            { label: "Category Completeness", val: aggregatedQuality.categoryCompleteness },
          ].map((metric) => (
            <div key={metric.label} className="space-y-1.5">
              <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest">
                <span className="text-muted-foreground">{metric.label}</span>
                <span className={getProgressColor(metric.val).replace('bg-', 'text-')}>{metric.val}% Complete</span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${getProgressColor(metric.val)}`} 
                  style={{ width: `${metric.val}%` }} 
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
