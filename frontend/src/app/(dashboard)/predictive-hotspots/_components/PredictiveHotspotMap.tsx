"use client";

import { useEffect, useRef, useState } from "react";
import { riskTierColors } from "@/lib/design-tokens";
import { useLanguage } from "@/components/LanguageContext";
import { Loader2, Info } from "lucide-react";
import type { WardPrediction, ViewMode } from "../types";

declare global {
  interface Window {
    L: any;
  }
}

interface PredictiveHotspotMapProps {
  predictions: WardPrediction[];
  selectedWardId: string | null;
  onSelectWard: (id: string) => void;
  viewMode: ViewMode;
  isLoading: boolean;
}

export function PredictiveHotspotMap({
  predictions,
  selectedWardId,
  onSelectWard,
  viewMode,
  isLoading,
}: PredictiveHotspotMapProps) {
  const { t } = useLanguage();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);
  const [isLeafletLoaded, setIsLeafletLoaded] = useState(false);

  // Load Leaflet dynamically
  useEffect(() => {
    if (window.L) {
      setIsLeafletLoaded(true);
      return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.async = true;
    script.onload = () => setIsLeafletLoaded(true);
    document.body.appendChild(script);
  }, []);

  // Initialize and update map
  useEffect(() => {
    if (!isLeafletLoaded || !mapContainerRef.current) return;

    const L = window.L;

    // Destroy existing map if any
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [14.0, 76.5], // Center of Karnataka approx
        zoom: 7,
        zoomControl: true,
        attributionControl: false,
      });

      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 18,
        subdomains: "abcd",
      }).addTo(map);

      mapInstanceRef.current = map;
      layerGroupRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    if (predictions.length === 0) return;

    // Add ward markers
    const bounds = L.latLngBounds();

    predictions.forEach((ward) => {
      const color = riskTierColors[ward.riskLevel];
      const isSelected = selectedWardId === ward.wardId;
      
      const radius = viewMode === "predicted"
        ? Math.max(5, (ward.riskScore / 100) * 12)
        : Math.max(5, (ward.expectedIncidents / 10) * 10);

      const marker = L.circleMarker([ward.lat, ward.lng], {
        radius: isSelected ? radius + 4 : radius,
        fillColor: color,
        color: isSelected ? "#ffffff" : color,
        weight: isSelected ? 3 : 1,
        opacity: 1,
        fillOpacity: isSelected ? 0.9 : 0.6,
      });

      bounds.extend([ward.lat, ward.lng]);

      const valueHtml = viewMode === "predicted"
        ? `Risk Score: <strong>${ward.riskScore} / 100</strong>`
        : `Expected Incidents: <strong>${ward.expectedIncidents}</strong>`;

      const popupHtml = `
        <div style="min-width: 180px; font-family: sans-serif; padding: 2px;">
          <div style="font-weight: bold; font-size: 14px; color: #a855f7; margin-bottom: 4px;">
            ${ward.wardName}
          </div>
          <div style="font-size: 11px; color: #6b7280; margin-bottom: 6px;">
            ${ward.adminArea} | ${ward.district}
          </div>
          <div style="font-size: 12px; margin-bottom: 8px;">
            ${valueHtml}
          </div>
          <div style="display: inline-block; padding: 2px 8px; border-radius: 999px; background: ${color}22; color: ${color}; font-weight: bold; font-size: 11px; border: 1px solid ${color}66;">
            ${ward.riskLevel.toUpperCase()}
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.on("click", () => {
        onSelectWard(ward.wardId);
      });
      
      // Pulse animation for emerging hotspots
      if (ward.hotspotStatus === "emerging" && viewMode === "predicted") {
        const pulseMarker = L.circleMarker([ward.lat, ward.lng], {
          radius: radius + 8,
          fillColor: "transparent",
          color: color,
          weight: 2,
          opacity: 0.5,
          dashArray: "4 4",
        });
        pulseMarker.addTo(layerGroup);
      }

      marker.addTo(layerGroup);
    });

    if (predictions.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }

  }, [isLeafletLoaded, predictions, selectedWardId, viewMode, onSelectWard]);

  return (
    <div className="relative w-full h-[500px] xl:h-[600px] bg-sidebar z-0">
      <div ref={mapContainerRef} className="w-full h-full z-0" />
      
      {isLoading && (
        <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-blue" />
        </div>
      )}

      {/* Demo Visualization Warning (Required by design) */}
      <div className="absolute top-4 left-4 z-[400] max-w-xs bg-background/90 backdrop-blur-md border border-border/50 rounded-xl p-3 shadow-lg">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-brand-blue shrink-0 mt-0.5" />
          <div className="flex flex-col">
            <span className="text-xs font-bold text-foreground">Demo Visualization</span>
            <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
              Ward geometries are approximated with point markers for demonstration.
            </span>
          </div>
        </div>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-6 right-6 z-[400] bg-background/90 backdrop-blur-md border border-border/50 rounded-xl p-3 shadow-lg flex flex-col gap-2">
        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Risk Level</span>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#10b981]" />
            <span className="text-xs text-foreground font-medium">Safe</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#f59e0b]" />
            <span className="text-xs text-foreground font-medium">Moderate</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#fb923c]" />
            <span className="text-xs text-foreground font-medium">High</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#f43f5e]" />
            <span className="text-xs text-foreground font-medium">Critical</span>
          </div>
        </div>
      </div>
    </div>
  );
}
