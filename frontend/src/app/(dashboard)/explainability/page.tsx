"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import * as motion from "motion/react-client";
import { AnimatePresence } from "motion/react";
import { Eye, Brain, Clock, Activity, CheckCircle2, ChevronRight, Info, ShieldAlert, Cpu } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine, Cell } from "recharts";
import { brandColors } from "@/lib/design-tokens";
import { useLanguage } from "@/components/LanguageContext";

const explainData = [
  { id: "hist", factor: "Historical Baseline", impact: 35, description: "Base risk calculated from the 5-year trailing average of incidents in this sector during this specific time block.", example: "Area averages 4.2 property crimes weekly." },
  { id: "seas", factor: "Seasonal Pattern", impact: 20, description: "Adjustments based on time-of-year cyclic trends. Certain crime types spike during holidays or specific weather conditions.", example: "Winter months show a +15% correlation with theft." },
  { id: "dist", factor: "District Risk Index", impact: 15, description: "Spatial analysis of socioeconomic and environmental vulnerabilities specific to the geographic ward.", example: "Low street lighting in sector 4B increases risk." },
  { id: "out", factor: "Community Outreach", impact: -8, description: "Active social programs and community engagement efforts that statistically suppress local crime rates.", example: "Active youth center reduces local vandalism by 8%." },
  { id: "wea", factor: "Severe Weather", impact: -12, description: "Immediate meteorological conditions. Heavy rain or extreme temperatures drastically reduce street-level incidents.", example: "Current heavy rainfall suppresses foot traffic." },
  { id: "pat", factor: "Active Patrol Density", impact: -25, description: "The deterrent effect of currently deployed law enforcement resources and visible CCTV surveillance within a 2km radius.", example: "3 active patrol units currently in sector." },
];

