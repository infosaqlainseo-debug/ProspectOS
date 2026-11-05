"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  Users,
  Mail,
  Phone,
  Globe2,
  TrendingUp,
  Award,
  Layers,
  Building2,
  RefreshCw,
  PieChart
} from "lucide-react";
import { crmApi, CRMAnalyticsData } from "@/lib/crmApi";

export default function CRMAnalyticsPage() {
  const [data, setData] = useState<CRMAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const res = await crmApi.getCRMAnalytics();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Pipeline & Lead Analytics
            </span>
            <span className="text-xs text-slate-400 font-mono">Real-Time Data</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">CRM Intelligence & Performance Metrics</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Aggregated intelligence metrics across lead volumes, enrichment coverage, geographic footprints, and score distributions.
          </p>
        </div>

        <button
          onClick={fetchAnalytics}
          className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-100 rounded-lg transition"
          title="Refresh Metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading || !data ? (
        <div className="p-16 text-center text-slate-400 text-sm">
          Calculating CRM intelligence analytics...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider">Total Leads</span>
                <Users className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="text-2xl font-bold font-mono text-slate-900">{data.total_leads}</div>
              <p className="text-[11px] text-slate-500">Persistent Central CRM database</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider">Email Coverage</span>
                <Mail className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-600">
                {data.data_completeness.email_coverage_percent}%
              </div>
              <p className="text-[11px] text-slate-500 font-mono">{data.data_completeness.with_email} verified emails</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider">Phone Coverage</span>
                <Phone className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-2xl font-bold font-mono text-blue-600">
                {data.data_completeness.phone_coverage_percent}%
              </div>
              <p className="text-[11px] text-slate-500 font-mono">{data.data_completeness.with_phone} verified phone lines</p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider">Active Websites</span>
                <Globe2 className="w-4 h-4 text-sky-600" />
              </div>
              <div className="text-2xl font-bold font-mono text-slate-900">
                {data.data_completeness.with_website}
              </div>
              <p className="text-[11px] text-slate-500">Live domains ready for SEO audit</p>
            </div>
          </div>

          {/* Middle Section: Stage Funnel & Score Distribution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sales Stage Funnel */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                Pipeline Stage Distribution
              </h3>

              <div className="space-y-3">
                {Object.entries(data.stage_distribution || {}).map(([stage, count]) => {
                  const pct = Math.round((count / Math.max(1, data.total_leads)) * 100);
                  return (
                    <div key={stage} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="text-slate-700">{stage.replace("_", " ")}</span>
                        <span className="font-mono text-slate-500">{count} ({pct}%)</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Lead Score Distribution Buckets */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-500" />
                Lead Quality Score Distribution
              </h3>

              <div className="space-y-3">
                {Object.entries(data.score_distribution || {}).map(([bucket, count]) => {
                  const pct = Math.round((count / Math.max(1, data.total_leads)) * 100);
                  const isTop = bucket === "81-100" || bucket === "61-80";
                  return (
                    <div key={bucket} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="text-slate-700">Score {bucket} pts</span>
                        <span className="font-mono text-slate-500">{count} leads</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${isTop ? "bg-emerald-500" : "bg-slate-400"}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Bottom Section: Top Countries & Industries */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Countries */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <Globe2 className="w-4 h-4 text-blue-600" />
                Top Geographic Footprints
              </h3>
              <div className="divide-y divide-slate-100 text-xs">
                {(data.top_countries || []).length === 0 ? (
                  <p className="py-4 text-slate-400 text-center">No location data recorded yet.</p>
                ) : (
                  data.top_countries.map((c, i) => (
                    <div key={i} className="py-2.5 flex items-center justify-between">
                      <span className="font-medium text-slate-800">{c.country}</span>
                      <span className="font-mono font-bold text-slate-600">{c.count} leads</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Top Industries */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-indigo-600" />
                Top Industry Verticals
              </h3>
              <div className="divide-y divide-slate-100 text-xs">
                {(data.top_industries || []).length === 0 ? (
                  <p className="py-4 text-slate-400 text-center">No industry verticals categorized yet.</p>
                ) : (
                  data.top_industries.map((ind, i) => (
                    <div key={i} className="py-2.5 flex items-center justify-between">
                      <span className="font-medium text-slate-800">{ind.industry}</span>
                      <span className="font-mono font-bold text-slate-600">{ind.count} leads</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

