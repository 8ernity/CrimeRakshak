"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/components/LanguageContext";
import { ArrowUpRight, ArrowDownRight, Loader2, ListOrdered, ChevronRight } from "lucide-react";
import type { WardPrediction } from "../types";

interface HotspotRankingTableProps {
  predictions: WardPrediction[];
  selectedWardId: string | null;
  onSelectWard: (id: string) => void;
  isLoading: boolean;
}

export function HotspotRankingTable({
  predictions,
  selectedWardId,
  onSelectWard,
  isLoading,
}: HotspotRankingTableProps) {
  const { t } = useLanguage();

  return (
    <div className="glass-card h-[500px] xl:h-[600px] flex flex-col relative group">
      {/* Ambient glow behind ranking */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-brand-purple/10 blur-[40px] rounded-full pointer-events-none" />

      <div className="p-4 sm:p-5 border-b border-white/10 shrink-0 relative z-10">
        <h2 className="text-sm font-heading font-bold flex items-center justify-between text-foreground">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-brand-purple/10 text-brand-purple">
              <ListOrdered className="h-4 w-4" />
            </div>
            {t("Top Hotspots")}
          </div>
          <span className="text-[9px] text-muted-foreground font-bold bg-black/20 border border-white/5 px-2.5 py-1 rounded-full tracking-widest uppercase shadow-inner">
            Ranked by Risk
          </span>
        </h2>
      </div>
      
      <div className="p-0 overflow-y-auto flex-1 scrollbar-hide relative z-10">
        {isLoading && (
          <div className="absolute inset-0 bg-background/20 backdrop-blur-md z-10 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-brand-purple" />
          </div>
        )}

        <div className="flex flex-col p-2 space-y-1">
          {predictions.map((ward, idx) => {
            const isSelected = selectedWardId === ward.wardId;
            const isIncrease = ward.riskChange > 0;
            const isDecrease = ward.riskChange < 0;

            return (
              <button
                key={ward.wardId}
                onClick={() => onSelectWard(ward.wardId)}
                className={`w-full text-left p-3 lg:p-4 rounded-xl transition-all duration-300 group/item relative overflow-hidden ${
                  isSelected 
                    ? "bg-white/10 border-white/20 shadow-[0_4px_15px_rgba(0,0,0,0.1)]" 
                    : "bg-transparent border-transparent hover:bg-white/5 hover:border-white/10"
                } border`}
              >
                {/* Active indicator */}
                {isSelected && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-brand-purple" />
                )}

                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-[10px] font-black text-muted-foreground w-4 shrink-0 mt-0.5">{idx + 1}.</span>
                    <span className="text-sm font-bold text-foreground truncate group-hover/item:text-brand-purple transition-colors">
                      {ward.wardName}
                    </span>
                  </div>
                  <ChevronRight className={`h-4 w-4 shrink-0 transition-transform duration-300 ${isSelected ? "text-brand-purple translate-x-0.5" : "text-muted-foreground/30 opacity-0 group-hover/item:opacity-100 group-hover/item:translate-x-0"}`} />
                </div>
                
                <div className="flex items-center justify-between pl-6.5">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-muted-foreground font-medium">{ward.district}</span>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end">
                      <span className="text-sm font-black text-foreground">{ward.riskScore}</span>
                      <span className="text-[8px] uppercase tracking-widest text-muted-foreground/70">Score</span>
                    </div>
                    
                    <div className="flex flex-col items-end w-12">
                      <div className={`flex items-center text-xs font-bold ${isIncrease ? "text-red-500 drop-shadow-[0_0_8px_rgba(239,68,68,0.3)]" : isDecrease ? "text-emerald-500" : "text-muted-foreground"}`}>
                        {isIncrease && <ArrowUpRight className="h-3 w-3 mr-0.5" />}
                        {isDecrease && <ArrowDownRight className="h-3 w-3 mr-0.5" />}
                        {Math.abs(ward.riskChange)}%
                      </div>
                      <span className="text-[8px] uppercase tracking-widest text-muted-foreground/70">Change</span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
          
          {predictions.length === 0 && !isLoading && (
            <div className="p-8 text-center flex flex-col items-center gap-3 opacity-50">
              <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-muted-foreground">!</div>
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">No hotspots matched your filters.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
