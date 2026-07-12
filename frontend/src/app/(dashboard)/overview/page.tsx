"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertTriangle,
  ShieldCheck,
  Activity,
  TrendingDown,
  Building2,
  Scale,
} from "lucide-react";
import * as motion from "motion/react-client";
import { getOverviewKPIs, getTopDistricts } from "@/lib/derive";
import { ipcCrimes, monthlyComparison } from "@/data/crimeData";
import { DistrictVolumeChart } from "./_components/DistrictVolumeChart";
import { CrimeCategoryDonut } from "./_components/CrimeCategoryDonut";
import { MonthlyTrendChart } from "./_components/MonthlyTrendChart";
import { useLanguage } from "@/components/LanguageContext";

const kpiData = getOverviewKPIs();

const kpis = [
  {
    title: "Total Crimes (2025)",
    value: kpiData.totalCrimes.toLocaleString("en-IN"),
    icon: AlertTriangle,
    trend: `${kpiData.yoyChange}%`,
    trendLabel: "vs 2024",
  },
  {
    title: "IPC Cases",
    value: kpiData.ipcCount.toLocaleString("en-IN"),
    icon: Scale,
    trend: `${kpiData.ipcShare}%`,
    trendLabel: "of total",
    positive: true,
  },
  {
    title: "Resolution Rate",
    value: `${kpiData.resolutionRate}%`,
    icon: ShieldCheck,
    trend: "+2.1%",
    trendLabel: "vs 2024",
    positive: true,
  },
  {
    title: "Districts Monitored",
    value: String(kpiData.districtCount),
    icon: Building2,
    trend: "All Ranges",
    trendLabel: "statewide",
    positive: true,
  },
];

export default function OverviewPage() {
  const { t } = useLanguage();
  return (
    <div className="px-4 md:px-6 lg:px-8 pb-8 pt-2 md:pt-2 lg:pt-2 space-y-6 ">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <motion.div 
          initial={{ y: -20, opacity: 0 }} 
          animate={{ y: 0, opacity: 1 }} 
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <h1 className="text-2xl md:text-4xl font-heading font-bold text-brand-purple">
            {t("Dashboard Overview")}
          </h1>
          <p className="text-muted-foreground mt-1 text-sm md:text-base">{t("Karnataka Police Crime Intelligence — 2025 Year-to-Date")}</p>
        </motion.div>
      </div>

      {/* KPI Grid */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <motion.div
              key={kpi.title}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
            >
              <Card className="glass-card relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-brand-purple/10 hover:border-brand-purple/30">
                <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 pointer-events-none" />
                <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 relative">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {t(kpi.title)}
                  </CardTitle>
                  <div className="h-9 w-9 rounded-lg bg-brand-purple/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-brand-purple" />
                  </div>
                </CardHeader>
                <CardContent className="relative">
                  <div className="text-2xl font-mono font-bold gradient-text">
                    {kpi.value}
                  </div>
                  <p className={`text-xs mt-1 flex items-center gap-1 ${
                    kpi.positive !== false && !kpi.trend.startsWith("-")
                      ? "text-emerald-500"
                      : "text-rose-500"
                  }`}>
                    {kpi.trend.startsWith("-") ? (
                      <TrendingDown className="h-3 w-3" />
                    ) : (
                      <Activity className="h-3 w-3" />
                    )}
                    {kpi.trend === "All Ranges" ? t(kpi.trend) : kpi.trend} {t(kpi.trendLabel)}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-6 lg:grid-cols-5">
        <motion.div
          className="lg:col-span-3"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.35 }}
        >
          <DistrictVolumeChart />
        </motion.div>
        <motion.div
          className="lg:col-span-2"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <CrimeCategoryDonut />
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.45 }}
      >
        <MonthlyTrendChart />
      </motion.div>
    </div>
  );
}
