"use client";

import { useEffect, useState } from "react";
import {
  api,
  GoogleDriveStatus,
  GoogleDriveSyncJob
} from "@/lib/api";
import {
  HardDrive,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Folder,
  FileSpreadsheet,
  Lock,
  Zap,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Sliders,
  Radio,
  FileText
} from "lucide-react";

export default function GoogleDrivePage() {
  const [status, setStatus] = useState<GoogleDriveStatus | null>(null);
  const [syncJobs, setSyncJobs] = useState<GoogleDriveSyncJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [syncAllLoading, setSyncAllLoading] = useState(false);

  // Manual connect modal / form states
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [accountEmail, setAccountEmail] = useState("");
  const [folderPath, setFolderPath] = useState("ProspectOS/Leads/Mexico/E-commerce/");
  const [exportFormat, setExportFormat] = useState("GOOGLE_SHEETS");
  const [autoSync, setAutoSync] = useState(true);

  // Messages
  const [notice, setNotice] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const showNotice = (type: "success" | "error" | "info", message: string) => {
    setNotice({ type, message });
    setTimeout(() => setNotice(null), 7000);
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [st, jobs] = await Promise.all([
        api.getGDriveStatus().catch(() => null),
        api.getGDriveSyncJobs(30).catch(() => [])
      ]);
      if (st) {
        setStatus(st);
        if (st.selected_folder_path) setFolderPath(st.selected_folder_path);
        if (st.export_format) setExportFormat(st.export_format);
        setAutoSync(st.auto_sync_enabled);
      }
      setSyncJobs(jobs);
    } catch (err: any) {
      showNotice("error", err.message || "Failed to load Google Drive settings");
    } finally {
      setLoading(false);
    }
  };

  const handleManualConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clientId.trim() || !clientSecret.trim() || !refreshToken.trim()) {
      showNotice("error", "Client ID, Client Secret, and Refresh Token are required.");
      return;
    }

    setActionLoading(true);
    try {
      const res = await api.connectGDriveManual({
        client_id: clientId.trim(),
        client_secret: clientSecret.trim(),
        refresh_token: refreshToken.trim(),
        account_email: accountEmail.trim() || undefined,
        selected_folder_path: folderPath.trim()
      });
      showNotice("success", `Google Drive successfully linked to ${res.account_email}! Master sheet created.`);
      await loadData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to connect Google Drive.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect Google Drive? Leads in CRM will not be deleted, but auto-sync will be paused.")) return;
    setActionLoading(true);
    try {
      await api.disconnectGDrive();
      showNotice("info", "Google Drive disconnected.");
      await loadData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to disconnect Google Drive.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateSettings = async () => {
    setActionLoading(true);
    try {
      await api.updateGDriveSettings({
        selected_folder_path: folderPath,
        export_format: exportFormat,
        auto_sync_enabled: autoSync
      });
      showNotice("success", "Google Drive sync settings updated.");
      await loadData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to update settings.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSyncAll = async () => {
    setSyncAllLoading(true);
    try {
      const res = await api.syncAllToGDrive();
      showNotice("success", `Batch synchronization initiated for ${res.candidate_count} eligible CRM prospects.`);
      await loadData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to trigger batch sync.");
    } finally {
      setSyncAllLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16 px-4 sm:px-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-bold bg-blue-100 text-blue-800 rounded">Module D & G</span>
            <span className="px-2 py-0.5 text-xs font-bold bg-emerald-100 text-emerald-800 rounded">Official Google Drive API</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 flex items-center mt-1">
            <HardDrive className="w-7 h-7 mr-3 text-blue-600" /> Google Drive Live Synchronization
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automatically export and synchronize verified SEO prospects into your Google Drive Master Sheet.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
          >
            <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          {status?.connected && (
            <button
              onClick={handleSyncAll}
              disabled={syncAllLoading}
              className="inline-flex items-center px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-sm transition disabled:opacity-50"
            >
              <Zap className={`w-3.5 h-3.5 mr-1.5 ${syncAllLoading ? "animate-spin" : ""}`} /> Sync All Leads
            </button>
          )}
        </div>
      </div>

      {/* Notice Banner */}
      {notice && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center gap-2.5 ${
            notice.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : notice.type === "error"
              ? "bg-red-50 border-red-200 text-red-800"
              : "bg-blue-50 border-blue-200 text-blue-800"
          }`}
        >
          {notice.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span>{notice.message}</span>
        </div>
      )}

      {/* Main Status & Connection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4 md:col-span-1">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-800">Connection Health</h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                status?.connected
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                  : "bg-slate-100 text-slate-700 border border-slate-200"
              }`}
            >
              {status?.connected ? "CONNECTED" : "DISCONNECTED"}
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500">Connected Account:</span>
              <div className="font-semibold text-slate-900 mt-0.5">
                {status?.account_email || "Not Connected"}
              </div>
            </div>

            <div>
              <span className="text-slate-500">Total Synced Records:</span>
              <div className="font-bold text-xl text-blue-700 mt-0.5">
                {status?.total_synced_records || 0}
              </div>
            </div>

            <div>
              <span className="text-slate-500">Last Successful Sync:</span>
              <div className="font-medium text-slate-700 mt-0.5">
                {status?.last_successful_sync
                  ? new Date(status.last_successful_sync).toLocaleString()
                  : "No syncs completed yet"}
              </div>
            </div>

            {status?.last_error_message && (
              <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg text-red-700 text-[11px]">
                <strong>Last Error:</strong> {status.last_error_message}
              </div>
            )}
          </div>

          {status?.connected && status.master_sheet_url && (
            <div className="pt-2">
              <a
                href={status.master_sheet_url}
                target="_blank"
                rel="noreferrer"
                className="w-full inline-flex items-center justify-center px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition"
              >
                <FileSpreadsheet className="w-4 h-4 mr-2" /> Open Master Google Sheet <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
              </a>
            </div>
          )}

          {status?.connected && (
            <div className="pt-1">
              <button
                onClick={handleDisconnect}
                disabled={actionLoading}
                className="w-full text-xs font-semibold text-red-600 hover:text-red-800 p-2 border border-red-200 rounded-lg hover:bg-red-50 transition"
              >
                Disconnect Account
              </button>
            </div>
          )}
        </div>

        {/* Configuration / Settings Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm md:col-span-2 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-800">Destination Structure & Sync Policy</h2>
            </div>
            <span className="text-xs text-slate-500">PostgreSQL is system of record</span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Destination Folder Hierarchy *
              </label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Folder className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="text"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder="ProspectOS/Leads/Mexico/E-commerce/"
                />
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Hierarchical folder in your Google Drive root where prospect sheets and exports will reside.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Export Format
                </label>
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value)}
                  className="mt-1 block w-full py-2 px-3 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="GOOGLE_SHEETS">Google Sheets (Master Structured Sheet)</option>
                  <option value="CSV">CSV File Export</option>
                  <option value="JSON">JSON File Export</option>
                </select>
              </div>

              <div className="flex items-center pt-5">
                <label className="flex items-center space-x-2.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoSync}
                    onChange={(e) => setAutoSync(e.target.checked)}
                    className="h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                  />
                  <span className="font-semibold">Automatic Lead Synchronization</span>
                </label>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={handleUpdateSettings}
                disabled={actionLoading}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
              >
                Save Sync Policy
              </button>
            </div>
          </div>

          {/* Secure OAuth & Credentials Setup */}
          {!status?.connected && (
            <div className="pt-5 border-t border-slate-100 space-y-4">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-slate-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                  Link Google Drive via OAuth 2.0 Credentials
                </h3>
              </div>
              <p className="text-xs text-slate-500">
                To connect your Google Drive without exposing secrets, enter your Google Cloud OAuth Client ID, Secret, and Refresh Token. Tokens are protected on the backend using AES-256 encryption.
              </p>

              <form onSubmit={handleManualConnect} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Google Client ID"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  className="py-1.5 px-3 text-xs border border-slate-300 rounded-lg"
                  required
                />
                <input
                  type="password"
                  placeholder="Google Client Secret"
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  className="py-1.5 px-3 text-xs border border-slate-300 rounded-lg"
                  required
                />
                <input
                  type="password"
                  placeholder="Google OAuth Refresh Token"
                  value={refreshToken}
                  onChange={(e) => setRefreshToken(e.target.value)}
                  className="py-1.5 px-3 text-xs border border-slate-300 rounded-lg"
                  required
                />
                <input
                  type="email"
                  placeholder="Account Email (e.g. saqlain@grokxseo.online)"
                  value={accountEmail}
                  onChange={(e) => setAccountEmail(e.target.value)}
                  className="py-1.5 px-3 text-xs border border-slate-300 rounded-lg"
                />

                <div className="sm:col-span-2 pt-1">
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition"
                  >
                    {actionLoading ? "Connecting & Initializing Master Sheet..." : "Connect Google Drive & Initialize Sheet"}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* Sync Jobs Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Google Drive Synchronization History</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Idempotent audit log of all exported prospect records, row mappings, and retry outcomes.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Total Logged: {syncJobs.length}</span>
        </div>

        {syncJobs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No synchronization jobs logged yet. Newly saved CRM leads will appear here automatically.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-bold text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Sync Status</th>
                  <th className="py-3 px-4">Retries</th>
                  <th className="py-3 px-4">Drive File / Sheet</th>
                  <th className="py-3 px-4">Synced At</th>
                  <th className="py-3 px-4">Error Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {syncJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {job.company_name}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          job.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-800"
                            : job.status === "FAILED"
                            ? "bg-red-100 text-red-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-600">
                      {job.retry_count}
                    </td>
                    <td className="py-3 px-4">
                      {job.gdrive_file_url ? (
                        <a
                          href={job.gdrive_file_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:underline flex items-center gap-1"
                        >
                          View Sheet <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-slate-400 font-mono">{job.gdrive_file_id || "—"}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {job.sync_completed_at
                        ? new Date(job.sync_completed_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-slate-500 max-w-xs truncate">
                      {job.error_message || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
