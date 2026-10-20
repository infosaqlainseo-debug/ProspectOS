"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Building2, LayoutDashboard, Search, Globe, LineChart, BrainCircuit, Activity, ShieldAlert, Settings, BookOpen, GitFork, Mail, Kanban, Target, BarChart3, Swords, FileText, ShieldCheck, HardDrive, Share2 } from "lucide-react";

import { Suspense } from "react";

function SidebarContent() {
  const pathname = usePathname();

  const routes = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/companies", label: "Companies", icon: Building2 },
    { href: "/discovery", label: "Discovery & Scraping", icon: Search },
    { href: "/website-intelligence", label: "Website Intelligence", icon: Globe },
    { href: "/seo-intelligence", label: "SEO Intelligence", icon: LineChart },
    { href: "/ai-intelligence", label: "AI Intelligence", icon: BrainCircuit },
    { href: "/sales-intelligence", label: "Sales Intelligence", icon: Target },
    { href: "/competitive-intelligence", label: "Competitive SEO", icon: Swords },
    { href: "/reports", label: "Client Reports", icon: FileText },
    { href: "/portal", label: "Client Portal", icon: ShieldCheck },
    { href: "/publishers", label: "Publishers", icon: BookOpen },
    { href: "/workflows", label: "Workflows", icon: GitFork },
    { href: "/outreach", label: "Outreach Composer", icon: Mail },
    { href: "/social-connections", label: "Social Accounts", icon: Share2 },
    { href: "/google-drive", label: "Google Drive", icon: HardDrive },
    { href: "/crm", label: "CRM & Pipeline", icon: Kanban },
    { href: "/analytics", label: "Revenue Analytics", icon: BarChart3 },
    { href: "/jobs", label: "Jobs", icon: Activity },
    { href: "/contradictions", label: "Contradictions", icon: ShieldAlert },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <div className="w-64 border-r border-gray-200 bg-white h-screen flex flex-col fixed top-0 left-0">
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <h1 className="text-xl font-bold tracking-tight text-gray-900">ProspectOS</h1>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {routes.map((route) => {
          const isActive = pathname === route.href;
          const Icon = route.icon;
          return (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive 
                  ? "bg-blue-50 text-blue-700" 
                  : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Icon className={cn("mr-3 h-5 w-5", isActive ? "text-blue-700" : "text-gray-400")} />
              {route.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
export function Sidebar() { return <Suspense fallback={<div className="w-64 bg-white border-r border-gray-200"></div>}><SidebarContent /></Suspense>; }
