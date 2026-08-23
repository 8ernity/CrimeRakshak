"use client";

import { useMemo } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useLanguage } from "@/components/LanguageContext";
import { CRIME_CATEGORIES } from "@/data/crimeCategories";
import { 
  Filter, 
  Clock, 
  MapPin, 
  SlidersHorizontal, 
  ShieldAlert, 
  RotateCcw,
  Sparkles
} from "lucide-react";
import type { PredictionFilters, ForecastHorizon, GeoLevel } from "../types";

interface PredictionControlBarProps {
  filters: PredictionFilters;
  onFilterChange: (patch: Partial<PredictionFilters>) => void;
}

export function PredictionControlBar({ filters, onFilterChange }: PredictionControlBarProps) {
  const { t } = useLanguage();

  const isFiltered = useMemo(() => {
    return (
      filters.crimeCategory !== "all" ||
      filters.forecastHorizon !== "24h" ||
      filters.geoLevel !== "ward" ||
      filters.confidenceThreshold !== 0
    );
  }, [filters]);

  const handleReset = () => {
    onFilterChange({
      crimeCategory: "all",
      forecastHorizon: "24h",
      geoLevel: "ward",
      confidenceThreshold: 0,
    });
  };

  return (
    <div className="bg-card/90 backdrop-blur-xl border border-border/80 p-4 sm:p-5 rounded-3xl shadow-[0_10px_30px_rgba(0,0,0,0.06)] relative z-30">
      
      {/* Top Bar Header Label */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-brand-purple/10 text-brand-purple">
            <Filter className="h-3.5 w-3.5" />
          </div>
          <span className="text-[11px] font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
            {t("Prediction Filter Parameters")}
          </span>
        </div>

        {isFiltered && (
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-purple/10 text-brand-purple hover:bg-brand-purple/20 transition-all cursor-pointer border border-brand-purple/20"
          >
            <RotateCcw className="h-3 w-3" />
            {t("Reset Filters")}
          </button>
        )}
      </div>

      {/* Grid of Control Pickers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        
        {/* Crime Category */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 pl-1">
            <ShieldAlert className="h-3 w-3 text-brand-blue" />
            {t("Crime Category")}
          </label>
          <Select
            value={filters.crimeCategory}
            onValueChange={(val) => val && onFilterChange({ crimeCategory: val })}
          >
            <SelectTrigger className="h-11 bg-card border border-border/80 text-foreground hover:border-emerald-500/40 hover:bg-emerald-50/50 dark:hover:bg-emerald-500/10 shadow-sm focus:ring-2 focus:ring-emerald-500/30 rounded-xl px-3.5 w-full flex items-center justify-between text-xs font-semibold transition-all cursor-pointer">
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent className="bg-card text-card-foreground border border-border/80 shadow-[0_10px_40px_rgba(0,0,0,0.12)] p-1.5 rounded-xl z-[9999] opacity-100">
              {CRIME_CATEGORIES.map((c) => (
                <SelectItem 
                  key={c.id} 
                  value={c.id} 
                  className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200"
                >
                  {t(c.label)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Forecast Horizon */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 pl-1">
            <Clock className="h-3 w-3 text-brand-purple" />
            {t("Forecast Horizon")}
          </label>
          <Select
            value={filters.forecastHorizon}
            onValueChange={(val) => val && onFilterChange({ forecastHorizon: val as ForecastHorizon })}
          >
            <SelectTrigger className="h-11 bg-card border border-border/80 text-foreground hover:border-emerald-500/40 hover:bg-emerald-50/50 dark:hover:bg-emerald-500/10 shadow-sm focus:ring-2 focus:ring-emerald-500/30 rounded-xl px-3.5 w-full flex items-center justify-between text-xs font-semibold transition-all cursor-pointer">
              <SelectValue placeholder="Select horizon" />
            </SelectTrigger>
            <SelectContent className="bg-card text-card-foreground border border-border/80 shadow-[0_10px_40px_rgba(0,0,0,0.12)] p-1.5 rounded-xl z-[9999] opacity-100">
              <SelectItem value="6h" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("6 Hours")}</SelectItem>
              <SelectItem value="12h" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("12 Hours")}</SelectItem>
              <SelectItem value="24h" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("24 Hours")}</SelectItem>
              <SelectItem value="7d" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("7 Days")}</SelectItem>
              <SelectItem value="30d" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("30 Days")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Geographic Level */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 pl-1">
            <MapPin className="h-3 w-3 text-emerald-500" />
            {t("Geographic Level")}
          </label>
          <Select
            value={filters.geoLevel}
            onValueChange={(val) => val && onFilterChange({ geoLevel: val as GeoLevel })}
          >
            <SelectTrigger className="h-11 bg-card border border-border/80 text-foreground hover:border-emerald-500/40 hover:bg-emerald-50/50 dark:hover:bg-emerald-500/10 shadow-sm focus:ring-2 focus:ring-emerald-500/30 rounded-xl px-3.5 w-full flex items-center justify-between text-xs font-semibold transition-all cursor-pointer">
              <SelectValue placeholder="Select level" />
            </SelectTrigger>
            <SelectContent className="bg-card text-card-foreground border border-border/80 shadow-[0_10px_40px_rgba(0,0,0,0.12)] p-1.5 rounded-xl z-[9999] opacity-100">
              <SelectItem value="ward" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("Ward (Fine-grained)")}</SelectItem>
              <SelectItem value="district" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("District Level")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Confidence Threshold */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 pl-1">
            <SlidersHorizontal className="h-3 w-3 text-amber-500" />
            {t("Min Confidence")}
          </label>
          <Select
            value={String(filters.confidenceThreshold)}
            onValueChange={(val) => val !== null && onFilterChange({ confidenceThreshold: parseInt(val, 10) })}
          >
            <SelectTrigger className="h-11 bg-card border border-border/80 text-foreground hover:border-emerald-500/40 hover:bg-emerald-50/50 dark:hover:bg-emerald-500/10 shadow-sm focus:ring-2 focus:ring-emerald-500/30 rounded-xl px-3.5 w-full flex items-center justify-between text-xs font-semibold transition-all cursor-pointer">
              <SelectValue placeholder="Min confidence" />
            </SelectTrigger>
            <SelectContent className="bg-card text-card-foreground border border-border/80 shadow-[0_10px_40px_rgba(0,0,0,0.12)] p-1.5 rounded-xl z-[9999] opacity-100">
              <SelectItem value="0" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("All Predictions (0%+)")}</SelectItem>
              <SelectItem value="75" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("> 75% Confidence")}</SelectItem>
              <SelectItem value="85" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("> 85% Confidence")}</SelectItem>
              <SelectItem value="90" className="cursor-pointer text-xs font-semibold px-3 py-2.5 rounded-lg focus:bg-emerald-500/10 focus:text-emerald-600 dark:focus:text-emerald-400 data-[state=checked]:bg-emerald-500/15 data-[state=checked]:text-emerald-700 dark:data-[state=checked]:text-emerald-400 transition-all duration-200">{t("> 90% High Precision")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

      </div>
    </div>
  );
}
