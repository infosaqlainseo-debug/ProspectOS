import React from "react";
import Link from "next/link";
import { Shield, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="h-10 border-t border-slate-200/80 bg-white/80 px-6 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 font-medium text-slate-700">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>All Systems Operational</span>
        </div>
        <span className="text-slate-300">|</span>
        <span className="font-mono text-slate-400">ProspectOS v2.4.0-enterprise</span>
      </div>

      <div className="flex items-center gap-4">
        <Link href="/docs" className="hover:text-slate-900 transition flex items-center gap-1">
          <span>Documentation</span>
          <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
        </Link>
        <Link href="/api-docs" className="hover:text-slate-900 transition">
          API Specs
        </Link>
        <Link href="/admin/seo" className="hover:text-slate-900 transition flex items-center gap-1">
          <Shield className="w-2.5 h-2.5 text-blue-600" />
          <span>SEO &amp; Security</span>
        </Link>
        <span className="text-slate-400 hidden sm:inline">&copy; 2026 ProspectOS Intelligence Platform</span>
      </div>
    </footer>
  );
}

