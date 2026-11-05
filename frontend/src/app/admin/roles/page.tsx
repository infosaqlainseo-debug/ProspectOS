"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ShieldCheck, ChevronLeft, Check, X, RefreshCw, Sliders, Lock } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi, RolePermissionItem } from "@/lib/adminApi";

export default function RolesPermissionsPage() {
  const [roles, setRoles] = useState<RolePermissionItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const res = await adminApi.getRoles();
      setRoles(res);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const capabilities = [
    { key: "scraper:view", module: "Scraper", label: "View Scraping Tasks & Results" },
    { key: "scraper:create", module: "Scraper", label: "Create & Configure Workflows" },
    { key: "scraper:execute", module: "Scraper", label: "Execute Cloud Extraction Runs" },
    { key: "scraper:configure_infra", module: "Scraper", label: "Manage Worker Concurrency" },
    { key: "crm:view", module: "Lead CRM", label: "View Lead Intelligence Dossiers" },
    { key: "crm:edit", module: "Lead CRM", label: "Edit Lead Scoring & Stages" },
    { key: "crm:export", module: "Lead CRM", label: "Export Filtered CSV / JSON" },
    { key: "ai:chat", module: "AI Engine", label: "Query AI Intelligence Assistant" },
    { key: "ai:deep_research", module: "AI Engine", label: "Trigger Deep AI Company Analysis" },
    { key: "ai:configure_providers", module: "AI Engine", label: "Configure AI Providers & Keys" },
    { key: "seo:view", module: "SEO Engine", label: "View SEO Opportunities & Metrics" },
    { key: "seo:edit_metadata", module: "SEO Engine", label: "Edit Public SEO Metadata" },
    { key: "seo:run_audit", module: "SEO Engine", label: "Run Technical SEO Audits" },
    { key: "admin:access_panel", module: "Governance", label: "Access Super Admin Panel" },
    { key: "admin:manage_users", module: "Governance", label: "Provision & Suspend Users" },
    { key: "admin:view_audit_logs", module: "Governance", label: "Inspect Security Audit History" },
  ];

  const hasPermission = (role: RolePermissionItem, capKey: string): boolean => {
    if (role.role_name === "SUPER_ADMIN") return true;
    const [mod, action] = capKey.split(":");
    const modPerms = role.permissions[mod] || [];
    return modPerms.includes(action);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Link href="/admin" className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-medium">
              <ChevronLeft className="w-3.5 h-3.5" /> Back to Admin
            </Link>
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              Security Architecture
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-600" />
            Roles &amp; Granular Permissions Matrix
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict least-privilege role definitions enforced on both FastAPI backend endpoints and frontend views.
          </p>
        </div>
        <button
          onClick={fetchRoles}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Role Cards Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {roles.map((r) => (
          <Card key={r.id} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-900">{r.display_name}</span>
              {r.role_name === "SUPER_ADMIN" ? (
                <Badge variant="ai" size="sm">ROOT</Badge>
              ) : (
                <Badge variant="neutral" size="sm">{r.role_name}</Badge>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">{r.description}</p>
          </Card>
        ))}
      </div>

      {/* Permissions Matrix Table */}
      <Card>
        <CardHeader>
          <CardTitle>Capability Access Matrix</CardTitle>
          <CardDescription>System-level policy matrix across modules</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 border-b border-slate-200/80 text-slate-500 font-semibold">
                <tr>
                  <th className="py-3 px-4 w-1/3">Capability</th>
                  <th className="py-3 px-4">Module</th>
                  {roles.map((r) => (
                    <th key={r.id} className="py-3 px-4 text-center">
                      {r.display_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {capabilities.map((cap) => (
                  <tr key={cap.key} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4 font-medium text-slate-900">{cap.label}</td>
                    <td className="py-3 px-4">
                      <Badge variant="neutral" size="sm">{cap.module}</Badge>
                    </td>
                    {roles.map((r) => {
                      const granted = hasPermission(r, cap.key);
                      return (
                        <td key={r.id} className="py-3 px-4 text-center">
                          {granted ? (
                            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-50 text-emerald-600 font-bold">
                              <Check className="w-3.5 h-3.5" />
                            </span>
                          ) : (
                            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-50 text-slate-300">
                              <X className="w-3.5 h-3.5" />
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

