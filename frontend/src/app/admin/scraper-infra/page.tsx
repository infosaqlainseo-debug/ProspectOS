"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Cpu,
  ChevronLeft,
  RefreshCw,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  Server,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Terminal
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi, ScraperInfraStatus } from "@/lib/adminApi";

export default function ScraperInfraPage() {
  const [status, setStatus] = useState<ScraperInfraStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [concurrency, setConcurrency] = useState(5);

  const fetchInfra = async () => {
    try {
      setLoading(true);
      const [infraStatus, infraLogs] = await Promise.all([
        adminApi.getScraperInfraStatus(),
        adminApi.getScraperLogs(),
      ]);
      setStatus(infraStatus);
      setConcurrency(infraStatus.concurrency_limit);
      setLogs(infraLogs.lines || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInfra();
  }, []);

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true);
      const res = await adminApi.executeScraperAction(action, concurrency);
      alert(res.message);
      await fetchInfra();
    } catch (e: any) {
      alert(`Action error: ${e.message}`);
    } finally {
      setActionLoading(false);
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
              Infrastructure
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            Scraper Infrastructure Control Center
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor worker pool availability, regulate concurrency limits, inspect queue depths, and review execution logs.
          </p>
        </div>
        <button
          onClick={fetchInfra}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Status
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Worker Pool</span>
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Active
            </span>
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{status?.active_workers_count ?? 1} Nodes</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Standalone Linux cluster</div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Running Jobs</span>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{status?.running_jobs ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Active extraction tasks</div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Queue Depth</span>
            <Server className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-[26px] font-semibold text-slate-900 tracking-tight tabular-nums">{status?.queue_depth ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Pending jobs in Redis</div>
        </Card>

        <Card className="p-3.5 border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white">
          <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Completed (24h)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-[26px] font-semibold text-emerald-600 tracking-tight tabular-nums">{status?.completed_jobs_24h ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Avg duration: {status?.average_duration_seconds ?? 3.8}s</div>
        </Card>
      </div>

      {/* Control Actions & Concurrency Tuning */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Worker Operations &amp; Safety Controls</CardTitle>
            <CardDescription>Pause, resume, or trigger retries for failed tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleAction("PAUSE")}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition"
              >
                <Pause className="w-4 h-4" /> Pause Ingestion
              </button>

              <button
                onClick={() => handleAction("RESUME")}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
              >
                <Play className="w-4 h-4" /> Resume Workers
              </button>

              <button
                onClick={() => handleAction("RETRY_FAILED")}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition"
              >
                <RotateCcw className="w-4 h-4" /> Retry Failed Jobs
              </button>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Pausing workers gracefully allows currently running HTTP extraction streams to finalize while withholding queued tasks.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Concurrency &amp; Rate Limits</CardTitle>
            <CardDescription>Configure global worker extraction parallelism</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Max Concurrent HTTP Connections: {concurrency}</span>
                <span className="font-mono text-slate-400">Default: 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="25"
                value={concurrency}
                onChange={(e) => setConcurrency(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>
            <button
              onClick={() => handleAction("SET_CONCURRENCY")}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
            >
              <Sliders className="w-3.5 h-3.5" /> Apply Concurrency Policy
            </button>
          </CardContent>
        </Card>
      </div>

      {/* Live Log Terminal */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-600" />
            <CardTitle>Cluster Worker Live Log Output</CardTitle>
          </div>
          <Badge variant="neutral" size="sm">LIVE STREAM</Badge>
        </CardHeader>
        <CardContent className="p-0">
          <div className="bg-slate-950 text-slate-200 p-4 font-mono text-xs rounded-b-xl overflow-x-auto max-h-64 space-y-1">
            {logs.map((line, idx) => (
              <div key={idx} className="leading-relaxed">
                <span className="text-emerald-400">&gt;</span> {line}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

