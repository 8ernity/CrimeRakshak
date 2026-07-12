"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { districts } from "@/data/crimeData";
import { getRiskTier, getRiskScore, getTopDistricts, getSafestDistricts } from "@/lib/derive";
import { riskTierBg, riskTierColors, type RiskTier } from "@/lib/design-tokens";
import * as motion from "motion/react-client";
import { Map, MapPin, Shield, AlertTriangle } from "lucide-react";
import { AnimatePresence } from "motion/react";
import { useLanguage } from "@/components/LanguageContext";

export default function HeatmapPage() {
  const { t } = useLanguage();
  const [selected, setSelected] = useState<string | null>(null);
  const selectedDistrict = districts.find((d) => d.name === selected);
  const top5 = getTopDistricts(5);
  const safest5 = getSafestDistricts(5);

  // Group districts by risk for the visual grid (since we don't have real SVG map data)
  const sortedDistricts = [...districts].sort((a, b) => (b.ipc + b.sll) - (a.ipc + a.sll));

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6">
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
        <h1 className="text-2xl md:text-3xl font-heading font-bold flex items-center gap-2">
          <Map className="h-7 w-7 text-brand-green" /> {t("AI Crime Hotspot Map")}
        </h1>
        <p className="text-muted-foreground mt-1">{t("Interactive Karnataka district risk map — click a district to see details")}</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Map Grid */}
        <Card className="glass-card lg:col-span-2 relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 pointer-events-none" />
          <CardHeader className="relative"><CardTitle className="font-heading text-base">{t("Karnataka Districts — Risk Heatmap")}</CardTitle></CardHeader>
          <CardContent className="relative">
            <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
              {sortedDistricts.map((d, i) => {
                const tier = getRiskTier(d);
                const score = getRiskScore(d);
                const isSelected = selected === d.name;
                return (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: i * 0.02 }}
                    key={d.name}
                    onClick={() => setSelected(d.name)}
                    className={`relative p-2 rounded-lg border text-center transition-all duration-200 hover:scale-105 hover:shadow-md ${
                      isSelected ? "ring-2 ring-brand-purple scale-105 shadow-md" : ""
                    }`}
                    style={{
                      backgroundColor: `${riskTierColors[tier]}15`,
                      borderColor: `${riskTierColors[tier]}40`,
                    }}
                    title={`${d.name} — ${tier}`}
                  >
                    <MapPin className="h-3 w-3 mx-auto mb-1" style={{ color: riskTierColors[tier] }} />
                    <span className="text-[9px] font-medium leading-tight block truncate">
                      {t(d.name).length > 10 ? t(d.name).slice(0, 10) + "…" : t(d.name)}
                    </span>
                    <span className="text-[8px] font-mono block" style={{ color: riskTierColors[tier] }}>
                      {score}
                    </span>
                  </motion.button>
                );
              })}
            </div>
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-border justify-center">
              {(["Safe", "Moderate", "High", "Critical"] as RiskTier[]).map((tier) => (
                <div key={tier} className="flex items-center gap-1.5 text-xs">
                  <div className="h-3 w-3 rounded-sm" style={{ backgroundColor: riskTierColors[tier] }} />
                  <span>{t(tier)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Side Panels */}
        <motion.div 
          className="space-y-4"
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {/* Selected District */}
          <Card className="glass-card relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20">
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 pointer-events-none" />
            <CardHeader className="relative"><CardTitle className="font-heading text-sm">{t("Selected District")}</CardTitle></CardHeader>
            <CardContent className="relative">
              <AnimatePresence mode="wait">
                {selectedDistrict ? (
                  <motion.div 
                    key={selectedDistrict.name}
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    <h3 className="font-bold text-lg text-brand-purple">{t(selectedDistrict.name)}</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-muted-foreground">{t("Range")}</span><span>{t(selectedDistrict.range)}</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">{t("IPC Cases")}</span><span className="font-mono">{selectedDistrict.ipc.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">{t("SLL Cases")}</span><span className="font-mono">{selectedDistrict.sll.toLocaleString()}</span></div>
                      <div className="flex justify-between pt-2 border-t"><span className="text-muted-foreground font-medium">{t("Total")}</span><span className="font-mono font-bold">{(selectedDistrict.ipc + selectedDistrict.sll).toLocaleString()}</span></div>
                      <div className="flex justify-between items-center pt-2"><span className="text-muted-foreground">{t("Risk Level")}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${riskTierBg[getRiskTier(selectedDistrict)]}`}>{t(getRiskTier(selectedDistrict))}</span>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.p 
                    key="empty"
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }} 
                    exit={{ opacity: 0 }}
                    className="text-sm text-muted-foreground text-center py-4"
                  >
                    {t("Click a district on the map")}
                  </motion.p>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>

          {/* Top Risk */}
          <Card className="glass-card relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20">
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 pointer-events-none" />
            <CardHeader className="relative"><CardTitle className="font-heading text-sm flex items-center gap-1"><AlertTriangle className="h-4 w-4 text-brand-red" /> {t("Top 5 Risk")}</CardTitle></CardHeader>
            <CardContent className="space-y-2 relative">
              {top5.map((d, i) => (
                <button key={d.name} onClick={() => setSelected(d.name)} className="flex items-center justify-between w-full text-sm hover:bg-red-500/10 dark:hover:bg-red-500/20 rounded-md px-3 py-2 transition-all hover:scale-[1.02]">
                  <span><span className="text-muted-foreground mr-2">{i + 1}.</span>{t(d.name)}</span>
                  <span className="font-mono text-xs text-brand-red font-medium">{(d.ipc + d.sll).toLocaleString()}</span>
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Safest */}
          <Card className="glass-card relative overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl hover:border-brand-purple/20">
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 pointer-events-none" />
            <CardHeader className="relative"><CardTitle className="font-heading text-sm flex items-center gap-1"><Shield className="h-4 w-4 text-brand-green" /> {t("Safest 5")}</CardTitle></CardHeader>
            <CardContent className="space-y-2 relative">
              {safest5.map((d, i) => (
                <button key={d.name} onClick={() => setSelected(d.name)} className="flex items-center justify-between w-full text-sm hover:bg-emerald-500/10 dark:hover:bg-emerald-500/20 rounded-md px-3 py-2 transition-all hover:scale-[1.02]">
                  <span><span className="text-muted-foreground mr-2">{i + 1}.</span>{t(d.name)}</span>
                  <span className="font-mono text-xs text-brand-green font-medium">{(d.ipc + d.sll).toLocaleString()}</span>
                </button>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
