"use client";

import { useState } from "react";
import { getTopDistricts } from "@/lib/derive";
import { useLanguage } from "@/components/LanguageContext";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

type ViewMode = "total" | "ipc" | "sll";
type TimeScale = "annual" | "monthly" | "daily";

export function DistrictVolumeChart() {
  const { t } = useLanguage();
  const [mode, setMode] = useState<ViewMode>("total");
  const [time, setTime] = useState<TimeScale>("annual");
  const top10 = getTopDistricts(10, mode);

  const data = top10.map((d) => {
    const divisor = time === "monthly" ? 12 : time === "daily" ? 365 : 1;
    const ipcVal = time === "daily" ? Math.round((d.ipc / divisor) * 10) / 10 : Math.round(d.ipc / divisor);
    const sllVal = time === "daily" ? Math.round((d.sll / divisor) * 10) / 10 : Math.round(d.sll / divisor);
    const totalVal = time === "daily" ? Math.round(((d.ipc + d.sll) / divisor) * 10) / 10 : Math.round((d.ipc + d.sll) / divisor);

    return {
      name: t(d.name).length > 12 ? t(d.name).slice(0, 12) + "…" : t(d.name),
      fullName: d.name,
      IPC: ipcVal,
      SLL: sllVal,
      Total: totalVal,
    };
  });

  return (
    <div className="bg-surface/40 border border-white/5 p-5 rounded-xl h-full flex flex-col group hover:bg-surface/60 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-lg font-bold text-on-background">
            {t("District Volume Comparison")}
          </h3>
          <p className="text-xs text-on-background/60 mt-1">
            {time === "annual" ? t("2025 Annual Official") : time === "monthly" ? t("2025 Monthly Average") : t("2025 Daily Average")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex gap-1 bg-surface/50 p-1 rounded-lg border border-white/5">
            {(
              [
                { id: "annual", label: "Annual" },
                { id: "monthly", label: "Monthly" },
                { id: "daily", label: "Daily" },
              ] as const
            ).map((item) => (
              <button
                key={item.id}
                onClick={() => setTime(item.id)}
                className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                  time === item.id
                    ? "bg-primary/20 text-primary"
                    : "text-on-background/60 hover:text-on-background hover:bg-white/5"
                }`}
              >
                {t(item.label)}
              </button>
            ))}
          </div>
          <div className="flex gap-1 bg-surface/50 p-1 rounded-lg border border-white/5">
            {(["total", "ipc", "sll"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-3 py-1 rounded text-xs font-bold transition-colors ${
                  mode === m
                    ? "bg-primary text-surface"
                    : "text-on-background/60 hover:text-on-background hover:bg-white/5"
                }`}
              >
                {t(m.toUpperCase())}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="flex-1 w-full min-h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ left: -10, top: 10, bottom: 20 }}>
            <defs>
              <linearGradient id="colorPrimary" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a3d73c" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#a3d73c" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorSecondary" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e1e4d3" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#e1e4d3" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#8c9383" }}
              angle={-35}
              textAnchor="end"
              height={70}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={{ stroke: "rgba(255,255,255,0.1)" }}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: "#8c9383" }} 
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={{ stroke: "rgba(255,255,255,0.1)" }}
            />
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
            {mode === "total" ? (
              <>
                <Area
                  type="monotone"
                  name={t("IPC Cases")}
                  dataKey="IPC"
                  stroke="#a3d73c"
                  fill="url(#colorPrimary)"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#11150b", stroke: "#a3d73c", strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: "#a3d73c", stroke: "#11150b" }}
                  animationDuration={1500}
                />
                <Area
                  type="monotone"
                  name={t("SLL Cases")}
                  dataKey="SLL"
                  stroke="#e1e4d3"
                  fill="url(#colorSecondary)"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#11150b", stroke: "#e1e4d3", strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: "#e1e4d3", stroke: "#11150b" }}
                  animationDuration={1500}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8c9383" }} />
              </>
            ) : mode === "ipc" ? (
              <Area
                type="monotone"
                name={t("IPC Cases")}
                dataKey="IPC"
                stroke="#a3d73c"
                fill="url(#colorPrimary)"
                strokeWidth={2}
                dot={{ r: 4, fill: "#11150b", stroke: "#a3d73c", strokeWidth: 2 }}
                activeDot={{ r: 6, fill: "#a3d73c", stroke: "#11150b" }}
                animationDuration={1500}
              />
            ) : (
              <Area
                type="monotone"
                name={t("SLL Cases")}
                dataKey="SLL"
                stroke="#a3d73c" // use primary when only SLL is shown
                fill="url(#colorPrimary)"
                strokeWidth={2}
                dot={{ r: 4, fill: "#11150b", stroke: "#a3d73c", strokeWidth: 2 }}
                activeDot={{ r: 6, fill: "#a3d73c", stroke: "#11150b" }}
                animationDuration={1500}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
