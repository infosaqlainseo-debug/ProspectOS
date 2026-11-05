"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search,
  Bell,
  Command,
  Plus,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Menu,
  LogOut,
  UserCheck
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  onMobileMenuToggle?: () => void;
  onOpenCommandPalette?: () => void;
}

export function Header({ onMobileMenuToggle, onOpenCommandPalette }: HeaderProps) {
  const pathname = usePathname();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Generate dynamic breadcrumbs from URL pathname
  const generateBreadcrumbs = () => {
    if (!pathname || pathname === "/") return [{ label: "Workspace", href: "/" }, { label: "Overview", href: "/" }];

    const segments = pathname.split("/").filter(Boolean);
    const crumbs = [{ label: "Workspace", href: "/" }];

    let currentHref = "";
    for (const segment of segments) {
      currentHref += `/${segment}`;
      let label = segment.replace(/-/g, " ");
      label = label.charAt(0).toUpperCase() + label.slice(1);

      if (segment === "crm") label = "Lead Intelligence";
      else if (segment === "admin") label = "Super Admin";
      else if (segment === "api-docs") label = "API & Docs";
      else if (segment === "seo") label = "SEO Control";
      else if (segment === "custom-scraper") label = "Custom Scraper";

      crumbs.push({ label, href: currentHref });
    }
    return crumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  return (
    <header className="sticky top-0 z-30 h-14 bg-white/95 backdrop-blur-xs border-b border-slate-200/75 px-6 flex items-center justify-between gap-4 transition-all">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        {onMobileMenuToggle && (
          <button
            onClick={onMobileMenuToggle}
            className="md:hidden p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-50 transition"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <nav aria-label="Breadcrumb" className="flex items-center text-xs font-medium text-slate-500">
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            return (
              <React.Fragment key={crumb.href + idx}>
                {idx > 0 && <ChevronRight className="w-3.5 h-3.5 mx-1.5 text-slate-300 shrink-0" />}
                {isLast ? (
                  <span className="text-slate-900 font-semibold truncate max-w-[200px]">{crumb.label}</span>
                ) : (
                  <Link href={crumb.href} className="hover:text-slate-800 transition truncate max-w-[150px]">
                    {crumb.label}
                  </Link>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      {/* Right: Actions, Command Palette, System Health & User Profile */}
      <div className="flex items-center gap-2.5">
        {/* Quick Search / Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 text-xs text-slate-500 bg-slate-50 border border-slate-200/80 rounded-lg hover:bg-slate-100/70 hover:text-slate-900 transition"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="hidden md:inline">Quick search or commands...</span>
          <span className="md:hidden">Search</span>
          <kbd className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white border border-slate-200 rounded">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </button>

        {/* Live System Health Pill */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200/60 rounded-full text-[11px] font-medium text-slate-600">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Services Online</span>
        </div>

        {/* Quick New Task Link */}
        <Link
          href="/custom-scraper"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-[0_1px_2px_rgba(15,23,42,0.05)] transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Scraper</span>
        </Link>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-lg transition"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-blue-600 rounded-full ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl border border-slate-200/90 shadow-[0_4px_16px_rgba(15,23,42,0.07)] p-4 text-xs z-50 animate-in fade-in">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <span className="font-semibold text-slate-900">System Notifications</span>
                <span className="text-[10px] text-slate-400">Live Telemetry</span>
              </div>
              <div className="space-y-2.5">
                <div className="flex items-start gap-2.5 p-2 rounded-lg bg-blue-50/40 border border-blue-100/60">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-800">Scraper Cloud Workers Active</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">25 functions registered. Recurring cron tick every 30s.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/40 border border-emerald-100/60">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-800">Super Admin Security Active</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">Role-based controls &amp; sitemap validator configured.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Avatar & Super Admin Badge */}
        <div className="relative pl-2 border-l border-slate-200/80">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-50 transition text-left"
          >
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-xs ring-2 ring-white">
              SA
            </div>
            <div className="hidden xl:block text-left">
              <div className="text-xs font-semibold text-slate-900 leading-none">Super Admin</div>
              <div className="text-[10px] text-blue-600 font-medium mt-0.5">Platform Owner</div>
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl border border-slate-200/90 shadow-[0_4px_16px_rgba(15,23,42,0.07)] p-2 text-xs z-50 animate-in fade-in">
              <div className="p-2 border-b border-slate-100">
                <p className="font-semibold text-slate-900">Super Admin</p>
                <p className="text-[11px] text-slate-500 font-mono">infosaqlainseo@gmail.com</p>
                <div className="mt-1.5">
                  <Badge variant="ai" size="sm">SUPER_ADMIN</Badge>
                </div>
              </div>
              <div className="py-1 space-y-0.5">
                <Link
                  href="/admin"
                  className="flex items-center gap-2 px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 rounded-md transition font-medium"
                  onClick={() => setShowUserMenu(false)}
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                  Super Admin Panel
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-2 px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 rounded-md transition"
                  onClick={() => setShowUserMenu(false)}
                >
                  Workspace Settings
                </Link>
                <Link
                  href="/api-docs"
                  className="flex items-center gap-2 px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 rounded-md transition"
                  onClick={() => setShowUserMenu(false)}
                >
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                  API Documentation
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 px-2.5 py-1.5 text-slate-600 hover:bg-slate-50 rounded-md transition border-t border-slate-100 mt-1 pt-1"
                  onClick={() => setShowUserMenu(false)}
                >
                  <LogOut className="w-3.5 h-3.5 text-slate-400" />
                  Sign In / Switch User
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
