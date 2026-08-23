"use client";

import React, { useRef, useEffect, useCallback } from "react";
import type { Detection } from "./types";

/* ── Color map per object class ── */
const CLASS_COLORS: Record<string, string> = {
  person: "#3B82F6",
  car: "#F59E0B",
  truck: "#F59E0B",
  motorcycle: "#10B981",
  bicycle: "#10B981",
};
const HIGHLIGHT_COLOR = "#EF4444";
const FALLBACK_COLOR = "#8B5CF6";

interface VideoCanvasSyncProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  detections: Detection[];
  highlightedTrackId: number | null;
  isImage?: boolean;
  mediaSrc?: string;
}

export function VideoCanvasSync({
  videoRef,
  detections,
  highlightedTrackId,
  isImage = false,
  mediaSrc,
}: VideoCanvasSyncProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const drawFrame = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const displayEl = isImage ? imageRef.current : videoRef.current;
    if (!displayEl) return;

    /* Sync canvas resolution to display size */
    const w = displayEl.clientWidth;
    const h = displayEl.clientHeight;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }

    ctx.clearRect(0, 0, w, h);

    const currentTime = isImage ? 0 : (videoRef.current?.currentTime ?? 0);

    /* Find detections within ±0.3s of current playback */
    const active = detections.filter(
      (d) => Math.abs(d.timestamp_seconds - currentTime) < 0.3
    );

    for (const det of active) {
      /* bbox values are normalized 0–1 fractions from the backend */
      const x = det.bbox.xmin * w;
      const y = det.bbox.ymin * h;
      const bw = (det.bbox.xmax - det.bbox.xmin) * w;
      const bh = (det.bbox.ymax - det.bbox.ymin) * h;

      const isHighlighted = highlightedTrackId !== null && det.tracking_id === highlightedTrackId;
      const color = isHighlighted
        ? HIGHLIGHT_COLOR
        : (CLASS_COLORS[det.object_class] ?? FALLBACK_COLOR);

      /* ── Draw bounding box ── */
      ctx.strokeStyle = color;
      ctx.lineWidth = isHighlighted ? 3.5 : 2.5;

      if (isHighlighted) {
        ctx.setLineDash([8, 5]);
      } else {
        ctx.setLineDash([]);
      }

      ctx.strokeRect(x, y, bw, bh);
      ctx.setLineDash([]);

      /* ── Draw label pill ── */
      const label = `${det.object_class.toUpperCase()} ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = "bold 11px sans-serif";
      const textWidth = ctx.measureText(label).width;
      const pillW = textWidth + 12;
      const pillH = 20;
      const pillX = x;
      const pillY = y - pillH - 4;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(pillX, pillY, pillW, pillH, 4);
      ctx.fill();

      ctx.fillStyle = "#FFFFFF";
      ctx.fillText(label, pillX + 6, pillY + 14);

      /* Track ID badge (if exists) */
      if (det.tracking_id !== null) {
        const tid = `#${det.tracking_id}`;
        const tidW = ctx.measureText(tid).width + 10;
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.beginPath();
        ctx.roundRect(x + bw - tidW, y - pillH - 4, tidW, pillH, 4);
        ctx.fill();
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 10px sans-serif";
        ctx.fillText(tid, x + bw - tidW + 5, pillY + 14);
      }
    }
  }, [detections, highlightedTrackId, isImage, videoRef]);

  useEffect(() => {
    const video = videoRef.current;
    if (isImage) {
      /* For images: draw once on load */
      drawFrame();
      return;
    }
    if (!video) return;

    let rafId: number;
    const loop = () => {
      drawFrame();
      rafId = requestAnimationFrame(loop);
    };

    const onPlay = () => loop();
    const onSeeked = () => { drawFrame(); };
    const onPause = () => { cancelAnimationFrame(rafId); drawFrame(); };

    video.addEventListener("play", onPlay);
    video.addEventListener("seeked", onSeeked);
    video.addEventListener("pause", onPause);

    /* Initial draw if video is paused at start */
    drawFrame();

    return () => {
      cancelAnimationFrame(rafId);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("seeked", onSeeked);
      video.removeEventListener("pause", onPause);
    };
  }, [videoRef, isImage, drawFrame]);

  /* Re-draw whenever highlighted track changes */
  useEffect(() => { drawFrame(); }, [highlightedTrackId, drawFrame]);

  return (
    <div className="relative w-full h-full">
      {isImage ? (
        <img
          ref={imageRef}
          src={mediaSrc}
          alt="Crime scene evidence"
          className="w-full h-full object-contain"
          onLoad={drawFrame}
        />
      ) : (
        <video
          ref={videoRef}
          src={mediaSrc}
          className="w-full h-full object-contain"
          controls
          muted
          crossOrigin="anonymous"
        />
      )}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
      />
    </div>
  );
}
