"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import "@/app/auth.css";

// ── Input recipe (shared across all fields) ──
const inputClass =
  "w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-[#4B4DD9] transition-colors";

interface UniversalAuthProps {
  defaultIsSignUp?: boolean;
}

export default function UniversalAuth({
  defaultIsSignUp = false,
}: UniversalAuthProps) {
  const pathname = usePathname();
  const [isSignUp, setIsSignUp] = useState(defaultIsSignUp);

  // ── Login state ──
  const [identifier, setIdentifier] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");

  // ── Signup state ──
  const [formData, setFormData] = useState({
    displayName: "",
    email: "",
    phone: "",
    department: "",
    password: "",
    confirmPassword: "",
  });
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [showSignupConfirmPassword, setShowSignupConfirmPassword] =
    useState(false);
  const [signupLoading, setSignupLoading] = useState(false);
  const [signupError, setSignupError] = useState("");

  // ── Slow-network UX (5s timeout → stage 2) ──
  const [showLongLoading, setShowLongLoading] = useState(false);
  useEffect(() => {
    let t: NodeJS.Timeout;
    if (loginLoading || signupLoading) {
      t = setTimeout(() => setShowLongLoading(true), 5000);
    }
    return () => {
      clearTimeout(t);
      setShowLongLoading(false);
    };
  }, [loginLoading, signupLoading]);

  // ── URL ↔ panel sync ──
  useEffect(() => {
    if (isSignUp !== (pathname === "/signup")) {
      setIsSignUp(pathname === "/signup");
    }
  }, [pathname, isSignUp]);

  const togglePanel = (toSignUp: boolean) => {
    setIsSignUp(toSignUp);
    window.history.pushState(null, "", toSignUp ? "/signup" : "/login");
  };

  // ── Form helpers ──
  const updateFormData = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // ── Submit: Login ──
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError("");
    // Simulate a brief loading state then redirect
    setTimeout(() => {
      window.location.href = "/overview";
    }, 800);
  };

  // ── Submit: Signup ──
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignupLoading(true);
    setSignupError("");

    if (formData.password !== formData.confirmPassword) {
      setSignupError("Passwords do not match");
      setSignupLoading(false);
      return;
    }

    // Simulate a brief loading state then redirect
    setTimeout(() => {
      window.location.href = "/overview";
    }, 800);
  };

  return (
    <div className="auth-page-bg auth-mesh-bg relative">
      {/* ═══════════════════════════════════════════
          Loading Overlay — Stage 1 (instant spinner)
          ═══════════════════════════════════════════ */}
      {(loginLoading || signupLoading) && !showLongLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-md transition-all">
          <div className="relative flex flex-col items-center justify-center">
            <div className="relative flex items-center justify-center w-32 h-32 mb-8">
              <div className="absolute inset-0 rounded-full border-4 border-[#4B4DD9]/20 border-t-[#4B4DD9] animate-spin drop-shadow-[0_0_15px_rgba(75,77,217,0.5)]" />
              <div className="absolute inset-4 rounded-full border-4 border-purple-500/20 border-b-purple-500 animate-[spin_1.5s_linear_reverse_infinite] drop-shadow-[0_0_15px_rgba(168,85,247,0.5)]" />
            </div>
            <div className="flex flex-col items-center">
              <span className="font-extrabold text-white text-lg tracking-[0.2em] uppercase animate-pulse">
                {loginLoading ? "Authenticating" : "Initializing"}
              </span>
              <div className="flex gap-1.5 mt-3">
                <span
                  className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════
          Loading Overlay — Stage 2 ("taking a while")
          ═══════════════════════════════════════════ */}
      {showLongLoading && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 transition-all">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden flex flex-col p-6 animate-in zoom-in-95 duration-200 border-t-4 border-[#4B4DD9]">
            <div className="flex flex-col items-center text-center gap-4">
              <Loader2
                size={40}
                className="animate-spin text-[#4B4DD9] shrink-0"
              />
              <div>
                <p className="font-bold text-lg text-slate-800">
                  Please wait...
                </p>
                <p className="text-sm mt-1 text-slate-600">
                  This is taking longer than usual. Hang tight!
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════
          The Card
          ═══════════════════════════════════════════ */}
      <div className="auth-wrapper">
        <div
          className={`auth-container ${isSignUp ? "right-panel-active" : ""}`}
        >
          {/* ─── Sign Up Form (DOM-first) ─── */}
          <div className="auth-form-container sign-up-container">
            <form onSubmit={handleSignup} className="space-y-4">
              <h1
                className="text-3xl font-bold text-center text-gray-900 mb-2 italic"
                style={{ fontFamily: '"Playfair Display", serif' }}
              >
                Create Account
              </h1>

              {signupError && (
                <div className="p-2 text-sm rounded-lg border font-medium text-red-500 bg-red-50 border-red-200">
                  {signupError}
                </div>
              )}

              <input
                required
                name="displayName"
                type="text"
                placeholder="Name"
                value={formData.displayName}
                onChange={updateFormData}
                className={inputClass}
              />
              <input
                required
                name="email"
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={updateFormData}
                className={inputClass}
              />
              <input
                name="phone"
                type="tel"
                placeholder="Phone"
                value={formData.phone}
                onChange={updateFormData}
                className={inputClass}
              />
              <input
                required
                name="department"
                type="text"
                placeholder="Department"
                value={formData.department}
                onChange={updateFormData}
                className={inputClass}
              />

              {/* Password + Confirm — side by side */}
              <div className="flex gap-2">
                <div className="relative w-full">
                  <input
                    required
                    name="password"
                    type={showSignupPassword ? "text" : "password"}
                    placeholder="Password"
                    value={formData.password}
                    onChange={updateFormData}
                    className={inputClass}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSignupPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#4B4DD9] transition-colors"
                  >
                    {showSignupPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>
                <div className="relative w-full">
                  <input
                    required
                    name="confirmPassword"
                    type={showSignupConfirmPassword ? "text" : "password"}
                    placeholder="Confirm"
                    value={formData.confirmPassword}
                    onChange={updateFormData}
                    className={inputClass}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSignupConfirmPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#4B4DD9] transition-colors"
                  >
                    {showSignupConfirmPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={signupLoading}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#4B4DD9] px-4 py-3 font-semibold text-white hover:bg-[#3B3DB9] transition-all disabled:bg-[#3B3DB9] disabled:cursor-wait"
              >
                {signupLoading ? "Creating Account..." : "Sign Up"}
              </button>

              {/* Mobile-only switch link */}
              <div className="mt-4 text-center md:hidden">
                <button
                  type="button"
                  onClick={() => togglePanel(false)}
                  className="text-sm text-gray-500"
                >
                  Already have an account?{" "}
                  <span className="text-[#5D5FEF] font-medium">Sign In</span>
                </button>
              </div>
            </form>
          </div>

          {/* ─── Sign In Form (DOM-second) ─── */}
          <div className="auth-form-container sign-in-container">
            <form onSubmit={handleLogin} className="space-y-4">
              <h1
                className="text-3xl font-bold text-center text-gray-900 mb-2 italic"
                style={{ fontFamily: '"Playfair Display", serif' }}
              >
                Welcome Back
              </h1>

              {loginError && (
                <div className="p-3 text-sm rounded-lg border font-medium text-red-500 bg-red-50 border-red-200">
                  {loginError}
                </div>
              )}

              <input
                required
                type="text"
                placeholder="Login Id / Email"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className={inputClass}
              />

              <div className="relative w-full">
                <input
                  required
                  type={showLoginPassword ? "text" : "password"}
                  placeholder="Password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#4B4DD9] transition-colors"
                >
                  {showLoginPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#4B4DD9] px-4 py-3 mt-4 font-semibold text-white hover:bg-[#3B3DB9] transition-all shadow-md hover:shadow-lg disabled:bg-[#3B3DB9] disabled:cursor-wait"
              >
                {loginLoading ? "Signing In..." : "Sign In"}
              </button>

              {/* Mobile-only switch link */}
              <div className="mt-4 text-center md:hidden">
                <button
                  type="button"
                  onClick={() => togglePanel(true)}
                  className="text-sm text-gray-500"
                >
                  Don&apos;t have an account?{" "}
                  <span className="text-[#5D5FEF] font-medium">Sign Up</span>
                </button>
              </div>
            </form>
          </div>

          {/* ─── Desktop Overlay (sliding gradient blob) ─── */}
          <div className="auth-overlay-container hidden md:block">
            <div className="auth-overlay">
              {/* Left panel — shown when Sign Up is active */}
              <div className="auth-overlay-panel auth-overlay-left">
                <h2
                  className="text-3xl font-bold italic mb-4"
                  style={{ fontFamily: '"Playfair Display", serif' }}
                >
                  Welcome Back!
                </h2>
                <p className="text-sm text-white/80 mb-8 max-w-[260px] leading-relaxed">
                  To keep connected with us please login with your personal info
                </p>
                <button
                  onClick={() => togglePanel(false)}
                  className="rounded-xl border-2 border-white px-12 py-3 font-semibold text-white hover:bg-white hover:text-[#4B4DD9] transition-colors shadow-sm"
                >
                  Sign In
                </button>
              </div>

              {/* Right panel — shown when Sign In is active */}
              <div className="auth-overlay-panel auth-overlay-right">
                <h2
                  className="text-3xl font-bold italic mb-4"
                  style={{ fontFamily: '"Playfair Display", serif' }}
                >
                  Hello, Friend!
                </h2>
                <p className="text-sm text-white/80 mb-8 max-w-[260px] leading-relaxed">
                  Enter your personal details and start your journey with us
                </p>
                <button
                  onClick={() => togglePanel(true)}
                  className="rounded-xl border-2 border-white px-12 py-3 font-semibold text-white hover:bg-white hover:text-[#4B4DD9] transition-colors shadow-sm"
                >
                  Sign Up
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
