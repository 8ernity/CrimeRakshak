"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { SignIn, SignUp } from "@clerk/nextjs";
import "@/app/auth.css";

interface UniversalAuthProps {
  defaultIsSignUp?: boolean;
}

export default function UniversalAuth({
  defaultIsSignUp = false,
}: UniversalAuthProps) {
  const pathname = usePathname();
  const [isSignUp, setIsSignUp] = useState(defaultIsSignUp);

  useEffect(() => {
    if (isSignUp !== (pathname === "/signup")) {
      setIsSignUp(pathname === "/signup");
    }
  }, [pathname, isSignUp]);

  const togglePanel = (toSignUp: boolean) => {
    setIsSignUp(toSignUp);
    window.history.pushState(null, "", toSignUp ? "/signup" : "/login");
  };

  return (
    <div className="auth-page-bg auth-mesh-bg relative">
      <div className="auth-wrapper">
        <div
          className={`auth-container ${isSignUp ? "right-panel-active" : ""}`}
        >
          {/* ─── Sign Up Form ─── */}
          <div className="auth-form-container sign-up-container">
            <div className="w-full h-full flex flex-col items-center justify-center overflow-auto px-6 py-6">
              <SignUp routing="hash" />
              
              <div className="mt-6 text-center md:hidden pb-10">
                <button
                  type="button"
                  onClick={() => togglePanel(false)}
                  className="text-sm text-gray-500"
                >
                  Already have an account?{" "}
                  <span className="text-[#2563EB] font-medium">Sign In</span>
                </button>
              </div>
            </div>
          </div>

          {/* ─── Sign In Form ─── */}
          <div className="auth-form-container sign-in-container">
            <div className="w-full h-full flex flex-col items-center justify-center overflow-auto px-6 py-6">
              <SignIn routing="hash" />
              
              <div className="mt-6 text-center md:hidden pb-10">
                <button
                  type="button"
                  onClick={() => togglePanel(true)}
                  className="text-sm text-gray-500"
                >
                  Don't have an account?{" "}
                  <span className="text-[#2563EB] font-medium">Sign Up</span>
                </button>
              </div>
            </div>
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
                  className="rounded-xl border-2 border-white px-12 py-3 font-semibold text-white hover:bg-white hover:text-[#2563EB] transition-colors shadow-sm"
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
                  className="rounded-xl border-2 border-white px-12 py-3 font-semibold text-white hover:bg-white hover:text-[#2563EB] transition-colors shadow-sm"
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
