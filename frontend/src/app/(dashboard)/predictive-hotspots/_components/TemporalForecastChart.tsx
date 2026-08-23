"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/components/LanguageContext";
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ComposedChart } from "recharts";
import { Activity, Clock, LineChart as LucideLineChart } from "lucide-react";
import type { WardPrediction, ViewMode } from "../types";

interface TemporalForecastChartProps {
  ward: WardPrediction | null;
  allPredictions: WardPrediction[];
  viewMode: ViewMode;
}

export function TemporalForecastChart({ ward, allPredictions, viewMode }: TemporalForecastChartProps) {
  const { t } = useLanguage();

  const data = useMemo(() => {
    if (ward) return ward.temporalForecast;
    if (allPredictions.length === 0) return [];

    // If no ward selected, aggregate temporal forecast across all top 5 hotspots
    const top5 = allPredictions.slice(0, 5);
    const aggregated = top5[0].temporalForecast.map((pt, i) => {
      let sumPred = 0;
      let sumHist = 0;
      let sumUpper = 0;
      let sumLower = 0;
      top5.forEach((w) => {
        sumPred += w.temporalForecast[i].predictedRisk;
        sumHist += w.temporalForecast[i].historicalRisk;
        sumUpper += w.temporalForecast[i].confidenceUpper;
        sumLower += w.temporalForecast[i].confidenceLower;
      });
      return {
        timestamp: pt.timestamp,
        predictedRisk: Math.round(sumPred / top5.length),
        historicalRisk: Math.round(sumHist / top5.length),
        confidenceUpper: Math.round(sumUpper / top5.length),
        confidenceLower: Math.round(sumLower / top5.length),
      };
    });
    return aggregated;
  }, [ward, allPredictions]);

  if (data.length === 0) {
    return (
      <Card className="border-border/50">
        <CardContent className="h-[300px] flex flex-col items-center justify-center text-muted-foreground">
          <Activity className="h-8 w-8 mb-2 opacity-50" />
          <p className="text-sm">No temporal data available</p>
        </CardContent>
      </Card>
    );
  }

  const formatHour = (ts: any) => {
    if (!ts) return "";
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="glass-card flex flex-col relative overflow-hidden group">
      <div className="absolute top-0 left-0 w-64 h-64 bg-brand-purple/5 blur-[60px] rounded-full pointer-events-none" />
      <div className="p-4 sm:p-5 border-b border-white/10 relative z-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-heading font-bold flex items-center gap-2 text-foreground">
              <div className="p-1.5 rounded-lg bg-brand-purple/10 text-brand-purple">
                <LucideLineChart className="h-4 w-4" />
              </div>
              {t("Temporal Forecast")}
            </h2>
            <p className="text-xs text-muted-foreground mt-1">
              {viewMode === "historical" ? t("Past observed incidents") : t("Predicted incidents over next 24 hours")}
            </p>
          </div>
          <div className="flex items-center gap-3 bg-black/10 px-3 py-1.5 rounded-xl border border-white/5 shadow-inner">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-brand-purple" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Predicted</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Historical Avg</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="p-4 sm:p-5 h-[300px] w-full relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickMargin={10}
              tickFormatter={formatHour}
            />
            <YAxis 
              tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => `${val}`}
            />
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'rgba(15, 23, 42, 0.8)', 
                backdropFilter: 'blur(12px)',
                borderColor: 'rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '12px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
              }}
              labelStyle={{ color: 'rgba(255,255,255,0.5)', marginBottom: '4px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px' }}
              itemStyle={{ color: '#fff' }}
              labelFormatter={formatHour}
            />
            
            {viewMode === "predicted" && (
              <Area 
                type="monotone" 
                dataKey="confidenceUpper" 
                stroke="none" 
                fill="url(#colorConfidence)" 
                fillOpacity={1}
              />
            )}
            {viewMode === "predicted" && (
              <Area 
                type="monotone" 
                dataKey="confidenceLower" 
                stroke="none" 
                fill="#0f172a" 
                fillOpacity={1}
              />
            )}

            <Line 
              type="monotone" 
              dataKey="historicalRisk" 
              stroke="rgba(255,255,255,0.3)" 
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              name="Historical Baseline"
            />
            <Line 
              type="monotone" 
              dataKey="predictedRisk" 
              stroke="#a855f7" 
              strokeWidth={3}
              dot={{ r: 3, fill: "#a855f7", strokeWidth: 0 }}
              activeDot={{ r: 6, fill: "#a855f7", stroke: "#0f172a", strokeWidth: 2 }}
              name="Predicted Risk"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
