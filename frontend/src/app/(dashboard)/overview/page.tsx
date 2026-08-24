"use client";

import { useState, useMemo } from "react";
import { useUser } from "@clerk/nextjs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  ShieldCheck,
  Activity,
  TrendingDown,
  Building2,
  Scale,
  Siren,
  FileCheck,
  Brain,
  Filter,
  CheckCircle2
} from "lucide-react";
import * as motion from "motion/react-client";
import { getOverviewKPIs, getDistrictsByRange } from "@/lib/derive";
import { districts } from "@/data/crimeData";
import { DistrictVolumeChart } from "./_components/DistrictVolumeChart";
import { CrimeCategoryDonut } from "./_components/CrimeCategoryDonut";
import { MonthlyTrendChart } from "./_components/MonthlyTrendChart";
import { useLanguage } from "@/components/LanguageContext";

const RANGES = [
  "All Karnataka",
  "Bengaluru Commissionerate",
  "Southern Range",
  "Coastal Range",
  "North Karnataka Range"
] as const;

export default function OverviewPage() {
  const { t } = useLanguage();
  const { user } = useUser();
  const [selectedRange, setSelectedRange] = useState<string>("All Karnataka");

  const userName = user?.firstName || user?.fullName || "Officer";
  const baseKpis = useMemo(() => getOverviewKPIs(), []);

  // Calculate dynamic KPIs based on selected range
  const dynamicStats = useMemo(() => {
    if (selectedRange === "All Karnataka") {
      return {
        totalCrimes: baseKpis.totalCrimes,
        ipcCount: baseKpis.ipcCount,
        resolutionRate: baseKpis.resolutionRate,
        districtCount: baseKpis.districtCount,
        yoyChange: baseKpis.yoyChange,
        ipcShare: baseKpis.ipcShare,
      };
    }

    const matchedDistricts = districts.filter((d) => {
      if (selectedRange === "Bengaluru Commissionerate") return d.name.includes("Bengaluru");
      if (selectedRange === "Southern Range") return ["Mysuru City", "Mysuru Dist", "Mandya", "Hassan", "Kodagu"].includes(d.name);
      if (selectedRange === "Coastal Range") return ["Mangaluru City", "D.K.", "Udupi", "Uttara Kannada"].includes(d.name);
      return ["Kalaburagi", "Belagavi City", "Belagavi Dist", "Ballari", "Hubballi-Dharwad"].includes(d.name);
    });

    const rangeIpc = matchedDistricts.reduce((acc, d) => acc + d.ipc, 0);
    const rangeSll = matchedDistricts.reduce((acc, d) => acc + d.sll, 0);
    const rangeTotal = rangeIpc + rangeSll;
    const share = rangeTotal > 0 ? Math.round((rangeIpc / rangeTotal) * 100) : 70;

    return {
      totalCrimes: rangeTotal || 4520,
      ipcCount: rangeIpc || 3150,
      resolutionRate: 88.4,
      districtCount: matchedDistricts.length || 5,
      yoyChange: -2.4,
      ipcShare: share,
    };
  }, [selectedRange, baseKpis]);

  const kpis = [
    {
      title: "Total Crimes",
      value: dynamicStats.totalCrimes.toLocaleString("en-IN"),
      icon: "crisis_alert",
      trend: `${dynamicStats.yoyChange}% vs 2024`,
      trendLabel: "vs 2024",
      positive: true,
    },
    {
      title: "IPC Cases",
      value: dynamicStats.ipcCount.toLocaleString("en-IN"),
      icon: "gavel",
      trend: `${dynamicStats.ipcShare}% of total`,
      trendLabel: "of total",
      positive: true,
    },
    {
      title: "Resolution Rate",
      value: `${dynamicStats.resolutionRate}%`,
      icon: "verified_user",
      trend: "+2.1% statutory clearance",
      trendLabel: "statutory clearance",
      positive: true,
    },
    {
      title: "Monitored Jurisdictions",
      value: String(dynamicStats.districtCount),
      icon: "location_city",
      trend: `${selectedRange} active sector`,
      trendLabel: "active sector",
      positive: true,
    },
  ];

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto w-full">
      {/* Header Section */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between mb-8 gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-widest text-primary bg-primary/10 border border-primary/20 uppercase">
              {t("MACRO SURVEILLANCE")}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-on-background">
            {t("Welcome")}, {userName}
          </h1>
          <p className="text-sm text-on-background/60">
            {t("Executive Pattern Snapshot")}
          </p>
        </div>

        {/* Range Filter Selector */}
        <div className="flex items-center space-x-2 bg-surface/50 p-1 rounded-lg border border-white/5 overflow-x-auto">
          {RANGES.map((range) => (
            <button
              key={range}
              onClick={() => setSelectedRange(range)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                selectedRange === range
                  ? "bg-primary text-surface"
                  : "text-on-background/70 hover:text-on-background hover:bg-white/5"
              }`}
            >
              {t(range)}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Early Warning Banner & Governance SLA Row ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {/* Early Warning Banner */}
        <div className="bg-surface/40 border border-[#ffb4ab]/20 p-4 rounded-xl flex items-center justify-between relative overflow-hidden group">
          <div className="absolute inset-0 bg-[#ffb4ab]/5 group-hover:bg-[#ffb4ab]/10 transition-colors"></div>
          <div className="flex items-start space-x-4 relative z-10">
            <div className="p-2 bg-[#ffb4ab]/10 rounded-lg">
              <span className="material-symbols-outlined text-[#ffb4ab] animate-pulse">
                warning
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs font-bold text-[#ffb4ab] uppercase tracking-wider">
                  AI PREDICTIVE ALERT
                </span>
                <span className="px-2 py-0.5 rounded bg-[#ffb4ab]/20 text-[#ffb4ab] text-[10px] font-mono font-bold">
                  ACTIVE
                </span>
              </div>
              <p className="text-sm font-medium text-on-background">
                Projected +14.2% Property Theft anomaly.
              </p>
              <p className="text-xs text-on-background/60">
                Action: Pre-deploy units &amp; step up screening.
              </p>
            </div>
          </div>
          <button className="relative z-10 px-4 py-2 bg-[#ffb4ab]/10 text-[#ffb4ab] text-xs font-bold rounded-lg border border-[#ffb4ab]/20 hover:bg-[#ffb4ab]/20 transition-colors whitespace-nowrap">
            Triage Alerts →
          </button>
        </div>

        {/* Governance SLA */}
        <div className="bg-surface/40 border border-primary/20 p-4 rounded-xl flex items-center justify-between relative overflow-hidden group">
          <div className="absolute inset-0 bg-primary/5 group-hover:bg-primary/10 transition-colors"></div>
          <div className="flex items-start space-x-4 relative z-10">
            <div className="p-2 bg-primary/10 rounded-lg">
              <span className="material-symbols-outlined text-primary">
                policy
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs font-bold text-primary uppercase tracking-wider">
                  DIGITAL POLICING SLA
                </span>
                <span className="px-2 py-0.5 rounded bg-primary/20 text-primary text-[10px] font-mono font-bold flex items-center space-x-1">
                  <span className="material-symbols-outlined text-[12px]">
                    check_circle
                  </span>
                  <span>VERIFIED</span>
                </span>
              </div>
              <p className="text-sm font-medium text-on-background">
                eSign FIR Compliance: 98.4% | Service Disposal: 96.8%.
              </p>
              <p className="text-xs text-on-background/60">
                All records backed by immutable audit logs.
              </p>
            </div>
          </div>
          <button className="relative z-10 px-4 py-2 bg-primary/10 text-primary text-xs font-bold rounded-lg border border-primary/20 hover:bg-primary/20 transition-colors whitespace-nowrap">
            Audit Log →
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {kpis.map((kpi, i) => (
          <div key={i} className="bg-surface/60 border border-white/5 p-5 rounded-xl hover:bg-surface/80 hover:border-primary/30 transition-all group">
            <div className="flex items-start justify-between mb-4">
              <span className="text-sm font-medium text-on-background/60">
                {t(kpi.title)}
              </span>
              <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                <span className="material-symbols-outlined text-primary text-sm">
                  {kpi.icon}
                </span>
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-on-background mb-1">
                {kpi.value}
              </div>
              <div className="flex items-center space-x-1">
                <span className="material-symbols-outlined text-[14px] text-primary">
                  trending_down
                </span>
                <span className="text-xs font-medium text-primary">
                  {kpi.trend}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <DistrictVolumeChart />
        </div>
        <div className="lg:col-span-1">
          <CrimeCategoryDonut />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="w-full">
        <MonthlyTrendChart />
      </div>
    </div>
  );
}

