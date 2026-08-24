"use client";

import { ipcCrimes } from "@/data/crimeData";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useLanguage } from "@/components/LanguageContext";

export function CrimeCategoryDonut() {
  const { t } = useLanguage();
  const top8 = [...ipcCrimes]
    .sort((a, b) => b.total - a.total)
    .slice(0, 8);
  const otherTotal = ipcCrimes
    .filter((c) => !top8.includes(c))
    .reduce((s, c) => s + c.total, 0);

  const stateTotalIpc = ipcCrimes.reduce((s, c) => s + c.total, 0);

  const data = [
    ...top8.map((c) => ({ name: t(c.category), value: c.total })),
    { name: t("Other Categories"), value: otherTotal },
  ];

  // Tactical colors matching Chart.js config in the HTML
  const tacticalColors = [
    "#a3d73c", // primary
    "#e1e4d3", // on-background
    "#8c9383", // muted
    "#4caf50", 
    "#8bc34a",
    "#cddc39",
    "#ffeb3b",
    "#ffc107",
    "#ff9800"
  ];

  return (
    <div className="bg-surface/40 border border-white/5 p-5 rounded-xl h-full flex flex-col group hover:bg-surface/60 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-on-background/70">
          {t("Category Share")}
        </h3>
        <span className="material-symbols-outlined text-primary text-sm">
          donut_large
        </span>
      </div>
      <div className="flex-1 relative min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="75%" // 80% cutout equivalent
              outerRadius="95%"
              paddingAngle={2}
              dataKey="value"
              animationDuration={1500}
              animationEasing="ease-out"
              stroke="transparent" // Remove border
            >
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={tacticalColors[i % tacticalColors.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "rgba(17, 21, 11, 0.9)", // surface color
                border: "1px solid rgba(163, 215, 60, 0.2)", // primary/20
                borderRadius: "8px",
                color: "#e1e4d3",
                fontSize: "12px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.5)",
              }}
              itemStyle={{ color: "#e1e4d3", fontWeight: 600 }}
              formatter={(value: any) => value?.toLocaleString("en-IN")}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center Donut Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-[10px] uppercase font-bold text-on-background/60 tracking-wider">
            {t("TOTAL IPC")}
          </span>
          <span className="text-2xl font-bold text-on-background">
            {stateTotalIpc.toLocaleString("en-IN")}
          </span>
        </div>
      </div>
    </div>
  );
}
