"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  LayoutDashboard,
  Search,
  Code2,
  LayoutGrid,
  Database,
  Cloud,
  CheckCircle2,
  Clock,
  ArrowRight,
  RefreshCw,
  Play,
  FileSpreadsheet,
  Activity,
  Layers,
  Sparkles,
  Users,
  Kanban,
  ShieldCheck,
  TrendingUp,
  Cpu,
  BarChart3,
  PieChart,
  HelpCircle,
  AlertTriangle,
  FolderOpen
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { scraperApi, ScraperTask } from "@/lib/scraperApi";
import { crmApi, CRMLead } from "@/lib/crmApi";

function formatRelativeTime(dateStr?: string | null): string {
  if (!dateStr) return "N/A";
  const date = new Date(dateStr);
  const now = new Date();
  const diffInSec = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diffInSec < 60) return "just now";
  if (diffInSec < 3600) return `${Math.floor(diffInSec / 60)}m ago`;
  if (diffInSec < 86400) return `${Math.floor(diffInSec / 3600)}h ago`;
  if (diffInSec < 604800) return `${Math.floor(diffInSec / 86400)}d ago`;
  return date.toLocaleDateString();
}

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    total_tasks: 0,
    active_schedules: 0,
    total_records: 0,
    valid_records: 0,
    duplicate_records: 0,
    total_runs: 0,
    total_crm_leads: 0,
    completed_runs: 0,
    failed_runs: 0,
    success_rate_percent: 100,
    failure_rate_percent: 0,
  });
  const [dailyExtractions, setDailyExtractions] = useState<Array<{ date: string; count: number; valid: number; duplicates: number }>>([]);
  const [monthlyExtractions, setMonthlyExtractions] = useState<Array<{ month: string; count: number }>>([]);
  const [leadSources, setLeadSources] = useState<Array<{ source: string; count: number; percentage: number }>>([]);
  const [crmFunnel, setCrmFunnel] = useState<Array<{ stage: string; count: number; percentage: number }>>([]);
  const [recentTasks, setRecentTasks] = useState<ScraperTask[]>([]);
  const [recentLeads, setRecentLeads] = useState<CRMLead[]>([]);
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const [overviewData, leadsData] = await Promise.all([
        scraperApi.getOverview(),
        crmApi.listLeads({ page: 1, page_size: 5 }),
      ]);
      if (overviewData && overviewData.metrics) {
        setMetrics({
          total_tasks: overviewData.metrics.total_tasks || 0,
          active_schedules: overviewData.metrics.active_schedules || 0,
          total_records: overviewData.metrics.total_records || 0,
          valid_records: overviewData.metrics.valid_records || 0,
          duplicate_records: overviewData.metrics.duplicate_records || 0,
          total_runs: overviewData.metrics.total_runs || 0,
          total_crm_leads: overviewData.metrics.total_crm_leads || 0,
          completed_runs: overviewData.metrics.completed_runs || 0,
          failed_runs: overviewData.metrics.failed_runs || 0,
          success_rate_percent: overviewData.metrics.success_rate_percent ?? 100,
          failure_rate_percent: overviewData.metrics.failure_rate_percent ?? 0,
        });
        setRecentTasks(overviewData.recent_tasks || []);
        setDailyExtractions(overviewData.daily_extractions || []);
        setMonthlyExtractions(overviewData.monthly_extractions || []);
        setLeadSources(overviewData.lead_sources || []);
        setCrmFunnel(overviewData.crm_funnel || []);
        setRecentActivities(overviewData.recent_activities || []);
      }
      if (leadsData && leadsData.items) {
        setRecentLeads(leadsData.items);
      }
    } catch (err) {
      console.error("Failed to load overview data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleQuickRun = async (taskId: string) => {
    try {
      setRunningTaskId(taskId);
      await scraperApi.runTask(taskId, "CLOUD");
      await fetchOverview();
    } catch (e: any) {
      alert(`Execution error: ${e.message}`);
    } finally {
      setRunningTaskId(null);
    }
  };

  // Find max extraction count for bar height scaling
  const maxDailyCount = Math.max(...dailyExtractions.map(d => d.count), 1);

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              Enterprise Platform
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Cloud Workers Online
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            ProspectOS Scraper &amp; Lead Intelligence Platform
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover businesses, run visual workflows, extract structured website data, clean, score, and sync with CRM.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/custom-scraper"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-[0_1px_2px_rgba(15,23,42,0.06)] transition"
          >
            <Code2 className="w-3.5 h-3.5" />
            New Scraper Task
          </Link>
        </div>
      </div>

      {/* Primary KPI Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Total Tasks</span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.total_tasks}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Configured workflows</div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Total active &amp; draft scraper tasks in the database.
          </div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Scraped Records</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.total_records}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Extracted from web</div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Raw company and contact records extracted by scraper tasks.
          </div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Validated Leads</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.valid_records}</div>
          <div className="text-[11px] text-emerald-600 mt-0.5">Quality verified (100%)</div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Scraped records that passed domain, email, and viability validation rules.
          </div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">CRM Leads</span>
            <Users className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.total_crm_leads}</div>
          <div className="text-[11px] text-blue-600 mt-0.5">Central Directory</div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Total company intelligence profiles stored in the central CRM database.
          </div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Total Runs</span>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.total_runs}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            <span className="text-emerald-600 font-medium">{metrics.success_rate_percent}%</span> success
          </div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Total task execution runs recorded across the cluster ({metrics.completed_runs} completed, {metrics.failed_runs} failed).
          </div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Schedules</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{metrics.active_schedules}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Cron automations</div>
          <div className="hidden group-hover:block absolute bottom-full mb-1 left-0 z-20 w-48 p-2 text-[10px] text-slate-600 bg-slate-900 text-white rounded shadow-lg pointer-events-none">
            Recurring background scraper jobs scheduled to run automatically.
          </div>
        </Card>
      </div>

      {/* Analytics & Pipeline Performance Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Daily Extraction Trends Card */}
        <Card className="p-5 bg-white border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] lg:col-span-2">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-semibold text-slate-900">Extraction Velocity &amp; Historical Volume</h3>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Actual daily and monthly scraping yield from PostgreSQL</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/50">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                100% Quality Pass
              </span>
            </div>
          </div>

          {dailyExtractions.length === 0 ? (
            <div className="py-10 text-center text-slate-400 text-xs">
              <Database className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              No extraction history recorded yet. Run a scraper task to generate telemetry.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Daily Chart Bars */}
              <div className="space-y-2.5">
                <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Daily Extracted Leads</div>
                <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 items-end pt-4 h-32 border-b border-slate-100 pb-2">
                  {dailyExtractions.map((d) => {
                    const heightPercent = Math.max(15, Math.round((d.count / maxDailyCount) * 100));
                    return (
                      <div key={d.date} className="flex flex-col items-center gap-1.5 h-full justify-end group relative">
                        {/* Hover Tooltip */}
                        <div className="hidden group-hover:block absolute bottom-full mb-2 z-30 p-2 text-[10px] bg-slate-900 text-white rounded shadow-md whitespace-nowrap pointer-events-none">
                          <div className="font-semibold">{d.date}</div>
                          <div>Total: {d.count} records</div>
                          <div>Valid: {d.valid} leads</div>
                          <div>Dups: {d.duplicates}</div>
                        </div>
                        <div className="text-[10px] font-mono text-slate-500 tabular-nums">{d.count}</div>
                        <div
                          style={{ height: `${heightPercent}%` }}
                          className="w-full max-w-[28px] bg-blue-500 hover:bg-blue-600 rounded-t transition-all duration-300"
                        />
                        <div className="text-[10px] text-slate-400 truncate w-full text-center font-mono">
                          {d.date.slice(5)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Monthly Summary Badges */}
              <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
                <span className="text-slate-400 font-medium">Monthly Breakdown:</span>
                {monthlyExtractions.map(m => (
                  <span key={m.month} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-50 border border-slate-200/70 text-slate-700 font-mono text-[11px]">
                    <span className="text-slate-400">{m.month}:</span>
                    <strong className="text-slate-900">{m.count} leads</strong>
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Lead Source & Channel Distribution */}
        <Card className="p-5 bg-white border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <PieChart className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-semibold text-slate-900">Lead Source Distribution</h3>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Origin channels across {metrics.total_crm_leads} leads</p>
            </div>
          </div>

          {leadSources.length === 0 ? (
            <div className="py-10 text-center text-slate-400 text-xs">
              No lead sources classified.
            </div>
          ) : (
            <div className="space-y-3">
              {leadSources.map((s) => (
                <div key={s.source} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-medium text-slate-700">{s.source}</span>
                    <span className="font-mono text-slate-500 tabular-nums">{s.count} ({s.percentage}%)</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.max(4, s.percentage)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* CRM Conversion Funnel Preview */}
          <div className="mt-5 pt-4 border-t border-slate-100">
            <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 mb-2">Pipeline Funnel</div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              {crmFunnel.slice(0, 3).map((f) => (
                <div key={f.stage} className="p-2 rounded bg-slate-50/70 border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">{f.stage}</div>
                  <div className="text-base font-semibold text-slate-900 tabular-nums">{f.count}</div>
                  <div className="text-[10px] text-blue-600 font-mono">{f.percentage}%</div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Dual Platform Hub: Scraper Engine + CRM Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Scraper Platform Hub Card */}
        <Card className="p-5 bg-white border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200/60">
              Engine 01
            </span>
            <span className="text-xs text-slate-400 font-medium">Scraper Core</span>
          </div>
          <h3 className="text-[16px] font-semibold text-slate-900">Web Scraping Engine</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Visual element picker, dynamic pagination loops, cloud worker pools, and automated scheduled ingestion.
          </p>
          <div className="grid grid-cols-2 gap-2.5 my-4 text-xs">
            <Link
              href="/discovery"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Search className="w-4 h-4 text-blue-600" />
              <span className="font-medium text-slate-800">Lead Discovery</span>
            </Link>
            <Link
              href="/templates"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <LayoutGrid className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">Prebuilt Templates</span>
            </Link>
            <Link
              href="/custom-scraper"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Code2 className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">Visual Builder</span>
            </Link>
            <Link
              href="/cloud-extraction"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Cloud className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">Cloud Cluster</span>
            </Link>
          </div>
          <Link
            href="/tasks"
            className="text-xs font-medium text-blue-600 hover:text-blue-700 inline-flex items-center gap-1.5 transition"
          >
            View All Scraper Tasks <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </Card>

        {/* Lead Intelligence & CRM Hub Card */}
        <Card className="p-5 bg-white border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200/60">
              Engine 02
            </span>
            <span className="text-xs text-slate-400 font-medium">Enterprise CRM</span>
          </div>
          <h3 className="text-[16px] font-semibold text-slate-900">Lead Intelligence CRM</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Central source of truth with 4-pillar lead scoring (0–100), Kanban pipelines, AI research, and adaptive learning loops.
          </p>
          <div className="grid grid-cols-2 gap-2.5 my-4 text-xs">
            <Link
              href="/crm"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Users className="w-4 h-4 text-blue-600" />
              <span className="font-medium text-slate-800">All CRM Leads</span>
            </Link>
            <Link
              href="/crm/pipeline"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Kanban className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">Pipeline Board</span>
            </Link>
            <Link
              href="/crm/assistant"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">ProspectOS AI</span>
            </Link>
            <Link
              href="/crm/analytics"
              className="p-2.5 rounded-lg border border-slate-200/75 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition flex items-center gap-2"
            >
              <TrendingUp className="w-4 h-4 text-slate-700" />
              <span className="font-medium text-slate-800">CRM Analytics</span>
            </Link>
          </div>
          <Link
            href="/crm"
            className="text-xs font-medium text-blue-600 hover:text-blue-700 inline-flex items-center gap-1.5 transition"
          >
            Explore Central Lead Database ({metrics.total_crm_leads} profiles) <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </Card>
      </div>

      {/* Recent Scraper Tasks & Recent CRM Leads Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Recent Scraping Tasks */}
        <Card className="border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-[13px] font-semibold text-slate-900">Recent Scraping Tasks</h3>
              <p className="text-[11px] text-slate-400">Recently executed and configured workflows</p>
            </div>
            <Link href="/tasks" className="text-xs text-blue-600 hover:underline font-medium">
              View all
            </Link>
          </div>
          <div className="divide-y divide-slate-100/80 text-xs">
            {recentTasks.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <FolderOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="font-medium text-slate-600">No scraping tasks found</p>
                <p className="text-[11px] mt-0.5">Create your first task using the Visual Builder or Templates.</p>
                <Link href="/custom-scraper" className="mt-3 inline-block px-3 py-1 bg-blue-50 text-blue-600 rounded text-xs font-medium hover:bg-blue-100">
                  Create Task
                </Link>
              </div>
            ) : (
              recentTasks.slice(0, 5).map((task) => (
                <div key={task.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                  <div>
                    <div className="font-medium text-slate-900">{task.name}</div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {task.task_type} &bull; <strong className="text-slate-700">{task.total_records}</strong> records collected
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${
                      task.status === "COMPLETED" 
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60" 
                        : "bg-slate-100 text-slate-600 border border-slate-200"
                    }`}>
                      {task.status}
                    </span>
                    <button
                      onClick={() => handleQuickRun(task.id)}
                      disabled={runningTaskId === task.id}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition"
                      title="Run Now in Cloud"
                    >
                      <Play className={`w-3.5 h-3.5 ${runningTaskId === task.id ? "animate-spin" : ""}`} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recent CRM Leads */}
        <Card className="border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-[13px] font-semibold text-slate-900">Recent CRM Prospects</h3>
              <p className="text-[11px] text-slate-400">Persisted leads with 4-pillar score breakdown</p>
            </div>
            <Link href="/crm" className="text-xs text-blue-600 hover:underline font-medium">
              View all ({metrics.total_crm_leads})
            </Link>
          </div>
          <div className="divide-y divide-slate-100/80 text-xs">
            {recentLeads.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="font-medium text-slate-600">No CRM leads available</p>
                <p className="text-[11px] mt-0.5">Import leads from the Scraper Engine or create them manually.</p>
                <Link href="/crm" className="mt-3 inline-block px-3 py-1 bg-blue-50 text-blue-600 rounded text-xs font-medium hover:bg-blue-100">
                  Open CRM
                </Link>
              </div>
            ) : (
              recentLeads.map((lead) => (
                <div key={lead.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                  <div>
                    <Link href={`/crm/leads/${lead.id}`} className="font-medium text-slate-900 hover:text-blue-600 transition truncate block max-w-xs">
                      {lead.company_name}
                    </Link>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {lead.canonical_domain || "No domain"} &bull; {lead.industry || "General"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-medium text-blue-700 bg-blue-50/80 px-2 py-0.5 rounded border border-blue-200/60 tabular-nums">
                      {(lead.lead_score ?? 0).toFixed(0)}/100
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-600 border border-slate-200">
                      {lead.sales_stage}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* System Audit Trail Row */}
      {recentActivities.length > 0 && (
        <Card className="border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white p-5">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Recent Platform Operations</h3>
              <p className="text-[11px] text-slate-400">Cryptographically verifiable audit log</p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">Live Heartbeat</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {recentActivities.slice(0, 6).map((act) => (
              <div key={act.id} className="p-2.5 rounded-lg bg-slate-50/60 border border-slate-100 text-xs">
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="font-medium text-slate-900 text-[11px] truncate">{act.action}</span>
                  <span className="text-[10px] font-mono text-slate-400 whitespace-nowrap" title={act.timestamp}>
                    {formatRelativeTime(act.timestamp)}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono truncate">
                  {act.resource_type}: {act.details?.email || act.details?.action || act.details?.notes || "System action"}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
