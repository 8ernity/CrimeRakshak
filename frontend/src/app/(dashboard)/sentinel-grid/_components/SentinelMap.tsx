"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  Loader2,
  Layers,
  ShieldAlert,
  Crosshair,
  Maximize2,
  Minimize2,
  RotateCcw,
  Map as MapIcon,
  Sun,
  Moon,
  Globe,
  Volume2,
  VolumeX,
  Siren,
  Square,
  Vibrate,
  Compass,
  Building2,
  MapPin,
} from "lucide-react";
import type { SensorEvent } from "@/lib/sentinelApi";
import {
  ALL_INDIA_NATIONAL_ZONES,
  KARNATAKA_DISTRICT_ZONES,
  BENGALURU_CIRCULAR_WARDS,
  getScopeCenterAndZoom,
  type GeographicRiskZone,
} from "@/data/nationalRiskZones";
import {
  announceHotspotZone,
  announceSensorEvent,
  startContinuousAmbulanceSiren,
  stopContinuousSiren,
  triggerEmergencyVibration,
} from "@/lib/audioAlerts";

declare global {
  interface Window {
    L: any;
  }
}

interface SentinelMapProps {
  events: SensorEvent[];
  isLoading: boolean;
}

type MapTileStyle = "VOYAGER" | "STREET" | "SATELLITE" | "DARK";
type MapScope = "BENGALURU" | "KARNATAKA" | "NATIONAL";

const TILE_SERVERS: Record<MapTileStyle, { url: string; subdomains?: string; maxZoom: number; label: string }> = {
  VOYAGER: {
    url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    subdomains: "abcd",
    maxZoom: 19,
    label: "Street View",
  },
  STREET: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    subdomains: "abc",
    maxZoom: 19,
    label: "OpenStreetMap",
  },
  SATELLITE: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 18,
    label: "Satellite",
  },
  DARK: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    subdomains: "abcd",
    maxZoom: 19,
    label: "Dark GIS",
  },
};

const SENSOR_COLORS: Record<string, string> = {
  cctv_alert: "#2563eb",  // vibrant blue
  anpr_hit:   "#d97706",  // amber
  sos_button: "#dc2626",  // crimson red
  gunshot:    "#7c3aed",  // purple
};

const CIRCLE_RISK_STYLES = {
  high: {
    fillColor: "#ef4444",
    fillOpacity: 0.32,
    color: "#dc2626",
    weight: 2.5,
    opacity: 0.95,
  },
  medium: {
    fillColor: "#f59e0b",
    fillOpacity: 0.25,
    color: "#d97706",
    weight: 2,
    opacity: 0.90,
  },
  low: {
    fillColor: "#0284c7",
    fillOpacity: 0.18,
    color: "#0369a1",
    weight: 1.8,
    opacity: 0.80,
  },
} as const;

const TYPE_LABELS: Record<string, string> = {
  cctv_alert: "CCTV Alert",
  anpr_hit:   "ANPR Hit",
  sos_button: "SOS Button",
  gunshot:    "Gunshot Detection",
};

