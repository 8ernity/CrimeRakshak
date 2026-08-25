"use client";

import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSidebar } from "./SidebarContext";
import { useState, useEffect } from "react";
import { useLanguage } from "@/components/LanguageContext";
import QRCode from "react-qr-code";
import { X, Smartphone, Shield, Zap, Activity } from "lucide-react";

const pageTitles: Record<string, string> = {
  "/overview": "Overview",
  "/heatmap": "AI Crime Hotspot Map",
  "/district": "District Analysis",
  "/crime-types": "Crime Categories",
  "/trends": "Trend Analysis",
  "/vulnerable": "Vulnerable Groups",
  "/ai-prediction": "AI Prediction Engine",
  "/ai-assistant": "AI Copilot Chat",
  "/alerts": "Alert Center",
  "/simulator": "Digital Twin Simulator",
  "/explainability": "AI Explainability",
  "/network": "Criminal Network",
  "/profiling": "Offender Profiles",
  "/case-intel": "Case Intelligence",
  "/financial": "Financial Trails",
  "/governance": "Governance",
  "/settings": "Settings",
};

export function Header() {
  const pathname = usePathname();

  const { setMobileOpen } = useSidebar();
  const [mounted, setMounted] = useState(false);
  const { lang, setLang, t } = useLanguage();
  const [isAppModalOpen, setIsAppModalOpen] = useState(false);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);


  return (
    <header className="w-full flex items-center justify-between px-4 md:px-6 pt-4 lg:pt-6 pb-2 pointer-events-none">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          suppressHydrationWarning
          className="lg:hidden pointer-events-auto bg-background/50 backdrop-blur-sm border border-border/50"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center gap-4 pointer-events-auto">
        <button 
          className="buttonupgrade hidden md:flex items-center shadow-lg"
          onClick={() => setIsAppModalOpen(true)}
        >
          <svg viewBox="0 0 36 24" xmlns="http://www.w3.org/2000/svg">
            <path d="m18 0 8 12 10-8-4 20H4L0 4l10 8 8-12z"></path>
          </svg>
          Get Android App
        </button>

        <div className="flex items-center gap-2 bg-background/50 backdrop-blur-md rounded-full p-1.5 border border-border/50 shadow-sm">
          {/* Language toggle sliding button */}
          {mounted && (
            <div 
              className="relative flex items-center bg-muted/80 rounded-full p-1 cursor-pointer select-none border border-border/50 ml-1 h-[36px]"
              onClick={() => setLang(lang === "EN" ? "KA" : "EN")}
              style={{ width: "112px" }}
            >
              <div 
                className={cn(
                  "absolute top-1 left-1 h-[26px] w-[50px] rounded-full shadow-md transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] border border-transparent",
                  lang === "EN" 
                    ? "translate-x-0 bg-brand-purple text-white" 
                    : "translate-x-[52px] bg-brand-cyan text-white"
                )}
              />
              <div className={cn("relative z-10 w-[50px] text-center text-xs font-extrabold tracking-wider transition-colors duration-300 flex items-center justify-center gap-1.5", lang === "EN" ? "text-white drop-shadow-sm" : "text-muted-foreground hover:text-foreground/80")}>
                <span className="text-[14px]">A</span> EN
              </div>
              <div className={cn("relative z-10 w-[50px] ml-[2px] text-center text-[11px] font-extrabold tracking-wider transition-colors duration-300 flex items-center justify-center gap-1.5", lang === "KA" ? "text-white drop-shadow-sm" : "text-muted-foreground hover:text-foreground/80")}>
                <span className="text-[14px]">ಅ</span> KA
              </div>
            </div>
          )}
        </div>
      </div>

      {isAppModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200 pointer-events-auto">
          <div className="bg-card border border-border shadow-2xl rounded-2xl w-full max-w-4xl overflow-hidden flex flex-col md:flex-row relative">
            <Button 
              variant="ghost" 
              size="icon" 
              className="absolute top-4 right-4 z-10 text-muted-foreground hover:text-foreground hover:bg-muted" 
              onClick={() => setIsAppModalOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>

            {/* Left Side - QR Code */}
            <div className="w-full md:w-2/5 bg-muted/30 p-8 flex flex-col items-center justify-center border-r border-border/50">
              <h3 className="text-xl font-bold mb-2">Scan to Download</h3>
              <p className="text-sm text-muted-foreground text-center mb-8">
                Get the CrimeRakshak mobile app for field operations
              </p>
              
              <div className="bg-white p-4 rounded-xl shadow-sm mb-6 flex items-center justify-center">
                <QRCode 
                  value="https://crimerakshak-backend-50044347084.development.catalystappsail.in/app-release.apk" 
                  size={200}
                  level="H"
                />
              </div>
              
              <a 
                href="https://crimerakshak-backend-50044347084.development.catalystappsail.in/app-release.apk" 
                className="text-brand-cyan hover:underline text-sm font-medium flex items-center gap-1.5"
              >
                Direct Download Link
              </a>
            </div>

            {/* Right Side - Features */}
            <div className="w-full md:w-3/5 p-8 flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-foreground mb-6">CrimeRakshak Mobile</h2>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="bg-brand-purple/10 p-3 rounded-lg h-fit text-brand-purple">
                    <Activity className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">Real-time Analytics</h4>
                    <p className="text-sm text-muted-foreground mt-1">Access interactive crime charts, IPC breakdowns, and dynamic dashboard metrics directly on the go.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="bg-brand-cyan/10 p-3 rounded-lg h-fit text-brand-cyan">
                    <Zap className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">AI Copilot Integration</h4>
                    <p className="text-sm text-muted-foreground mt-1">Query the database using natural language and receive immediate AI-driven insights in the field.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="bg-green-500/10 p-3 rounded-lg h-fit text-green-500">
                    <Shield className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">Secure Field Access</h4>
                    <p className="text-sm text-muted-foreground mt-1">Encrypted, role-based access ensuring that sensitive jurisdictional data remains secure during patrol.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
