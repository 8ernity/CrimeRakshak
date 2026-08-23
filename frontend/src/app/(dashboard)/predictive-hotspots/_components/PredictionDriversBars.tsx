"use client";

import { useLanguage } from "@/components/LanguageContext";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { WardPrediction } from "../types";

interface PredictionDriversBarsProps {
  drivers: WardPrediction["drivers"];
}

export function PredictionDriversBars({ drivers }: PredictionDriversBarsProps) {
  const { t } = useLanguage();

  if (!drivers || drivers.length === 0) {
    return (
      <div className="py-6 text-center text-sm text-muted-foreground">
        No driver explanation available.
      </div>
    );
  }

  // Find max for scaling
  const maxContribution = Math.max(...drivers.map((d) => d.contribution));

  return (
    <div className="space-y-4">
      {drivers.map((driver, i) => {
        const width = Math.max(5, (driver.contribution / maxContribution) * 100);
        const isPos = driver.direction === "positive";
        
        return (
          <div key={i} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-foreground truncate pr-4">{driver.factor}</span>
              <div className={`flex items-center font-bold shrink-0 ${isPos ? "text-red-400" : "text-emerald-400"}`}>
                {isPos ? <ArrowUpRight className="h-3 w-3 mr-0.5" /> : <ArrowDownRight className="h-3 w-3 mr-0.5" />}
                {Math.round(driver.contribution * 100)}%
              </div>
            </div>
            
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden flex">
              <div 
                className={`h-full rounded-full transition-all duration-1000 ${
                  isPos ? "bg-red-500" : "bg-emerald-500"
                }`}
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
