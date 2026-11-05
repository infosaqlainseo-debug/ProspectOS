"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckSquare,
  Search,
  Play,
  Pause,
  RotateCcw,
  Trash2,
  Copy,
  ExternalLink,
  Code2,
  FileText,
  Clock,
  Terminal,
  X,
  AlertTriangle,
  CheckCircle2,
  Layers,
  Database,
  Filter,
  RefreshCw,
  Download
} from "lucide-react";
import { scraperApi, ScraperTask, ScraperRun } from "@/lib/scraperApi";

export default function TasksPage() {
  const [tasks, setTasks] = useState<ScraperTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Live Terminal Logs Drawer State
  const [activeLogRun, setActiveLogRun] = useState<ScraperRun | null>(null);
  const [activeTaskName, setActiveTaskName] = useState("");
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const res = await scraperApi.getTasks({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        search: searchQuery || undefined
      });
      if (res && res.items) {
        setTasks(res.items);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [statusFilter]);

  // Periodic poll if any task is RUNNING
  useEffect(() => {
    const hasRunning = tasks.some((t) => t.status === "RUNNING");
    if (!hasRunning) return;
    const interval = setInterval(() => {
      scraperApi
        .getTasks({
          status: statusFilter === "ALL" ? undefined : statusFilter,
          search: searchQuery || undefined
        })
        .then((res) => {
          if (res?.items) setTasks(res.items);
        });
    }, 3000);
    return () => clearInterval(interval);
  }, [tasks, statusFilter, searchQuery]);

  const handleRunTask = async (taskId: string, mode: "CLOUD" | "LOCAL" = "CLOUD") => {
    try {
      setActionLoadingId(taskId);
      const res = await scraperApi.runTask(taskId, mode);
      await fetchTasks();
      if (mode === "LOCAL" && res.runner_command) {
        alert(`Local run prepared. Run command in terminal:\n\n${res.runner_command}`);
      }
    } catch (e: any) {
      alert(`Error starting task: ${e.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePauseResume = async (task: ScraperTask) => {
    try {
      setActionLoadingId(task.id);
      if (task.is_schedule_active) {
        await scraperApi.pauseTask(task.id);
      } else {
        await scraperApi.resumeTask(task.id);
      }
      await fetchTasks();
    } catch (e: any) {
      alert(`Error updating schedule: ${e.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDuplicate = async (taskId: string) => {
    try {
      setActionLoadingId(taskId);
      await scraperApi.duplicateTask(taskId);
      await fetchTasks();
    } catch (e: any) {
      alert(`Error duplicating task: ${e.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDelete = async (taskId: string, taskName: string) => {
    if (!confirm(`Are you sure you want to delete task "${taskName}"? This action cannot be undone.`)) {
      return;
    }
    try {
      setActionLoadingId(taskId);
      await scraperApi.deleteTask(taskId);
      await fetchTasks();
    } catch (e: any) {
      alert(`Error deleting task: ${e.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleViewLogs = async (task: ScraperTask) => {
    try {
      setActiveTaskName(task.name);
      setIsLoadingLogs(true);
      const fullTask = await scraperApi.getTask(task.id);
      if (fullTask.recent_runs && fullTask.recent_runs.length > 0) {
        const latestRun = await scraperApi.getRun(fullTask.recent_runs[0].id);
        setActiveLogRun(latestRun);
      } else {
        setActiveLogRun({
          id: "no_runs",
          task_id: task.id,
          run_number: 0,
          execution_mode: task.execution_mode,
          status: "DRAFT",
          duration_seconds: 0,
          records_extracted: 0,
          records_saved: 0,
          records_duplicate: 0,
          logs: [{ timestamp: new Date().toISOString(), level: "INFO", message: "No execution logs yet. Click 'Run' to start extraction." }],
          created_at: new Date().toISOString()
        });
      }
    } catch (e: any) {
      alert(`Failed to load logs: ${e.message}`);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const statusFilters = ["ALL", "RUNNING", "COMPLETED", "FAILED", "PAUSED", "DRAFT"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              Task Management
            </span>
            <span className="text-xs text-slate-400 font-mono">Live Monitoring &amp; History</span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">My Extraction Tasks</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor background extraction status, view terminal execution logs, manage recurring schedules, and export datasets.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/custom-scraper"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition shadow-[0_1px_2px_rgba(15,23,42,0.06)]"
          >
            <Code2 className="w-3.5 h-3.5" />
            Create Task
          </Link>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {statusFilters.map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition ${
                statusFilter === st
                  ? "bg-blue-600 text-white shadow-[0_1px_2px_rgba(15,23,42,0.06)]"
                  : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200/80"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchTasks()}
            placeholder="Search by task name or URL..."
            className="w-full bg-white border border-slate-200/80 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 font-normal text-slate-800"
          />
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white rounded-xl border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 text-slate-500 uppercase tracking-wider text-[11px] font-medium border-b border-slate-200/75">
              <tr>
                <th className="py-3 px-4">Task Name &amp; Target</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Execution</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Records (Total / Dup)</th>
                <th className="py-3 px-3">Schedule</th>
                <th className="py-3 px-3">Last Run</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/80">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    Loading extraction tasks...
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No tasks found. Use a template or open the visual builder to create your first scraper!
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-900 text-[13px]">{task.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono truncate max-w-xs mt-0.5">
                        {task.target_url || "Configured workflow"}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                        {task.task_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
                        {task.execution_mode}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${
                          task.status === "COMPLETED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                            : task.status === "RUNNING"
                            ? "bg-blue-50 text-blue-700 border border-blue-200/60 animate-pulse"
                            : task.status === "FAILED"
                            ? "bg-rose-50 text-rose-700 border border-rose-200/60"
                            : task.status === "PAUSED"
                            ? "bg-amber-50 text-amber-700 border border-amber-200/60"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {task.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900 text-[13px] tabular-nums">{task.total_records}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {task.successful_records} valid • {task.duplicate_records} dup
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <div className="text-slate-700 font-medium">
                        {task.schedule_type === "NONE" ? "Manual" : task.schedule_type}
                      </div>
                      {task.is_schedule_active ? (
                        <span className="text-[10px] text-emerald-600 font-semibold">Active</span>
                      ) : (
                        <span className="text-[10px] text-slate-400">Inactive</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <div className="text-slate-600 font-mono text-[11px]">
                        {task.last_run_at ? new Date(task.last_run_at).toLocaleString() : "Never"}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => handleRunTask(task.id, "CLOUD")}
                        disabled={actionLoadingId === task.id || task.status === "RUNNING"}
                        title="Run Cloud Extraction"
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded transition disabled:opacity-50"
                      >
                        <Play className="w-3 h-3" />
                        Run
                      </button>
                      <button
                        onClick={() => handleViewLogs(task)}
                        title="View Live Execution Logs"
                        className="p-1 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded transition"
                      >
                        <Terminal className="w-3.5 h-3.5" />
                      </button>
                      <Link
                        href={`/data-center?task_id=${task.id}`}
                        title="View Extracted Records"
                        className="p-1 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded transition inline-block"
                      >
                        <Database className="w-3.5 h-3.5" />
                      </Link>
                      <Link
                        href={`/custom-scraper?task_id=${task.id}`}
                        title="Edit in Visual Builder"
                        className="p-1 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded transition inline-block"
                      >
                        <Code2 className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        onClick={() => handlePauseResume(task)}
                        title={task.is_schedule_active ? "Pause Schedule" : "Resume Schedule"}
                        className="p-1 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded transition"
                      >
                        {task.is_schedule_active ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                      </button>
                      <button
                        onClick={() => handleDuplicate(task.id)}
                        title="Duplicate Task"
                        className="p-1 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded transition"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(task.id, task.name)}
                        title="Delete Task"
                        className="p-1 text-slate-400 hover:text-rose-600 bg-slate-50 hover:bg-rose-50 rounded transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Terminal Log Drawer */}
      {activeLogRun && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-end">
          <div className="bg-slate-950 text-slate-200 w-full max-w-2xl h-full shadow-2xl flex flex-col p-6 animate-in slide-in-from-right duration-200 font-mono text-xs">
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-bold text-sm text-white">Live Execution Logs</h3>
                </div>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Task: {activeTaskName} • Run #{activeLogRun.run_number} ({activeLogRun.status})
                </div>
              </div>
              <button
                onClick={() => setActiveLogRun(null)}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Run Stats Bar */}
            <div className="py-3 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
              <div>Mode: <span className="text-slate-200">{activeLogRun.execution_mode}</span></div>
              <div>Duration: <span className="text-slate-200">{activeLogRun.duration_seconds}s</span></div>
              <div>Records Extracted: <span className="text-emerald-400 font-bold">{activeLogRun.records_extracted}</span></div>
              <div>Saved: <span className="text-slate-200">{activeLogRun.records_saved}</span></div>
              <div>Duplicates: <span className="text-amber-400">{activeLogRun.records_duplicate}</span></div>
            </div>

            {/* Terminal Log Console */}
            <div className="flex-1 overflow-y-auto py-4 space-y-2">
              {activeLogRun.logs && activeLogRun.logs.length > 0 ? (
                activeLogRun.logs.map((lg, i) => (
                  <div key={i} className="flex items-start gap-2 text-[11px] leading-relaxed">
                    <span className="text-slate-600 select-none">{lg.timestamp ? lg.timestamp.split("T")[1]?.slice(0, 8) : "--:--:--"}</span>
                    <span
                      className={`px-1 py-0.2 rounded text-[9px] font-bold uppercase ${
                        lg.level === "ERROR"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : lg.level === "WARNING"
                          ? "bg-amber-950 text-amber-400 border border-amber-800"
                          : "bg-blue-950 text-blue-400 border border-blue-800"
                      }`}
                    >
                      {lg.level}
                    </span>
                    <span className="text-slate-300 flex-1">{lg.message}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 py-8 text-center">No log events recorded for this run.</div>
              )}
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">Live stream connected via ProspectOS Worker</span>
              <button
                onClick={() => setActiveLogRun(null)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs transition"
              >
                Close Console
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

