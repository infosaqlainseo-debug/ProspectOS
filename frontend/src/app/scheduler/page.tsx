"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarClock,
  Clock,
  Play,
  Pause,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Plus,
  Sliders,
  Settings2,
  Calendar,
  Layers,
  ArrowRight,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { scraperApi, ScraperTask } from "@/lib/scraperApi";

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<ScraperTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeModalTask, setActiveModalTask] = useState<ScraperTask | null>(null);

  // Modal Form State
  const [scheduleType, setScheduleType] = useState<string>("DAILY");
  const [scheduleTimezone, setScheduleTimezone] = useState<string>("UTC");
  const [isScheduleActive, setIsScheduleActive] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const res = await scraperApi.getTasks({ limit: 100 });
      if (res && res.items) {
        setTasks(res.items);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const scheduledTasks = tasks.filter((t) => t.schedule_type !== "NONE");
  const nonScheduledTasks = tasks.filter((t) => t.schedule_type === "NONE");

  const openScheduleModal = (task: ScraperTask) => {
    setActiveModalTask(task);
    setScheduleType(task.schedule_type === "NONE" ? "DAILY" : task.schedule_type);
    setScheduleTimezone(task.schedule_timezone || "UTC");
    setIsScheduleActive(task.is_schedule_active);
  };

  const handleSaveSchedule = async () => {
    if (!activeModalTask) return;
    try {
      setIsSaving(true);
      await scraperApi.updateTask(activeModalTask.id, {
        schedule_type: scheduleType,
        schedule_timezone: scheduleTimezone,
        is_schedule_active: isScheduleActive
      });
      await fetchTasks();
      setActiveModalTask(null);
    } catch (e: any) {
      alert(`Failed to update schedule: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleActive = async (task: ScraperTask) => {
    try {
      if (task.is_schedule_active) {
        await scraperApi.pauseTask(task.id);
      } else {
        await scraperApi.resumeTask(task.id);
      }
      await fetchTasks();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Module I: Task Scheduling & Incremental Extraction
            </span>
            <span className="text-xs text-slate-400 font-mono">Automated Cron Timers</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Task Scheduler</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Configure automated recurring scrapers with deduplication safeguards to discover newly published records incrementally.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Incremental Extraction Feature Highlight */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-blue-800/40 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-bold tracking-wide uppercase text-blue-200">
              Deterministic Incremental Extraction
            </h2>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed">
            Every scheduled run calculates a cryptographic SHA-256 fingerprint from the extracted domain, URL, and business name. Newly discovered leads are highlighted, while unchanged records are flagged to prevent duplicate clutter.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="p-3 bg-white/10 rounded-xl border border-white/20 text-center">
            <div className="text-xl font-bold text-white">{scheduledTasks.filter((t) => t.is_schedule_active).length}</div>
            <div className="text-[10px] text-blue-200 font-medium uppercase tracking-wider">Active Cron Schedules</div>
          </div>
        </div>
      </div>

      {/* Scheduled Tasks List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Active Recurring Schedules</h2>
            <p className="text-xs text-slate-500">Tasks configured with recurring execution triggers</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{scheduledTasks.length} Configured</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Task Name</th>
                <th className="py-3 px-3">Interval</th>
                <th className="py-3 px-3">Timezone</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Next Scheduled Execution</th>
                <th className="py-3 px-3">Last Run</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scheduledTasks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-400">
                    No recurring schedules configured yet. Click &quot;Configure Schedule&quot; on any task below!
                  </td>
                </tr>
              ) : (
                scheduledTasks.map((task) => (
                  <tr key={task.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{task.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono truncate max-w-xs">{task.target_url}</div>
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{task.schedule_type}</td>
                    <td className="py-3 px-3 font-mono text-slate-500">{task.schedule_timezone}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          task.is_schedule_active
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {task.is_schedule_active ? "Active" : "Paused"}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                      {task.next_run_at ? new Date(task.next_run_at).toLocaleString() : "Pending run"}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-500">
                      {task.last_run_at ? new Date(task.last_run_at).toLocaleString() : "Never"}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleToggleActive(task)}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold transition ${
                          task.is_schedule_active
                            ? "bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200"
                            : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200"
                        }`}
                      >
                        {task.is_schedule_active ? "Pause" : "Resume"}
                      </button>
                      <button
                        onClick={() => openScheduleModal(task)}
                        className="px-2.5 py-1 rounded text-[11px] font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Unscheduled Tasks Ready for Scheduling */}
      {nonScheduledTasks.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Unscheduled Tasks Ready for Automation</h2>
            <p className="text-xs text-slate-500">Enable recurring scheduling on these existing extraction tasks</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {nonScheduledTasks.map((t) => (
              <div key={t.id} className="p-3 rounded-lg border border-slate-200 hover:border-slate-300 flex items-center justify-between text-xs">
                <div>
                  <div className="font-bold text-slate-800 truncate max-w-[200px]">{t.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{t.total_records} records</div>
                </div>
                <button
                  onClick={() => openScheduleModal(t)}
                  className="px-2.5 py-1 text-xs font-semibold text-blue-600 hover:bg-blue-50 border border-blue-200 rounded transition"
                >
                  Schedule
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Edit Schedule Modal */}
      {activeModalTask && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Configure Task Schedule</h3>
            <p className="text-xs text-slate-500">Task: {activeModalTask.name}</p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Execution Interval</label>
                <select
                  value={scheduleType}
                  onChange={(e) => setScheduleType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs"
                >
                  <option value="HOURLY">Hourly (Every 60 minutes)</option>
                  <option value="DAILY">Daily (Every 24 hours)</option>
                  <option value="WEEKLY">Weekly (Every 7 days)</option>
                  <option value="MONTHLY">Monthly (Every 30 days)</option>
                  <option value="CUSTOM">Custom Interval (6 hours)</option>
                  <option value="NONE">Manual Execution Only</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Timezone</label>
                <select
                  value={scheduleTimezone}
                  onChange={(e) => setScheduleTimezone(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs"
                >
                  <option value="UTC">UTC (Universal Coordinated Time)</option>
                  <option value="America/Mexico_City">America/Mexico_City (CST)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-700">Activate Schedule Immediately</span>
                <input
                  type="checkbox"
                  checked={isScheduleActive}
                  onChange={(e) => setIsScheduleActive(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                onClick={() => setActiveModalTask(null)}
                className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSchedule}
                disabled={isSaving}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm"
              >
                {isSaving ? "Saving..." : "Save Schedule"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

