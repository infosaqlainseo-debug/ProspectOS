"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Code2,
  LayoutGrid,
  Database,
  Cloud,
  CheckCircle2,
  Calendar,
  Layers,
  Sparkles,
  Users,
  Kanban,
  FileSpreadsheet,
  BarChart3,
  Globe,
  Settings,
  ShieldCheck,
  ChevronLeft,
  ChevronDown,
  Building2,
  Cpu,
  Sliders,
  X
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface SidebarProps {
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({
  isMobileOpen = false,
  onMobileClose,
  isCollapsed = false,
  onToggleCollapse
}: SidebarProps) {
  const pathname = usePathname();
  const [isAdminExpanded, setIsAdminExpanded] = useState(true);

  const isActive = (path: string) => {
    if (path === "/" && pathname === "/") return true;
    if (path !== "/" && pathname.startsWith(path)) return true;
    return false;
  };

  const navGroups = [
    {
      group: "WORKSPACE",
      items: [
        { name: "Overview", href: "/", icon: LayoutDashboard },
        { name: "Lead Discovery", href: "/discovery", icon: Search },
        { name: "Templates", href: "/templates", icon: LayoutGrid },
        { name: "Custom Scraper", href: "/custom-scraper", icon: Code2 },
        { name: "My Tasks", href: "/tasks", icon: Calendar },
        { name: "Cloud Extraction", href: "/cloud-extraction", icon: Cloud },
        { name: "Task Scheduler", href: "/scheduler", icon: Calendar },
      ],
    },
    {
      group: "LEAD INTELLIGENCE",
      items: [
        { name: "All Leads", href: "/crm", icon: Users },
        { name: "Companies", href: "/companies", icon: Building2 },
        { name: "Pipeline Board", href: "/crm/pipeline", icon: Kanban },
        { name: "Lists & Segments", href: "/crm/lists", icon: Layers },
        { name: "ProspectOS AI", href: "/crm/assistant", icon: Sparkles, badge: "AI" },
        { name: "CRM Analytics", href: "/crm/analytics", icon: BarChart3 },
      ],
    },
    {
      group: "DATA MANAGEMENT",
      items: [
        { name: "Data Center", href: "/data-center", icon: Database },
        { name: "Data Cleaning", href: "/data-cleaning", icon: CheckCircle2 },
        { name: "Import & Export", href: "/crm/import-export", icon: FileSpreadsheet },
      ],
    },
    {
      group: "PLATFORM",
      items: [
        { name: "API & Integrations", href: "/api-docs", icon: Globe },
        { name: "Settings", href: "/settings", icon: Settings },
      ],
    },
  ];

  const adminSubItems = [
    { name: "Executive Overview", href: "/admin", icon: ShieldCheck },
    { name: "User Management", href: "/admin/users", icon: Users },
    { name: "Roles & RBAC", href: "/admin/roles", icon: Sliders },
    { name: "Scraper Infra", href: "/admin/scraper-infra", icon: Cpu },
    { name: "AI Control Center", href: "/admin/ai-control", icon: Sparkles },
    { name: "SEO Control Center", href: "/admin/seo", icon: Globe, badge: "SEO" },
    { name: "Platform Settings", href: "/admin/settings", icon: Settings },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white select-none">
      {/* Brand Header */}
      <div className={`h-14 border-b border-slate-100 flex items-center ${isCollapsed ? "justify-center px-2" : "justify-between px-4"}`}>
        <Link href="/" className="flex items-center gap-2.5 overflow-hidden group">
          <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-xs shrink-0 transition-transform group-hover:scale-105">
            P
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-slate-900 text-[13px] tracking-tight leading-none flex items-center gap-1.5">
                ProspectOS
                <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/50">v2.4</span>
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5">Scraper + CRM</span>
            </div>
          )}
        </Link>

        {/* Desktop Collapse Toggle */}
        {onToggleCollapse && !isCollapsed && (
          <button
            onClick={onToggleCollapse}
            className="hidden md:flex p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}

        {/* Mobile Close Button */}
        {onMobileClose && (
          <button
            onClick={onMobileClose}
            className="md:hidden p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto py-3 px-2.5 space-y-4">
        {navGroups.map((group) => (
          <div key={group.group}>
            {!isCollapsed && (
              <div className="px-2 mb-1 text-[10px] font-semibold text-slate-400 tracking-wider uppercase">
                {group.group}
              </div>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onMobileClose}
                    className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors group ${
                      active
                        ? "bg-blue-50/80 text-blue-700 font-medium"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    } ${isCollapsed ? "justify-center px-2" : ""}`}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 transition-colors ${
                        active ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
                      }`}
                    />
                    {!isCollapsed && (
                      <span className="truncate flex-1">{item.name}</span>
                    )}
                    {!isCollapsed && item.badge && (
                      <Badge variant="ai" size="sm" className="px-1.5 py-0 text-[9px]">
                        {item.badge}
                      </Badge>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}

        {/* Super Admin Section */}
        <div className="pt-2 border-t border-slate-100">
          {!isCollapsed && (
            <button
              onClick={() => setIsAdminExpanded(!isAdminExpanded)}
              className="w-full flex items-center justify-between px-2 py-1 mb-1 rounded hover:bg-slate-50 transition-colors text-left"
            >
              <span className="text-[10px] font-semibold text-slate-900 tracking-wider uppercase flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Administration
              </span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isAdminExpanded ? "" : "-rotate-90"}`} />
            </button>
          )}

          {(!isCollapsed ? isAdminExpanded : true) && (
            <div className="space-y-0.5">
              {adminSubItems.map((sub) => {
                const Icon = sub.icon;
                const active = isActive(sub.href);
                return (
                  <Link
                    key={sub.href}
                    href={sub.href}
                    onClick={onMobileClose}
                    className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors group ${
                      active
                        ? "bg-blue-50/80 text-blue-700 font-medium"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    } ${isCollapsed ? "justify-center px-2" : ""}`}
                    title={isCollapsed ? sub.name : undefined}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 transition-colors ${
                        active ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
                      }`}
                    />
                    {!isCollapsed && (
                      <span className="truncate flex-1">{sub.name}</span>
                    )}
                    {!isCollapsed && sub.badge && (
                      <Badge variant="success" size="sm" className="px-1.5 py-0 text-[9px]">
                        {sub.badge}
                      </Badge>
                    )}
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Footer Tenant Indicator */}
      {!isCollapsed && (
        <div className="p-3 border-t border-slate-100 bg-slate-50/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">
                P
              </div>
              <div className="truncate">
                <p className="text-xs font-medium text-slate-800 truncate">ProspectOS Global</p>
                <p className="text-[10px] text-slate-400 font-mono">Enterprise Workspace</p>
              </div>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-500" title="Connected" />
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={`hidden md:block fixed top-0 bottom-0 left-0 z-40 border-r border-slate-200/75 transition-all duration-200 ease-in-out ${
          isCollapsed ? "w-16" : "w-64"
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/20 backdrop-blur-xs transition-opacity"
            onClick={onMobileClose}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white shadow-xl">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
