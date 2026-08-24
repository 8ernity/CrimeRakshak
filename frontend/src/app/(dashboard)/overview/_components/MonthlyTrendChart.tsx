"use client";

import { monthlyComparison } from "@/data/crimeData";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useLanguage } from "@/components/LanguageContext";

export function MonthlyTrendChart() {
  const { t } = useLanguage();
  const data = monthlyComparison.map((row) => ({
    name: t(row.crime).length > 14 ? t(row.crime).slice(0, 14) + "…" : t(row.crime),
    fullName: row.crime,
    "Dec 2024 (Prev Year)": row.prevYearMonth,
    "Nov 2025 (Prev Month)": row.prevMonth,
    "Dec 2025 (Current)": row.currentMonth,
  }));

  return (
    <div className="bg-surface/40 border border-white/5 p-5 rounded-xl group hover:bg-surface/60 transition-colors">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
        <h3 className="text-lg font-bold text-on-background">
          {t("Temporal Trend Analysis")}
        </h3>
      </div>
      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#8c9383" }} // muted-foreground
              angle={-30}
              textAnchor="end"
              height={65}
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
              labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
              cursor={{ fill: "rgba(163, 215, 60, 0.05)" }} // primary with very low opacity
            />
            <Legend wrapperStyle={{ fontSize: 12, color: "#8c9383" }} />
            <Bar
              name={t("Dec 2024 (Prev Year)")}
              dataKey="Dec 2024 (Prev Year)"
              fill="rgba(163, 215, 60, 0.4)" // primary/40
              radius={[4, 4, 0, 0]}
              animationDuration={1500}
            />
            <Bar
              name={t("Nov 2025 (Prev Month)")}
              dataKey="Nov 2025 (Prev Month)"
              fill="rgba(163, 215, 60, 0.7)" // primary/70
              radius={[4, 4, 0, 0]}
              animationDuration={1500}
            />
            <Bar
              name={t("Dec 2025 (Current)")}
              dataKey="Dec 2025 (Current)"
              fill="#a3d73c" // primary
              radius={[4, 4, 0, 0]}
              animationDuration={1500}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
