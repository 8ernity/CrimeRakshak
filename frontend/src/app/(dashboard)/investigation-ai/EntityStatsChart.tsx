"use client";

import React, { useMemo } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { BarChart2 } from "lucide-react";
import type { Detection } from "./types";

interface EntityStatsChartProps {
  detections: Detection[];
}

const CLASS_META: Record<string, { label: string; color: string }> = {
  person: { label: "Persons", color: "#3B82F6" },
  car: { label: "Vehicles", color: "#F59E0B" },
  truck: { label: "Trucks", color: "#D97706" },
  motorcycle: { label: "Motorcycles", color: "#10B981" },
  bicycle: { label: "Bicycles", color: "#059669" },
};

export function EntityStatsChart({ detections }: EntityStatsChartProps) {
  const data = useMemo(() => {
    const counts: Record<string, number> = {};
    const uniqueTrackPerClass: Record<string, Set<number>> = {};

    for (const d of detections) {
      if (!uniqueTrackPerClass[d.object_class]) {
        uniqueTrackPerClass[d.object_class] = new Set();
      }
      if (d.tracking_id !== null) {
        uniqueTrackPerClass[d.object_class].add(d.tracking_id);
      }
      counts[d.object_class] = (counts[d.object_class] || 0) + 1;
    }

    return Object.entries(counts).map(([cls, count]) => ({
      name: CLASS_META[cls]?.label || cls,
      value: uniqueTrackPerClass[cls]?.size || count,
      rawDetections: count,
      color: CLASS_META[cls]?.color || "#8B5CF6",
    }));
  }, [detections]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/95 backdrop-blur-md border border-white/40 shadow-xl rounded-xl p-3 flex flex-col gap-0.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{payload[0].name}</span>
          <span className="text-lg font-black text-slate-900">{payload[0].value} Unique</span>
          <span className="text-[11px] text-slate-500">{payload[0].payload.rawDetections} total detections</span>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-sm font-medium text-slate-400">No detection data.</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full relative group">
      <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-blue-500/10 blur-[50px] rounded-full pointer-events-none group-hover:bg-blue-500/20 transition-all duration-700" />

      <div className="flex items-center gap-3 mb-4 relative z-10">
        <div className="p-2 rounded-xl bg-blue-50 border border-blue-100/50 shadow-sm">
          <BarChart2 className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <h3 className="font-bold text-slate-900 tracking-tight text-base leading-tight">Entity Demographics</h3>
          <span className="text-[11px] font-medium text-slate-500">Unique tracked subjects by class</span>
        </div>
      </div>

      <div className="flex-1 w-full relative z-10 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="48%"
              innerRadius="55%"
              outerRadius="80%"
              paddingAngle={4}
              dataKey="value"
              stroke="none"
              animationDuration={1200}
              animationEasing="ease-out"
            >
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.color}
                  className="outline-none"
                  style={{ outline: "none" }}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "transparent" }} />
            <Legend
              verticalAlign="bottom"
              height={30}
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => (
                <span className="text-[11px] font-semibold text-slate-600 ml-1">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