function formatTs(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

export function SentinelMap({ events, isLoading }: SentinelMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapWrapperRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  const circularZonesLayerRef = useRef<any>(null);
  const eventsLayerRef = useRef<any>(null);

  const [leafletReady, setLeafletReady] = useState(false);
  const [mapScope, setMapScope] = useState<MapScope>("NATIONAL");
  const [tileStyle, setTileStyle] = useState<MapTileStyle>("VOYAGER");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showLayerMenu, setShowLayerMenu] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [activeSirenAlert, setActiveSirenAlert] = useState<{
    title: string;
    ward: string;
    riskScore: number;
    activeCount: number;
  } | null>(null);
  const [isVibrating, setIsVibrating] = useState(false);

  // Clean up audio siren on unmount
  useEffect(() => {
    return () => {
      stopContinuousSiren();
    };
  }, []);

  // Count active events per ward
  const eventsPerWard = useMemo(() => {
    const counts: Record<string, number> = {};
    events.forEach((ev) => {
      if (ev.ward_id) {
        counts[ev.ward_id] = (counts[ev.ward_id] || 0) + 1;
      }
    });
    return counts;
  }, [events]);

  // Dynamically load Leaflet
  useEffect(() => {
    if (window.L) {
      setLeafletReady(true);
      return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.async = true;
    script.onload = () => setLeafletReady(true);
    document.body.appendChild(script);
  }, []);

  // Initialize Map
  useEffect(() => {
    if (!leafletReady || !containerRef.current || mapRef.current) return;
    const L = window.L;

    const initial = getScopeCenterAndZoom(mapScope);

    const map = L.map(containerRef.current, {
      center: initial.center,
      zoom: initial.zoom,
      minZoom: 4,
      maxZoom: 18,
      zoomControl: false,
      attributionControl: false,
    });

    // Custom positioned zoom control
    L.control.zoom({ position: "topleft" }).addTo(map);

    // Initial tile layer
    const initialConfig = TILE_SERVERS[tileStyle];
    tileLayerRef.current = L.tileLayer(initialConfig.url, {
      maxZoom: initialConfig.maxZoom,
      subdomains: initialConfig.subdomains || "abc",
    }).addTo(map);

    // Layer groups for clean layering: Circular zones below, Sensor Points above
    circularZonesLayerRef.current = L.layerGroup().addTo(map);
    eventsLayerRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;

    // Inject custom tooltip & popup CSS
    const styleEl = document.createElement("style");
    styleEl.id = "sentinel-gis-map-styles";
    styleEl.innerHTML = `
      .circle-zone-label {
        background: rgba(15, 23, 42, 0.92) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 999px !important;
        padding: 3px 9px !important;
        box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.4) !important;
        color: #ffffff !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        pointer-events: none !important;
        white-space: nowrap !important;
      }
      .circle-zone-label::before {
        display: none !important;
      }
      .leaflet-popup-content-wrapper {
        background: rgba(15, 23, 42, 0.96) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        color: #f8fafc !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.55) !important;
        padding: 4px !important;
      }
      .leaflet-popup-tip {
        background: rgba(15, 23, 42, 0.96) !important;
      }
      .leaflet-popup-close-button {
        color: #94a3b8 !important;
        padding: 8px !important;
      }
      .leaflet-popup-close-button:hover {
        color: #ffffff !important;
      }
      @keyframes siren-strobe {
        0%, 100% { box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.5), 0 0 30px rgba(239, 68, 68, 0.6); }
        50% { box-shadow: inset 0 0 70px rgba(239, 68, 68, 0.8), 0 0 50px rgba(239, 68, 68, 0.9); }
      }
      .siren-active-strobe {
        animation: siren-strobe 1s infinite alternate ease-in-out;
      }
    `;
    if (!document.getElementById("sentinel-gis-map-styles")) {
      document.head.appendChild(styleEl);
    }

    setTimeout(() => {
      if (map?.invalidateSize) {
        map.invalidateSize();
      }
    }, 200);
  }, [leafletReady]);

  // Switch Tile Layer when style changes
  useEffect(() => {
    if (!mapRef.current || !window.L) return;
    const L = window.L;
    const map = mapRef.current;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const config = TILE_SERVERS[tileStyle];
    tileLayerRef.current = L.tileLayer(config.url, {
      maxZoom: config.maxZoom,
      subdomains: config.subdomains || "abc",
    }).addTo(map);

    if (tileLayerRef.current?.bringToBack) {
      tileLayerRef.current.bringToBack();
    }
  }, [tileStyle]);

  // Handle Scope Change (Pan/Zoom map to target scope)
  const handleScopeChange = useCallback((newScope: MapScope) => {
    setMapScope(newScope);
    if (!mapRef.current) return;
    const { center, zoom } = getScopeCenterAndZoom(newScope);
    mapRef.current.setView(center, zoom, { animate: true, duration: 1.2 });
  }, []);

  // Render Round / Circle Crime Zones for selected scope
  useEffect(() => {
    if (!leafletReady || !mapRef.current || !circularZonesLayerRef.current || !window.L) return;
    const L = window.L;
    const zonesGroup = circularZonesLayerRef.current;
    zonesGroup.clearLayers();

    try {
      const activeZoneList: GeographicRiskZone[] =
        mapScope === "NATIONAL"
          ? ALL_INDIA_NATIONAL_ZONES
          : mapScope === "KARNATAKA"
          ? KARNATAKA_DISTRICT_ZONES
          : BENGALURU_CIRCULAR_WARDS;

      activeZoneList.forEach((zone: GeographicRiskZone) => {
        const isHigh = zone.risk_level === "high";
        const style = CIRCLE_RISK_STYLES[zone.risk_level] || CIRCLE_RISK_STYLES.low;

        // 1. Pulsing Outer Radar Ring for High Risk Zones
        if (isHigh) {
          L.circle([zone.lat, zone.lng], {
            radius: zone.radiusMeters * 1.25,
            fillColor: "transparent",
            color: "#ef4444",
            weight: 1.5,
            opacity: 0.5,
            dashArray: "6 4",
            interactive: false,
          }).addTo(zonesGroup);
        }

        // 2. Main High-Visibility Round Crime Zone Circle
        const circleZone = L.circle([zone.lat, zone.lng], {
          radius: zone.radiusMeters,
          ...style,
        });

        // Centered Round Badge Label
        circleZone.bindTooltip(zone.name, {
          permanent: true,
          direction: "center",
          className: "circle-zone-label",
        });

        // Hover & Click Interactions
        circleZone.on({
          mouseover: (e: any) => {
            e.target.setStyle({
              weight: 4,
              color: "#ffffff",
              fillOpacity: isHigh ? 0.48 : 0.38,
            });
          },
          mouseout: (e: any) => {
            e.target.setStyle(style);
          },
          click: (e: any) => {
            if (mapRef.current) {
              mapRef.current.setView([zone.lat, zone.lng], mapScope === "NATIONAL" ? 9 : 13, {
                animate: true,
              });
            }

            if (isHigh) {
              setActiveSirenAlert({
                title: "HIGH-RISK AMBULANCE SIREN ACTIVE",
                ward: zone.name,
                riskScore: zone.risk_score,
                activeCount: zone.active_sensors,
              });
              setIsVibrating(true);
            } else {
              setActiveSirenAlert(null);
              setIsVibrating(false);
            }

            announceHotspotZone(
              zone.name,
              zone.risk_level,
              zone.risk_score,
              zone.active_sensors,
              audioEnabled,
              () => {
                setIsVibrating((v) => !v);
              }
            );
          },
        });

        // Rich Circular Zone Popup
        const badgeBg = isHigh ? "#dc2626" : zone.risk_level === "medium" ? "#d97706" : "#0284c7";
        const popupHtml = `
          <div style="min-width: 230px; font-family: system-ui, -apple-system, sans-serif; padding: 4px 6px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 6px; gap: 8px;">
              <span style="font-weight: 800; font-size: 14px; color: #ffffff;">${zone.name}</span>
              <span style="font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 999px; background: ${badgeBg}; color: #ffffff; letter-spacing: 0.05em;">
                ${zone.risk_level.toUpperCase()} RISK
              </span>
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
              Region: <strong style="color: #e2e8f0;">${zone.stateOrRegion}</strong> · Threat Index: <strong style="color: #38bdf8;">${zone.risk_score}/100</strong>
            </div>
            ${zone.ipc_cases ? `<div style="font-size: 11px; color: #cbd5e1; margin-bottom: 6px;">Annual IPC Cases: <strong style="color:#ffffff;">${zone.ipc_cases.toLocaleString()}</strong></div>` : ""}
            <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 10px; font-size: 11px; display:flex; justify-content:space-between; align-items:center;">
              <span style="color: #cbd5e1;">Live Grid Telemetry:</span>
              <strong style="color: ${isHigh ? '#f87171' : '#38bdf8'}; font-size: 13px;">${zone.active_sensors} Units Online</strong>
            </div>
          </div>
        `;

        circleZone.bindPopup(popupHtml);
        circleZone.addTo(zonesGroup);

        // 3. Center Target Core Point
        const centerPoint = L.circleMarker([zone.lat, zone.lng], {
          radius: isHigh ? 6 : 5,
          fillColor: isHigh ? "#ef4444" : zone.risk_level === "medium" ? "#f59e0b" : "#0284c7",
          color: "#ffffff",
          weight: 2,
          opacity: 1,
          fillOpacity: 1,
          interactive: false,
        });
        centerPoint.addTo(zonesGroup);
      });
    } catch (err) {
      console.warn("SentinelMap: Failed rendering circular zones", err);
    }
  }, [leafletReady, mapScope, eventsPerWard, audioEnabled]);

  // Render Sensor Event Markers (Top Layer)
  useEffect(() => {
    if (!leafletReady || !mapRef.current || !eventsLayerRef.current || !window.L) return;
    const L = window.L;
    const eventsGroup = eventsLayerRef.current;
    eventsGroup.clearLayers();

    // Show individual sensor events
    events.forEach((ev) => {
      const fillColor = SENSOR_COLORS[ev.sensor_type] ?? "#2563eb";
      const isHigh = ev.priority === "high" || ev.sensor_type === "sos_button";
      const radius = isHigh ? 9 : 7;

      if (isHigh) {
        L.circleMarker([ev.lat, ev.lng], {
          radius: radius + 8,
          fillColor: "transparent",
          color: fillColor,
          weight: 2,
          opacity: 0.7,
          dashArray: "4 3",
          interactive: false,
        }).addTo(eventsGroup);
      }

      const marker = L.circleMarker([ev.lat, ev.lng], {
        radius,
        fillColor,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 1,
      });

      marker.on("click", () => {
        if (isHigh) {
          setActiveSirenAlert({
            title: "EMERGENCY SENSOR ALARM",
            ward: ev.ward_name || "Bengaluru",
            riskScore: Math.round(ev.confidence * 100),
            activeCount: 1,
          });
          setIsVibrating(true);
        }
        announceSensorEvent(ev.sensor_type, ev.ward_name, ev.priority, ev.linked_case_id, audioEnabled, () => {
          setIsVibrating((v) => !v);
        });
      });

      const caseLink = ev.linked_case_id
        ? `<div style="margin-top:8px; padding:4px 10px; border-radius:999px; background:rgba(124,58,237,0.25); border:1px solid rgba(167,139,250,0.5); display:inline-flex; align-items:center; gap:4px; font-size:10px; color:#c084fc; font-weight:800;">
            🔗 Dossier: ${ev.linked_case_id}
          </div>`
        : "";

      const popupHtml = `
        <div style="min-width: 220px; font-family: system-ui, -apple-system, sans-serif; padding: 4px 6px;">
          <div style="display:flex; align-items:center; gap:6px; margin-bottom: 6px;">
            <span style="display:inline-block; width:10px; height:10px; border-radius:999px; background:${fillColor}; box-shadow: 0 0 8px ${fillColor};"></span>
            <span style="font-weight: 800; font-size: 13px; color: #ffffff;">
              ${TYPE_LABELS[ev.sensor_type] ?? ev.sensor_type}
            </span>
          </div>
          <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 6px;">
            Location: <strong style="color:#ffffff;">${ev.ward_name || "Bengaluru City"}</strong> ${ev.district ? `(${ev.district})` : ""}
          </div>
          <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
            Confidence: <strong style="color:#38bdf8;">${Math.round(ev.confidence * 100)}%</strong>
          </div>
          <div style="font-size: 10px; color: #64748b; font-family: monospace;">
            ⏱ Detected: ${formatTs(ev.timestamp)}
          </div>
          ${caseLink}
        </div>
      `;

      marker.bindPopup(popupHtml, { offset: [0, -6] });
      marker.addTo(eventsGroup);
    });
  }, [leafletReady, events, audioEnabled]);

  // Recenter map handler
  const handleRecenter = useCallback(() => {
    if (!mapRef.current) return;
    const { center, zoom } = getScopeCenterAndZoom(mapScope);
    mapRef.current.setView(center, zoom, { animate: true });
  }, [mapScope]);

  // Fullscreen toggle handler
  const toggleFullscreen = useCallback(() => {
    if (!mapWrapperRef.current) return;
    if (!isFullscreen) {
      if (mapWrapperRef.current.requestFullscreen) {
        mapWrapperRef.current.requestFullscreen().catch(() => {});
      }
      setIsFullscreen(true);
    } else {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      setIsFullscreen(false);
    }
    setTimeout(() => {
      mapRef.current?.invalidateSize();
    }, 200);
  }, [isFullscreen]);

  // Stop siren function
  const handleSilenceSiren = useCallback(() => {
    stopContinuousSiren();
    setActiveSirenAlert(null);
    setIsVibrating(false);
  }, []);

  return (
    <div
      ref={mapWrapperRef}
      className={`relative w-full ${isFullscreen ? "h-screen" : "h-[540px] xl:h-[640px]"} bg-slate-950 overflow-hidden flex flex-col ${
        activeSirenAlert ? "siren-active-strobe" : ""
      }`}
    >
      {/* Map Container */}
      <div ref={containerRef} className="w-full h-full z-0" />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-slate-950/40 backdrop-blur-xs z-10 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      )}

      {/* CONTINUOUS AMBULANCE SIREN & VIBRATION LIVE ALERT BANNER */}
      {activeSirenAlert && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[500] px-5 py-2.5 rounded-2xl bg-red-600/95 text-white font-extrabold text-xs shadow-[0_0_30px_rgba(239,68,68,0.8)] border-2 border-red-400 backdrop-blur-md flex items-center gap-3 animate-pulse">
          <div className="p-1.5 rounded-xl bg-white/20 animate-spin">
            <Siren className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] tracking-widest text-red-200 uppercase flex items-center gap-1">
              <Vibrate className="h-3 w-3 animate-bounce" /> HIGH-RISK AMBULANCE SIREN & VIBRATION ACTIVE
            </span>
            <span className="text-sm font-black text-white">
              {activeSirenAlert.ward} — Threat Score {activeSirenAlert.riskScore}%
            </span>
          </div>
          <button
            onClick={handleSilenceSiren}
            className="ml-3 px-3 py-1.5 rounded-xl bg-black/40 hover:bg-black/70 text-white font-bold text-xs border border-white/30 flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:scale-105"
            title="Silence emergency ambulance siren"
          >
            <Square className="h-3.5 w-3.5 fill-white" />
            <span>SILENCE</span>
          </button>
        </div>
      )}

      {/* Top Controls Toolbar */}
      <div className="absolute top-4 right-4 z-[400] flex flex-wrap items-center gap-2">
        {/* GEOGRAPHIC SCOPE SELECTOR TABS (All-India / Karnataka / Bengaluru) */}
        <div className="p-1 rounded-xl bg-slate-900/95 border border-slate-700/80 shadow-2xl backdrop-blur-md flex items-center gap-1">
          <button
            onClick={() => handleScopeChange("NATIONAL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              mapScope === "NATIONAL"
                ? "bg-blue-600 text-white shadow-md"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="View All-India National Metropolitan Round Crime Zones"
          >
            <Compass className="h-3.5 w-3.5 text-amber-400" />
            <span>All India</span>
          </button>

          <button
            onClick={() => handleScopeChange("KARNATAKA")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              mapScope === "KARNATAKA"
                ? "bg-blue-600 text-white shadow-md"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="View Karnataka State Police District Zones"
          >
            <Building2 className="h-3.5 w-3.5 text-emerald-400" />
            <span>Karnataka</span>
          </button>

          <button
            onClick={() => handleScopeChange("BENGALURU")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              mapScope === "BENGALURU"
                ? "bg-blue-600 text-white shadow-md"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            title="View Bengaluru Metropolitan Municipal Wards"
          >
            <MapPin className="h-3.5 w-3.5 text-sky-400" />
            <span>Bengaluru Wards</span>
          </button>
        </div>

        {/* High-Risk Siren Indicator / Toggle */}
        <button
          onClick={() => {
            if (activeSirenAlert) {
              handleSilenceSiren();
            } else {
              setActiveSirenAlert({
                title: "HIGH-RISK AMBULANCE SIREN ACTIVE",
                ward: mapScope === "NATIONAL" ? "Delhi NCR" : mapScope === "KARNATAKA" ? "Kalaburagi Dist" : "Jayanagar",
                riskScore: mapScope === "NATIONAL" ? 95 : mapScope === "KARNATAKA" ? 88 : 91,
                activeCount: 4,
              });
              startContinuousAmbulanceSiren();
              triggerEmergencyVibration();
            }
          }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border shadow-lg text-xs font-bold backdrop-blur-md transition-all cursor-pointer ${
            activeSirenAlert
              ? "bg-red-600 text-white border-red-400 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.7)]"
              : "bg-slate-900/90 hover:bg-slate-800 text-rose-300 border-rose-900/50"
          }`}
          title={activeSirenAlert ? "Click to Silence Siren" : "High-Risk Zone Ambulance Siren"}
        >
          <Siren className={`h-4 w-4 ${activeSirenAlert ? "text-white animate-spin" : "text-rose-400"}`} />
          <span>{activeSirenAlert ? "SIREN ACTIVE" : "High-Risk Siren"}</span>
        </button>

        {/* Global Audio Toggle */}
        <button
          onClick={() => {
            const next = !audioEnabled;
            setAudioEnabled(next);
            if (!next) {
              handleSilenceSiren();
            }
          }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border shadow-lg text-xs font-semibold backdrop-blur-md transition-all cursor-pointer ${
            audioEnabled
              ? "bg-blue-600/90 text-white border-blue-500"
              : "bg-slate-900/90 hover:bg-slate-800 text-slate-400 border-slate-700/80"
          }`}
          title={audioEnabled ? "Audio Alerts Enabled (Tap to Mute)" : "Audio Alerts Muted (Tap to Enable)"}
        >
          {audioEnabled ? <Volume2 className="h-4 w-4 text-white" /> : <VolumeX className="h-4 w-4" />}
          <span>{audioEnabled ? "Sound ON" : "Muted"}</span>
        </button>

        {/* Layer Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowLayerMenu((prev) => !prev)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 shadow-lg text-xs font-semibold backdrop-blur-md transition-all cursor-pointer"
            title="Switch Map Layer"
          >
            <Layers className="h-4 w-4 text-blue-400" />
            <span>{TILE_SERVERS[tileStyle].label}</span>
          </button>

          {showLayerMenu && (
            <div className="absolute right-0 top-11 w-44 bg-slate-900/95 border border-slate-700/90 rounded-xl shadow-2xl p-1.5 backdrop-blur-xl flex flex-col gap-1 z-50">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1">
                Base Map Style
              </span>
              <button
                onClick={() => { setTileStyle("VOYAGER"); setShowLayerMenu(false); }}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors cursor-pointer ${
                  tileStyle === "VOYAGER" ? "bg-blue-600 text-white font-bold" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <Sun className="h-3.5 w-3.5 text-amber-400" />
                <span>Clear Street View</span>
              </button>

              <button
                onClick={() => { setTileStyle("SATELLITE"); setShowLayerMenu(false); }}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors cursor-pointer ${
                  tileStyle === "SATELLITE" ? "bg-blue-600 text-white font-bold" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <Globe className="h-3.5 w-3.5 text-emerald-400" />
                <span>Satellite / Hybrid</span>
              </button>

              <button
                onClick={() => { setTileStyle("DARK"); setShowLayerMenu(false); }}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors cursor-pointer ${
                  tileStyle === "DARK" ? "bg-blue-600 text-white font-bold" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <Moon className="h-3.5 w-3.5 text-indigo-400" />
                <span>Dark GIS View</span>
              </button>

              <button
                onClick={() => { setTileStyle("STREET"); setShowLayerMenu(false); }}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors cursor-pointer ${
                  tileStyle === "STREET" ? "bg-blue-600 text-white font-bold" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <MapIcon className="h-3.5 w-3.5 text-sky-400" />
                <span>OpenStreetMap</span>
              </button>
            </div>
          )}
        </div>

        {/* Recenter Button */}
        <button
          onClick={handleRecenter}
          className="p-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 shadow-lg backdrop-blur-md transition-all cursor-pointer"
          title="Recenter Map View"
        >
          <RotateCcw className="h-4 w-4" />
        </button>

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          className="p-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 shadow-lg backdrop-blur-md transition-all cursor-pointer"
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Map"}
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
      </div>

      {/* Bottom-Right Unified Legend */}
      <div className="absolute bottom-5 right-5 z-[400] bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-xl p-3.5 shadow-2xl flex flex-col gap-3 min-w-[210px]">
        {/* Ward / District Risk Section */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <ShieldAlert className="h-3 w-3 text-slate-400" /> Circular Crime Zones
          </span>
          <div className="grid grid-cols-3 gap-1.5 pt-0.5">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-rose-500/15 border border-rose-500/30">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
              <span className="text-[10px] text-rose-300 font-bold">High</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/15 border border-amber-500/30">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
              <span className="text-[10px] text-amber-300 font-bold">Medium</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-sky-500/15 border border-sky-500/30">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 shrink-0" />
              <span className="text-[10px] text-sky-300 font-bold">Normal</span>
            </div>
          </div>
        </div>

        <div className="h-px bg-slate-800 -mx-1" />

        {/* Sensor Type Section */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Crosshair className="h-3 w-3 text-slate-400" /> Live Grid Sensors
          </span>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 pt-0.5">
            {Object.entries(SENSOR_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 rounded-full ring-1 ring-white/60 shrink-0 shadow-xs"
                  style={{ backgroundColor: color }}
                />
                <span className="text-[11px] text-slate-300 font-medium truncate">
                  {TYPE_LABELS[type]?.split(" ")[0]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
