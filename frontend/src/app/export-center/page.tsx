"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Download,
  FileSpreadsheet,
  FileText,
  FileCode,
  Database,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Server,
  ShieldCheck
} from "lucide-react";
import { scraperApi, ScraperTask } from "@/lib/scraperApi";

export default function ExportCenterPage() {
  const [tasks, setTasks] = useState<ScraperTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("ALL");
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [exportHistory, setExportHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // DB Connector Form State
  const [dbType, setDbType] = useState<string>("postgresql");
  const [dbHost, setDbHost] = useState<string>("localhost");
  const [dbPort, setDbPort] = useState<number>(5432);
  const [dbName, setDbName] = useState<string>("prospectos_leads");
  const [dbUsername, setDbUsername] = useState<string>("postgres");
  const [dbPassword, setDbPassword] = useState<string>("");
  const [dbTable, setDbTable] = useState<string>("extracted_companies");
  const [isTestingDb, setIsTestingDb] = useState(false);
  const [dbTestMessage, setDbTestMessage] = useState<string | null>(null);

  const fetchExportHistory = async () => {
    try {
      setLoadingHistory(true);
      const res = await scraperApi.getExportHistory();
      if (res && res.items) {
        setExportHistory(res.items);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await scraperApi.getTasks({ limit: 100 });
      if (res && res.items) setTasks(res.items);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchExportHistory();
    fetchTasks();
  }, []);

  const handleCreateExport = async (format: string) => {
    try {
      setIsExporting(format);
      const res = await scraperApi.createExport({
        format,
        task_id: selectedTaskId === "ALL" ? undefined : selectedTaskId
      });
      await fetchExportHistory();
      // Trigger download in browser
      window.open(res.download_url, "_blank");
    } catch (e: any) {
      alert(`Export failed: ${e.message}`);
    } finally {
      setIsExporting(null);
    }
  };

  const handleTestDbConnection = async () => {
    try {
      setIsTestingDb(true);
      const res = await scraperApi.testDatabase({
        db_type: dbType,
        host: dbHost,
        port: dbPort,
        database: dbName,
        username: dbUsername,
        password: dbPassword,
        table_name: dbTable
      });
      setDbTestMessage(`Success: ${res.message}`);
    } catch (e: any) {
      setDbTestMessage(`Error: ${e.message}`);
    } finally {
      setIsTestingDb(false);
    }
  };

  const exportFormats = [
    { format: "CSV", label: "CSV Spreadsheet", desc: "Comma-separated UTF-8 values compatible with Excel, Google Sheets, and CRM imports.", icon: FileSpreadsheet, color: "text-emerald-600 bg-emerald-50" },
    { format: "XLSX", label: "Microsoft Excel (XLSX)", desc: "Formatted Excel workbook with bold headers, navy styling, and auto-sized column widths.", icon: FileSpreadsheet, color: "text-blue-600 bg-blue-50" },
    { format: "JSON", label: "JSON Data Stream", desc: "Structured hierarchical JSON array ideal for programmatic API ingest and data pipelines.", icon: FileCode, color: "text-indigo-600 bg-indigo-50" },
    { format: "HTML", label: "HTML Styled Table", desc: "Self-contained interactive HTML document ready to open directly in any browser.", icon: FileText, color: "text-purple-600 bg-purple-50" },
    { format: "XML", label: "XML Schema Document", desc: "Standard XML formatted tree document compatible with enterprise legacy integrations.", icon: FileCode, color: "text-amber-600 bg-amber-50" },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              Module K: Export Center & Database Sync
            </span>
            <span className="text-xs text-slate-400 font-mono">5 Output Formats Supported</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Data Export Center</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Download your extracted intelligence into CSV, Excel XLSX, JSON, HTML, and XML formats or configure direct database sync.
          </p>
        </div>
      </div>

      {/* Scope Filter Bar */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Export Scope:</span>
          <select
            value={selectedTaskId}
            onChange={(e) => setSelectedTaskId(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-800"
          >
            <option value="ALL">All Extracted Records (Global Dataset)</option>
            {tasks.map((t) => (
              <option key={t.id} value={t.id}>
                Task: {t.name} ({t.total_records} records)
              </option>
            ))}
          </select>
        </div>
        <div className="text-slate-500 text-[11px]">
          Files are generated with UTF-8 character encoding and sanitized data types.
        </div>
      </div>

      {/* Export Format Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {exportFormats.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.format}
              className="p-5 bg-white rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${item.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 font-mono">
                    .{item.format.toLowerCase()}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">{item.label}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <button
                  onClick={() => handleCreateExport(item.format)}
                  disabled={isExporting === item.format}
                  className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  {isExporting === item.format ? "Generating..." : `Download ${item.format}`}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Column Layout: Export History vs Database Connector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Export History (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Recent Generated Exports</h2>
              <p className="text-xs text-slate-500">History of generated dataset files ready for download</p>
            </div>
            <button onClick={fetchExportHistory} className="text-slate-400 hover:text-slate-600">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="py-3 px-4">Format</th>
                  <th className="py-3 px-3">Records</th>
                  <th className="py-3 px-3">File Size</th>
                  <th className="py-3 px-3">Timestamp</th>
                  <th className="py-3 px-4 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {exportHistory.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No exports generated yet. Click any format above to download!
                    </td>
                  </tr>
                ) : (
                  exportHistory.map((ex) => (
                    <tr key={ex.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 font-mono">
                          {ex.format}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-800">{ex.record_count}</td>
                      <td className="py-3 px-3 font-mono text-slate-500 text-[11px]">
                        {ex.file_size_bytes > 1024
                          ? `${(ex.file_size_bytes / 1024).toFixed(1)} KB`
                          : `${ex.file_size_bytes} B`}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-500">
                        {ex.created_at ? new Date(ex.created_at).toLocaleString() : "--"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <a
                          href={ex.download_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition"
                        >
                          <Download className="w-3 h-3" />
                          Download
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Direct Database Export Connector (1 col) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-600" />
            <h3 className="font-bold text-sm text-slate-900">Direct Database Sync</h3>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Configure direct target database export to PostgreSQL, MySQL, or SQL Server.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Database Engine</label>
              <select
                value={dbType}
                onChange={(e) => setDbType(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-xs font-medium"
              >
                <option value="postgresql">PostgreSQL (Relational)</option>
                <option value="mysql">MySQL 8.0+</option>
                <option value="mssql">Microsoft SQL Server</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Host</label>
                <input
                  type="text"
                  value={dbHost}
                  onChange={(e) => setDbHost(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Port</label>
                <input
                  type="number"
                  value={dbPort}
                  onChange={(e) => setDbPort(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-xs font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Database Name</label>
              <input
                type="text"
                value={dbName}
                onChange={(e) => setDbName(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Target Table Name</label>
              <input
                type="text"
                value={dbTable}
                onChange={(e) => setDbTable(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-xs font-mono"
              />
            </div>

            {dbTestMessage && (
              <div
                className={`p-2.5 rounded-lg text-[11px] ${
                  dbTestMessage.startsWith("Success")
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {dbTestMessage}
              </div>
            )}

            <button
              onClick={handleTestDbConnection}
              disabled={isTestingDb}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-lg transition"
            >
              {isTestingDb ? "Testing Connection..." : "Test Connection & Schema"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

