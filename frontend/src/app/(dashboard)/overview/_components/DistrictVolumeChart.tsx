"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { brandColors } from "@/lib/design-tokens";

type ViewMode = "total" | "ipc" | "sll";

export function DistrictVolumeChart() {
  const { t } = useLanguage();
  const [mode, setMode] = useState<ViewMode>("total");
  const [time, setTime] = useState<"7d" | "30d" | "90d">("30d");
  const top10 = getTopDistricts(10, mode);

  const data = top10.map((d) => {
    const scale = time === "7d" ? 0.25 : time === "30d" ? 1 : 3;
    return {
      name: t(d.name).length > 12 ? t(d.name).slice(0, 12) + "…" : t(d.name),
      IPC: Math.round(d.ipc * scale),
      SLL: Math.round(d.sll * scale),
      Total: Math.round((d.ipc + d.sll) * scale),
    };
  });

  return (
    <Card className="glass-card relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <CardTitle className="font-heading text-base">
          {t("Top 10 Districts — Crime Volume")}
        </CardTitle>
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex gap-1 bg-muted/40 p-1 rounded-lg">
            {(["7d", "30d", "90d"] as const).map((timeVal) => (
              <Button
                key={timeVal}
                size="sm"
                variant={time === timeVal ? "secondary" : "ghost"}
                className="text-xs h-7 px-3 rounded-md"
                onClick={() => setTime(timeVal)}
              >
                {t(timeVal.toUpperCase())}
              </Button>
            ))}
          </div>
          <div className="flex gap-1 bg-muted/40 p-1 rounded-lg">
            {(["total", "ipc", "sll"] as const).map((m) => (
              <Button
                key={m}
                size="sm"
                variant={mode === m ? "default" : "ghost"}
                className="text-xs h-7 px-3 rounded-md shadow-none"
                onClick={() => setMode(m)}
              >
                {t(m.toUpperCase())}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[320px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ left: 15, top: 10, bottom: 20 }}>
              <defs>
                <linearGradient id="colorIpc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorSll" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--chart-2)" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="var(--chart-2)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                angle={-35}
                textAnchor="end"
                height={70}
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
              />
              {mode === "total" ? (
                <>
                  <Area type="natural" name={t("IPC")} dataKey="IPC" stroke="var(--chart-1)" fill="url(#colorIpc)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={1500} animationEasing="ease-in-out" />
                  <Area type="natural" name={t("SLL")} dataKey="SLL" stroke="var(--chart-2)" fill="url(#colorSll)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={1500} animationEasing="ease-in-out" />
                  <Legend />
                </>
              ) : mode === "ipc" ? (
                <Area type="natural" name={t("IPC")} dataKey="IPC" stroke="var(--chart-1)" fill="url(#colorIpc)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={1500} animationEasing="ease-in-out" />
              ) : (
                <Area type="natural" name={t("SLL")} dataKey="SLL" stroke="var(--chart-2)" fill="url(#colorSll)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={1500} animationEasing="ease-in-out" />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
