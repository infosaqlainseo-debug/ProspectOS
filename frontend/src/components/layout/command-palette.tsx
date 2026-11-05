"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Code2,
  Users,
  Kanban,
  Database,
  Cloud,
  Calendar,
  Sparkles,
  BarChart3,
  ShieldCheck,
  Globe,
  Settings,
  ArrowRight,
  X
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // parent handles toggle
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const commands = [
    { label: "Overview Dashboard", category: "Workspace", href: "/", icon: BarChart3 },
    { label: "Lead Discovery", category: "Workspace", href: "/discovery", icon: Search },
    { label: "Scraper Templates", category: "Workspace", href: "/templates", icon: Database },
    { label: "Visual Custom Scraper", category: "Workspace", href: "/custom-scraper", icon: Code2 },
    { label: "My Tasks & Execution", category: "Workspace", href: "/tasks", icon: Calendar },
    { label: "Cloud Extraction Cluster", category: "Workspace", href: "/cloud-extraction", icon: Cloud },
    { label: "All CRM Leads", category: "Lead Intelligence", href: "/crm", icon: Users },
    { label: "Pipeline Kanban Board", category: "Lead Intelligence", href: "/crm/pipeline", icon: Kanban },
    { label: "ProspectOS AI Assistant", category: "Lead Intelligence", href: "/crm/assistant", icon: Sparkles },
    { label: "CRM Analytics & Funnels", category: "Lead Intelligence", href: "/crm/analytics", icon: BarChart3 },
    { label: "Data Center & Extracted Records", category: "Data Management", href: "/data-center", icon: Database },
    { label: "Super Admin Control Center", category: "Administration", href: "/admin", icon: ShieldCheck },
    { label: "SEO Control Center", category: "Administration", href: "/admin/seo", icon: Globe },
    { label: "Platform Settings", category: "Platform", href: "/settings", icon: Settings },
  ];

  const filtered = query.trim()
    ? commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()) || c.category.toLowerCase().includes(query.toLowerCase()))
    : commands;

  const handleSelect = (href: string) => {
    router.push(href);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-900/25 backdrop-blur-[2px] p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-white rounded-xl border border-slate-200/80 shadow-[0_16px_40px_-8px_rgba(15,23,42,0.12)] overflow-hidden">
        {/* Search Input */}
        <div className="flex items-center px-4 py-3 border-b border-slate-100 gap-3">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Search commands, tools, or administration..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            className="w-full text-[13px] bg-transparent outline-none text-slate-900 placeholder:text-slate-400"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-slate-50">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No matching pages or commands found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.href}
                  onClick={() => handleSelect(item.href)}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-50 transition text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center group-hover:bg-blue-50 group-hover:text-blue-600 transition">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-900">{item.label}</span>
                      <span className="text-[10px] text-slate-400 ml-2">{item.category}</span>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-600 transition shrink-0" />
                </button>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2.5 bg-slate-50/80 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>Navigate with arrow keys</span>
          <kbd className="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-[10px] font-mono text-slate-500">ESC to close</kbd>
        </div>
      </div>
    </div>
  );
}

