"use client";

import { Camera, Car, Phone, Zap, Clock } from "lucide-react";

export type SensorTypeFilter = "all" | "cctv_alert" | "anpr_hit" | "sos_button" | "gunshot";
export type PriorityFilter = "all" | "high" | "normal";
export type TimeWindowHours = 1 | 6 | 24;

interface SentinelFiltersProps {
  sensorType: SensorTypeFilter;
  priority: PriorityFilter;
  timeWindow: TimeWindowHours;
  onSensorTypeChange: (v: SensorTypeFilter) => void;
  onPriorityChange: (v: PriorityFilter) => void;
  onTimeWindowChange: (v: TimeWindowHours) => void;
}

const SENSOR_TYPE_OPTIONS: { value: SensorTypeFilter; label: string; icon: React.ElementType }[] = [
  { value: "all",        label: "All",      icon: Camera },
  { value: "cctv_alert", label: "CCTV",     icon: Camera },
  { value: "anpr_hit",   label: "ANPR",     icon: Car },
  { value: "sos_button", label: "SOS",      icon: Phone },
  { value: "gunshot",    label: "Gunshot",  icon: Zap },
];

const PRIORITY_OPTIONS: { value: PriorityFilter; label: string }[] = [
  { value: "all",    label: "All Priority" },
  { value: "high",   label: "High" },
  { value: "normal", label: "Normal" },
];

const TIME_OPTIONS: { value: TimeWindowHours; label: string }[] = [
  { value: 1,  label: "1h" },
  { value: 6,  label: "6h" },
  { value: 24, label: "24h" },
];

function ChipGroup<T extends string | number>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string; icon?: React.ElementType }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="p-1 rounded-full bg-slate-200/60 dark:bg-slate-800/60 backdrop-blur-md border border-slate-300/40 dark:border-slate-700/50 flex items-center gap-0.5 shadow-inner">
      {options.map((opt) => {
        const Icon = opt.icon;
        const isActive = value === opt.value;
        return (
          <button
            key={String(opt.value)}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
              isActive
                ? "bg-blue-600 text-white shadow-sm border border-blue-500/30"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            {Icon && <Icon className="h-3 w-3" />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export function SentinelFilters({
  sensorType, priority, timeWindow,
  onSensorTypeChange, onPriorityChange, onTimeWindowChange,
}: SentinelFiltersProps) {
  return (
    <div className="glass-card p-4 flex flex-wrap items-center gap-4">
      {/* Sensor type */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground whitespace-nowrap">
          Sensor
        </span>
        <ChipGroup value={sensorType} options={SENSOR_TYPE_OPTIONS} onChange={onSensorTypeChange} />
      </div>

      {/* Priority */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground whitespace-nowrap">
          Priority
        </span>
        <ChipGroup value={priority} options={PRIORITY_OPTIONS} onChange={onPriorityChange} />
      </div>

      {/* Time window */}
      <div className="flex items-center gap-2 ml-auto">
        <Clock className="h-3.5 w-3.5 text-muted-foreground" />
        <ChipGroup value={timeWindow} options={TIME_OPTIONS} onChange={onTimeWindowChange} />
      </div>
    </div>
  );
}
