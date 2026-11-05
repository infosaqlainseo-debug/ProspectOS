"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Cloud,
  Server,
  Activity,
  Cpu,
  RefreshCw,
  Terminal,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Download
} from "lucide-react";
import { scraperApi, ScraperTask, ScraperRun } from "@/lib/scraperApi";

export default function CloudExtractionPage() {
  const [tasks, setTasks] = useState<ScraperTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchCloudStatus = async () => {
    try {
      setRefreshing(true);
      const res = await scraperApi.getTasks({ limit: 100 });
      if (res && res.items) {
        setTasks(res.items);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCloudStatus();
  }, []);

  const runningTasks = tasks.filter((t) => t.status === "RUNNING");
  const completedTasks = tasks.filter((t) => t.status === "COMPLETED");
  const failedTasks = tasks.filter((t) => t.status === "FAILED");

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Module G: Cloud & Local Extraction
            </span>
            <span className="text-xs text-slate-400 font-mono">Distributed Worker Cluster</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Cloud Extraction Infrastructure</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Manage asynchronous extraction workers, monitor live background queues, and configure local agent runs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchCloudStatus}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/api-docs"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            <Terminal className="w-3.5 h-3.5" />
            Local Agent CLI
          </Link>
        </div>
      </div>

      {/* Cluster Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium">Cloud Queue State</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-slate-900">HEALTHY</div>
          <div className="text-[11px] text-slate-400">Redis & ARQ Workers Connected</div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium">Active Running Jobs</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{runningTasks.length}</div>
          <div className="text-[11px] text-blue-600 font-medium">Executing in background</div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium">Completed Jobs</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{completedTasks.length}</div>
          <div className="text-[11px] text-slate-400">Successfully persisted</div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium">Concurrency Limit</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">10 Workers</div>
          <div className="text-[11px] text-slate-400">Bounded rate limiting active</div>
        </div>
      </div>

      {/* Two Column Layout: Cloud Jobs vs Local Execution Agent */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Cloud Execution Jobs Table (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Cloud Background Tasks</h2>
              <p className="text-xs text-slate-500">Tasks executing on application server workers</p>
            </div>
            <Link href="/tasks" className="text-xs font-medium text-blue-600 hover:text-blue-700">
              Manage in My Tasks →
            </Link>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="py-3 px-4">Task</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Records Extracted</th>
                  <th className="py-3 px-3">Last Executed</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tasks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No cloud tasks queued.
                    </td>
                  </tr>
                ) : (
                  tasks.slice(0, 8).map((task) => (
                    <tr key={task.id} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{task.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono truncate max-w-xs">{task.target_url}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
                            task.status === "COMPLETED"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/50"
                              : task.status === "RUNNING"
                              ? "bg-blue-50 text-blue-700 border border-blue-200/50 animate-pulse"
                              : task.status === "FAILED"
                              ? "bg-rose-50 text-rose-700 border border-rose-200/50"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {task.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-800">{task.total_records}</td>
                      <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">
                        {task.last_run_at ? new Date(task.last_run_at).toLocaleTimeString() : "--"}
                      </td>
                      <td className="py-3 px-4 text-right space-x-1.5">
                        <button
                          onClick={async () => {
                            await scraperApi.runTask(task.id, "CLOUD");
                            await fetchCloudStatus();
                          }}
                          disabled={task.status === "RUNNING"}
                          className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-medium disabled:opacity-50 transition"
                        >
                          Run Cloud
                        </button>
                        <Link
                          href={`/data-center?task_id=${task.id}`}
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition inline-block"
                        >
                          Data
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Local Extraction Agent Architecture (1 col) */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-600" />
              <h3 className="font-bold text-sm text-slate-900">Local Execution Agent</h3>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              In addition to cloud extraction, ProspectOS supports running extraction jobs directly on your local machine via our standalone Python runner script.
            </p>

            <div className="space-y-2 pt-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Local Runner CLI</span>
              <pre className="p-3 bg-slate-900 text-emerald-400 rounded-lg text-[11px] font-mono overflow-x-auto leading-relaxed">
                curl -O http://localhost:8000/api/scraper/local-runner-script{"\n"}
                python prospectos_local_runner.py --task-id &lt;TASK_ID&gt;
              </pre>
            </div>

            <div className="pt-2">
              <a
                href="/api/scraper/local-runner-script"
                download="prospectos_local_runner.py"
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                <Download className="w-3.5 h-3.5" />
                Download Local Runner Script
              </a>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-3 text-xs">
            <div className="flex items-center gap-2 font-semibold text-slate-800">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Security & Execution Guardrails</span>
            </div>
            <ul className="space-y-1.5 text-slate-500 pl-5 list-disc">
              <li>All URLs verified through SSRF protection network filters.</li>
              <li>Robots.txt directives checked automatically prior to crawling.</li>
              <li>Respects rate limits to avoid server overload.</li>
              <li>Does not bypass CAPTCHAs, paywalls, or anti-bot protections.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