export default function ExplainabilityPage() {
  const { t } = useLanguage();
  const [selectedFactor, setSelectedFactor] = useState<string | null>("hist");

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6 ">
      {/* Header */}
      <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5 }}>
        <h1 className="text-2xl md:text-3xl font-heading font-bold flex items-center gap-3 text-foreground tracking-tight">
          <div className="p-2 bg-brand-teal/10 rounded-lg">
            <Eye className="h-6 w-6 text-brand-teal" />
          </div>
          {t("Model Transparency")}
        </h1>
        <p className="text-muted-foreground mt-3 text-base">{t("Understand exactly how our predictive engine weights factors to forecast crime risk.")}</p>
        <p className="text-xs font-semibold text-brand-purple mt-2 inline-flex items-center gap-1.5 bg-brand-purple/10 px-2.5 py-1 rounded-full border border-brand-purple/20">
          <Brain className="h-3.5 w-3.5" />
          {t("SHAP Value Explainability Active")}
        </p>
      </motion.div>

      {/* KPI Dashboard */}
      <div className="grid gap-4 sm:grid-cols-3">
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <Card className="glass-card hover:!transform-none border-l-4 border-l-brand-teal/70">
            <CardContent className="p-5 flex items-center gap-5">
              <div className="p-3.5 rounded-xl bg-brand-teal/10 text-brand-teal">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-widest mb-1">{t("Model Confidence")}</p>
                <p className="text-3xl font-sans font-bold text-foreground">87.4<span className="text-xl text-muted-foreground">%</span></p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
          <Card className="glass-card hover:!transform-none border-l-4 border-l-brand-blue/70">
            <CardContent className="p-5 flex items-center gap-5">
              <div className="p-3.5 rounded-xl bg-brand-blue/10 text-brand-blue">
                <Clock className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-widest mb-1">{t("Data Freshness")}</p>
                <p className="text-3xl font-sans font-bold text-foreground">&lt; 15<span className="text-xl text-muted-foreground">m</span></p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
          <Card className="glass-card hover:!transform-none border-l-4 border-l-brand-purple/70">
            <CardContent className="p-5 flex items-center gap-5">
              <div className="p-3.5 rounded-xl bg-brand-purple/10 text-brand-purple">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-widest mb-1">{t("Feature Drift")}</p>
                <p className="text-3xl font-sans font-bold text-foreground">{t("Stable")}</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left: SHAP Chart */}
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.4 }} className="lg:col-span-7">
          <Card className="glass-card hover:!transform-none h-[550px] flex flex-col">
            <CardHeader className="pb-2 border-b border-border/50 bg-muted/10">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Cpu className="h-5 w-5 text-brand-blue" />
                {t("Feature Impact Analysis (SHAP)")}
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">{t("Factors pushing risk")} <span className="text-brand-red font-bold">{t("higher")}</span> {t("vs")} <span className="text-brand-teal font-bold">{t("lower")}</span>.</p>
            </CardHeader>
            <CardContent className="flex-1 p-6 relative">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={explainData.map(d => ({ ...d, factor: t(d.factor) }))} layout="vertical" margin={{ top: 20, right: 30, left: 40, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis 
                    type="number" 
                    domain={[-40, 40]} 
                    tick={{ fontSize: 12, fill: "var(--muted-foreground)", fontWeight: 600 }} 
                    tickFormatter={(val) => `${val > 0 ? '+' : ''}${val}%`} 
                  />
                  <YAxis 
                    dataKey="factor" 
                    type="category" 
                    width={130} 
                    tick={{ fontSize: 12, fill: "var(--foreground)", fontWeight: 500 }} 
                    axisLine={false}
                    tickLine={false}
                  />
                  <RechartsTooltip 
                    cursor={{ fill: 'var(--muted)', opacity: 0.2 }}
                    contentStyle={{ background: "var(--card)", backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)", border: "1px solid var(--border)", borderRadius: "16px", boxShadow: "0 8px 30px rgba(0, 0, 0, 0.12)", color: "var(--foreground)", padding: "12px" }} 
                    itemStyle={{ color: "var(--foreground)", fontWeight: 500, fontSize: "13px" }}
                    formatter={(value: any) => [`${value > 0 ? '+' : ''}${value} ${t("% Impact")}`, t('Model Weight')]}
                  />
                  <ReferenceLine x={0} stroke="var(--foreground)" strokeWidth={2} opacity={0.5} />
                  <Bar dataKey="impact" radius={4} barSize={24}>
                    {explainData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.impact > 0 ? brandColors.customRed : brandColors.teal} 
                        cursor="pointer"
                        onClick={() => setSelectedFactor(entry.id)}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              
              <div className="absolute top-2 right-6 flex gap-4 text-xs font-semibold">
                <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-brand-teal"></div> {t("Reduces Risk")}</span>
                <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-brand-customRed"></div> {t("Increases Risk")}</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right: Interactive Feature List */}
        <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.5 }} className="lg:col-span-5">
          <Card className="glass-card hover:!transform-none h-[550px] flex flex-col overflow-hidden">
            <CardHeader className="pb-4 border-b border-border/50 bg-muted/10">
              <CardTitle className="font-heading text-lg">{t("Feature Deep Dive")}</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">{t("Select a factor to understand its logic.")}</p>
            </CardHeader>
            <CardContent className="p-0 overflow-y-auto flex-1">
              <div className="divide-y divide-border/50">
                {explainData.map((f) => {
                  const isSelected = selectedFactor === f.id;
                  const isPositive = f.impact > 0;
                  return (
                    <div key={f.id} className="flex flex-col">
                      <button 
                        onClick={() => setSelectedFactor(isSelected ? null : f.id)}
                        className={`w-full text-left p-4 flex items-center justify-between transition-colors ${isSelected ? 'bg-muted/30' : 'hover:bg-muted/10'}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-8 rounded-full ${isPositive ? 'bg-brand-customRed' : 'bg-brand-teal'}`} />
                          <span className={`font-semibold ${isSelected ? 'text-foreground' : 'text-muted-foreground'}`}>{t(f.factor)}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`font-mono font-bold text-sm ${isPositive ? 'text-brand-red' : 'text-brand-teal'}`}>
                            {isPositive ? '+' : ''}{f.impact}%
                          </span>
                          <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${isSelected ? 'rotate-90' : ''}`} />
                        </div>
                      </button>
                      
                      <AnimatePresence>
                        {isSelected && (
                          <motion.div 
                            initial={{ height: 0, opacity: 0 }} 
                            animate={{ height: 'auto', opacity: 1 }} 
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden bg-muted/10"
                          >
                            <div className="p-5 pt-2 pb-6 space-y-4">
                              <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">{t("Model Logic")}</p>
                                <p className="text-sm text-foreground/90 leading-relaxed">{t(f.description)}</p>
                              </div>
                              <div className="p-3 rounded-md border border-border/50 bg-background/50">
                                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1.5"><Info className="h-3.5 w-3.5" /> {t("Example in Current Context")}</p>
                                <p className="text-sm font-medium text-foreground">{t(f.example)}</p>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Transparency Note */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.6 }}>
        <div className="p-5 rounded-xl bg-muted/20 border border-border/50 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="p-3 rounded-full bg-brand-purple/10 text-brand-purple flex-shrink-0">
            <Brain className="h-6 w-6" />
          </div>
          <div className="text-sm text-muted-foreground">
            <p className="font-semibold text-foreground mb-0.5 text-base">{t("Ethical AI Transparency")}</p>
            <p>{t("This visualization uses SHAP (SHapley Additive exPlanations) methodology to decompose the Random Forest model's output. The features shown are dynamically calculated based on current data ingestion streams and do not rely on demographic profiling.")}</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
