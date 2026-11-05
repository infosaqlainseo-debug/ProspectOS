"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Settings,
  ChevronLeft,
  RefreshCw,
  Save,
  Shield,
  Clock,
  Sliders,
  FileText,
  User,
  Database
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi } from "@/lib/adminApi";

export default function PlatformSettingsPage() {
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"settings" | "audit">("settings");

  const fetchData = async () => {
    try {
      setLoading(true);
      const [s, logs] = await Promise.all([
        adminApi.getPlatformSettings(),
        adminApi.getAuditLogs(30),
      ]);
      setSettings(s);
      setAuditLogs(logs);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async (category: string) => {
    try {
      setSaveLoading(true);
      await adminApi.updatePlatformSettings(category, settings[category] || {});
      alert(`Category '${category}' updated successfully.`);
      await fetchData();
    } catch (e: any) {
      alert(`Error saving settings: ${e.message}`);
    } finally {
      setSaveLoading(false);
    }
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
              Governance &amp; Policies
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-600" />
            Platform Settings &amp; Security Audit History
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure global platform variables, extraction boundaries, session timeouts, and inspect administrative activity logs.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("settings")}
          className={`pb-3 transition border-b-2 ${
            activeTab === "settings"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Platform Configuration
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-3 transition border-b-2 ${
            activeTab === "audit"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Security Audit Logs ({auditLogs.length})
        </button>
      </div>

      {activeTab === "settings" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* General & Appearance */}
          <Card>
            <CardHeader>
              <CardTitle>General &amp; Branding</CardTitle>
              <CardDescription>Default platform identification and display settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Platform Brand Name</label>
                <input
                  type="text"
                  value={settings.GENERAL?.platform_name || "ProspectOS"}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      GENERAL: { ...settings.GENERAL, platform_name: e.target.value },
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Support Contact Email</label>
                <input
                  type="email"
                  value={settings.GENERAL?.support_email || "support@prospectos.com"}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      GENERAL: { ...settings.GENERAL, support_email: e.target.value },
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Default Typography Family</label>
                <input
                  type="text"
                  readOnly
                  value="Geist Sans (Primary) + Geist Mono"
                  className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-lg text-slate-600"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => handleSave("GENERAL")}
                  disabled={saveLoading}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
                >
                  Save General
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Scraper Policies */}
          <Card>
            <CardHeader>
              <CardTitle>Scraper Execution Boundaries</CardTitle>
              <CardDescription>Safe extraction limits, timeouts, and bot etiquette</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Max Concurrent Scrapes</label>
                  <input
                    type="number"
                    value={settings.SCRAPER?.max_concurrent_tasks ?? 5}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        SCRAPER: { ...settings.SCRAPER, max_concurrent_tasks: Number(e.target.value) },
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Timeout (Seconds)</label>
                  <input
                    type="number"
                    value={settings.SCRAPER?.default_timeout_seconds ?? 300}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        SCRAPER: { ...settings.SCRAPER, default_timeout_seconds: Number(e.target.value) },
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/60 text-emerald-800 text-[11px] leading-relaxed">
                Respect robots.txt directives and domain rate limits are permanently enforced across all cloud worker nodes.
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => handleSave("SCRAPER")}
                  disabled={saveLoading}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
                >
                  Save Scraper Policies
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab: Security Audit Logs */}
      {activeTab === "audit" && (
        <Card>
          <CardHeader>
            <CardTitle>Administrative &amp; Security Audit Trail</CardTitle>
            <CardDescription>Persistent chronological record of administrative actions</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/70 border-b border-slate-200/80 text-slate-500 font-semibold">
                  <tr>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Resource</th>
                    <th className="py-3 px-4">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-12 text-center text-slate-400">
                        No security audit logs recorded yet.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/50 transition">
                        <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{log.action}</td>
                        <td className="py-3 px-4">
                          <Badge variant="neutral" size="sm">{log.resource_type}</Badge>
                        </td>
                        <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                          {JSON.stringify(log.details || {})}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

