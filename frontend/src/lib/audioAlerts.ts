// Sentinel Grid Tactical Audio & Voice Synthesizer
// Ambulance Siren is played EXCLUSIVELY for High Risk Zones.

import { speak, stopSpeaking } from "@/lib/voice";

let audioCtx: AudioContext | null = null;
let sirenIntervalId: ReturnType<typeof setInterval> | null = null;
let isSirenActive = false;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const AudioCtor = window.AudioContext || (window as any).webkitAudioContext;
  if (!AudioCtor) return null;
  if (!audioCtx) {
    audioCtx = new AudioCtor();
  }
  if (audioCtx.state === "suspended") {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

/**
 * Trigger device vibration (Web Vibration API for mobile & supported hardware)
 */
export function triggerEmergencyVibration() {
  if (typeof window !== "undefined" && "navigator" in window && navigator.vibrate) {
    try {
      // SOS emergency vibration pattern: 300ms vibe, 100ms pause, 300ms vibe, 100ms pause, 600ms vibe
      navigator.vibrate([300, 100, 300, 100, 600]);
    } catch {
      // Ignore unsupported environments
    }
  }
}

/**
 * Play a single authentic dual-oscillator Ambulance Siren cycle ("Wee-Woo! Wee-Woo!")
 */
export function playAmbulanceCycle() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const duration = 1.0;

    // Primary High-Lo Siren Oscillator (Sawtooth with rich harmonics)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = "sawtooth";

    // Secondary Detuned Oscillator for wide acoustic chorus
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = "sine";

    // Filter to shape siren tone
    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(2200, now);

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.24, now);
    masterGain.gain.setValueAtTime(0.24, now + duration - 0.05);
    masterGain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    // Two-tone alternating frequency: High 960Hz -> Low 720Hz
    osc1.frequency.setValueAtTime(960, now);
    osc2.frequency.setValueAtTime(964, now);
    osc1.frequency.setValueAtTime(720, now + 0.45);
    osc2.frequency.setValueAtTime(724, now + 0.45);

    gain1.gain.setValueAtTime(0.20, now);
    gain2.gain.setValueAtTime(0.16, now);

    osc1.connect(gain1);
    osc2.connect(gain2);
    gain1.connect(filter);
    gain2.connect(filter);
    filter.connect(masterGain);
    masterGain.connect(ctx.destination);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + duration);
    osc2.stop(now + duration);

    // Sub-bass emergency thud
    const sub = ctx.createOscillator();
    const subGain = ctx.createGain();
    sub.type = "sine";
    sub.frequency.setValueAtTime(120, now);
    sub.frequency.exponentialRampToValueAtTime(45, now + 0.35);
    subGain.gain.setValueAtTime(0.25, now);
    subGain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);

    sub.connect(subGain);
    subGain.connect(ctx.destination);
    sub.start(now);
    sub.stop(now + 0.35);
  } catch (e) {
    console.warn("WebAudio ambulance siren error:", e);
  }
}

/**
 * Start CONTINUOUS looping ambulance siren + vibration (ONLY for High Risk Zones)
 */
export function startContinuousAmbulanceSiren(onPulse?: () => void) {
  stopContinuousSiren();
  isSirenActive = true;

  playAmbulanceCycle();
  triggerEmergencyVibration();
  onPulse?.();

  sirenIntervalId = setInterval(() => {
    if (!isSirenActive) {
      stopContinuousSiren();
      return;
    }
    playAmbulanceCycle();
    triggerEmergencyVibration();
    onPulse?.();
  }, 1050);
}

/**
 * Stop continuous siren & voice immediately
 */
export function stopContinuousSiren() {
  isSirenActive = false;
  if (sirenIntervalId) {
    clearInterval(sirenIntervalId);
    sirenIntervalId = null;
  }
  stopSpeaking();
}

export function isAmbulanceSirenPlaying(): boolean {
  return isSirenActive;
}

/**
 * Subtle soft radar chime for Medium and Normal risk zones (No siren)
 */
export function playSonarPing() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(580, now);
    osc.frequency.exponentialRampToValueAtTime(380, now + 0.25);

    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  } catch (e) {
    console.warn("Sonar sound error:", e);
  }
}

/**
 * Trigger audio alert: Ambulance Siren is used ONLY for High Risk Zones.
 */
export function announceHotspotZone(
  wardName: string,
  riskLevel: "high" | "medium" | "low" | string,
  riskScore: number,
  activeEventsCount: number,
  audioEnabled: boolean = true,
  onPulse?: () => void
) {
  if (!audioEnabled) {
    stopContinuousSiren();
    return;
  }

  const isHighRisk = riskLevel.toLowerCase() === "high";

  if (isHighRisk) {
    // ONLY HIGH RISK ZONES GET THE AMBULANCE SIREN
    startContinuousAmbulanceSiren(onPulse);
    setTimeout(() => {
      speak(
        `Emergency Alert: High risk zone in ${wardName}. Threat index: ${riskScore} percent. ${activeEventsCount} active incidents logged.`,
        "en"
      );
    }, 500);
  } else {
    // Non-high risk zones SILENCE any running siren and play gentle ping
    stopContinuousSiren();
    playSonarPing();
    setTimeout(() => {
      if (riskLevel.toLowerCase() === "medium") {
        speak(`Sector ${wardName}: Moderate risk index ${riskScore} percent.`, "en");
      } else {
        speak(`Sector ${wardName}: Normal status. Threat index ${riskScore} percent.`, "en");
      }
    }, 150);
  }
}

/**
 * Trigger sound on sensor marker tap: ambulance siren ONLY if critical SOS in high-risk zone
 */
export function announceSensorEvent(
  sensorType: string,
  wardName: string,
  priority: string,
  linkedCaseId?: string | null,
  audioEnabled: boolean = true,
  onPulse?: () => void
) {
  if (!audioEnabled) {
    stopContinuousSiren();
    return;
  }

  const isCritical = priority === "high" || sensorType === "sos_button";

  if (isCritical) {
    startContinuousAmbulanceSiren(onPulse);
  } else {
    stopContinuousSiren();
    playSonarPing();
  }

  setTimeout(() => {
    const typeLabel =
      sensorType === "sos_button"
        ? "Emergency S O S Button"
        : sensorType === "gunshot"
        ? "Gunshot acoustic alert"
        : sensorType === "anpr_hit"
        ? "Vehicle Target Match"
        : "C C T V surveillance alert";

    speak(`Alert: ${typeLabel} in ${wardName || "Bengaluru"}.`, "en");
  }, 400);
}
