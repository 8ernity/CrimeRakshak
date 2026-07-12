"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { brandColors } from "@/lib/design-tokens";
import { useLanguage } from "@/components/LanguageContext";

export function MonthlyTrendChart() {
  const { t } = useLanguage();
  const data = monthlyComparison.map((row) => ({
    name: t(row.crime).length > 14 ? t(row.crime).slice(0, 14) + "…" : t(row.crime),
    "Prev Year": row.prevYearMonth,
    "Prev Month": row.prevMonth,
    "Current": row.currentMonth,
  }));

  return (
    <Card className="glass-card relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20">
      <CardHeader>
        <CardTitle className="font-heading text-base">
          {t("Monthly Trend — December 2025 Comparison")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ left: -10 }}>
              <defs>
                <linearGradient id="colorPrevYear" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8cc5e3" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8cc5e3" stopOpacity={0.2}/>
                </linearGradient>
                <linearGradient id="colorPrevMonth" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#52a2d0" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#52a2d0" stopOpacity={0.2}/>
                </linearGradient>
                <linearGradient id="colorCurrent" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1a80bb" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#1a80bb" stopOpacity={0.2}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                angle={-30}
                textAnchor="end"
                height={65}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
              <Tooltip
                contentStyle={{
                  background: "rgba(255, 255, 255, 0.75)",
                  backdropFilter: "blur(20px)",
                  WebkitBackdropFilter: "blur(20px)",
                  border: "1px solid rgba(255, 255, 255, 0.7)",
                  borderRadius: "16px",
                  boxShadow: "0 8px 30px rgba(80, 140, 255, 0.08)",
                  color: "#0f172a",
                }}
                itemStyle={{ color: "#0f172a", fontWeight: 500 }}
                cursor={{ fill: "rgba(143, 211, 255, 0.1)" }}
              />
              <Legend />
              <Bar name={t("Prev Year")} dataKey="Prev Year" fill="url(#colorPrevYear)" radius={[6, 6, 0, 0]} animationDuration={1500} animationEasing="ease-out" />
              <Bar name={t("Prev Month")} dataKey="Prev Month" fill="url(#colorPrevMonth)" radius={[6, 6, 0, 0]} animationDuration={1500} animationEasing="ease-out" />
              <Bar name={t("Current")} dataKey="Current" fill="url(#colorCurrent)" radius={[6, 6, 0, 0]} animationDuration={1500} animationEasing="ease-out" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
