import Link from "next/link";
import { Shield, ArrowRight } from "lucide-react";

export default function SignUpPage() {
  return (
    <div className="auth-page-bg auth-mesh-bg flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl p-8 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 text-center space-y-6">
        <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-blue-600/10 border border-blue-600/20 text-blue-600 mb-2">
          <Shield className="h-8 w-8" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">CrimeRakshak Registration</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Karnataka State Police Crime Intelligence Platform</p>
        </div>

        <Link
          href="/overview"
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg shadow-blue-600/25 transition-all duration-200 hover:scale-[1.02]"
        >
          <span>Access Police Portal (Local Mode)</span>
          <ArrowRight className="h-4 w-4" />
        </Link>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
          <p className="text-xs text-slate-400">Local Development Environment</p>
        </div>
      </div>
    </div>
  );
}
