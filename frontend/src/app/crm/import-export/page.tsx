"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowUpDown,
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Filter,
  FileText
} from "lucide-react";
import { crmApi } from "@/lib/crmApi";

export default function ImportExportPage() {
  // Import State
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  // Export State
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");
  const [exportStage, setExportStage] = useState("");
  const [exportCountry, setExportCountry] = useState("");
  const [exportIndustry, setExportIndustry] = useState("");

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setImportText(content);
    };
    reader.readAsText(file);
  };

  const handleRunImport = async () => {
    if (!importText.trim()) {
      alert("Please upload a file or paste CSV/JSON lead rows first.");
      return;
    }

    try {
      setImporting(true);
      let parsedLeads: any[] = [];

      // Check if JSON
      if (importText.trim().startsWith("[") || importText.trim().startsWith("{")) {
        const parsed = JSON.parse(importText);
        parsedLeads = Array.isArray(parsed) ? parsed : [parsed];
      } else {
        // Parse simple CSV
        const lines = importText.trim().split("\n");
        if (lines.length < 2) throw new Error("CSV must have at least a header and one data row.");
        const headers = lines[0].split(",").map((h) => h.trim().toLowerCase().replace(/"/g, ""));
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(",").map((v) => v.trim().replace(/"/g, ""));
          const leadObj: Record<string, any> = {};
          headers.forEach((h, idx) => {
            if (values[idx]) {
              if (h.includes("name") || h.includes("company")) leadObj["company_name"] = values[idx];
              else if (h.includes("domain") || h.includes("website") || h.includes("url")) leadObj["website_url"] = values[idx];
              else if (h.includes("email")) leadObj["email"] = values[idx];
              else if (h.includes("phone")) leadObj["phone"] = values[idx];
              else if (h.includes("country")) leadObj["country"] = values[idx];
              else if (h.includes("industry")) leadObj["industry"] = values[idx];
              else leadObj[h] = values[idx];
            }
          });
          if (Object.keys(leadObj).length > 0) {
            parsedLeads.push(leadObj);
          }
        }
      }

      const res = await crmApi.importBatchLeads(parsedLeads);
      setImportResult(res);
      setImportText("");
    } catch (e: any) {
      alert(`Import error: ${e.message}`);
    } finally {
      setImporting(false);
    }
  };

  const handleExport = () => {
    const filters: Record<string, string> = {};
    if (exportStage) filters.stage = exportStage;
    if (exportCountry) filters.country = exportCountry;
    if (exportIndustry) filters.industry = exportIndustry;

    const url = crmApi.getExportUrl(exportFormat, filters);
    window.open(url, "_blank");
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Data Ingestion & Extraction
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">CRM Lead Import & Export Center</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Ingest external CSV/JSON lead spreadsheets with automatic deduplication, or export filtered CRM cohorts.
          </p>
        </div>

        <Link
          href="/crm"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
        >
          View Leads Directory
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Import Box */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-slate-900">Batch Lead Import</h2>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Upload CSV or paste JSON lead payloads. Canonical domains are automatically normalized and checked against existing CRM records.
          </p>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Upload CSV or JSON file</label>
              <input
                type="file"
                accept=".csv, .json, .txt"
                onChange={handleFileUpload}
                className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Or paste raw CSV / JSON text</label>
              <textarea
                rows={5}
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder="company_name,website,email,country&#10;Acme Corp,acme.com,contact@acme.com,United States"
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs font-mono outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              onClick={handleRunImport}
              disabled={importing || !importText.trim()}
              className="w-full py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition shadow-sm"
            >
              {importing ? "Importing & Deduplicating..." : "Execute Batch Ingestion"}
            </button>
          </div>

          {importResult && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                <CheckCircle2 className="w-4 h-4" />
                <span>Import Complete</span>
              </div>
              <p className="text-emerald-700">
                Added {importResult.added} new leads, merged {importResult.updated} existing companies, skipped {importResult.skipped} duplicates.
              </p>
            </div>
          )}
        </div>

        {/* Export Box */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Download className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-slate-900">Filtered CRM Export</h2>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Download your lead intelligence records in CSV or JSON format with optional stage, country, and industry criteria.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Export Format</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setExportFormat("csv")}
                  className={`py-2 text-center rounded-lg border font-semibold transition ${
                    exportFormat === "csv"
                      ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                      : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  CSV Spreadsheet
                </button>
                <button
                  type="button"
                  onClick={() => setExportFormat("json")}
                  className={`py-2 text-center rounded-lg border font-semibold transition ${
                    exportFormat === "json"
                      ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                      : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  JSON Payload
                </button>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Filter by Sales Stage</label>
              <select
                value={exportStage}
                onChange={(e) => setExportStage(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-medium"
              >
                <option value="">All Stages</option>
                <option value="NEW">New</option>
                <option value="QUALIFIED">Qualified</option>
                <option value="RESEARCHED">Researching</option>
                <option value="CONTACTED">Contacted</option>
                <option value="WON">Closed Won</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Country</label>
                <input
                  type="text"
                  value={exportCountry}
                  onChange={(e) => setExportCountry(e.target.value)}
                  placeholder="e.g. Mexico"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Industry</label>
                <input
                  type="text"
                  value={exportIndustry}
                  onChange={(e) => setExportIndustry(e.target.value)}
                  placeholder="e.g. E-Commerce"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <button
              onClick={handleExport}
              className="w-full py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm shadow-indigo-500/20"
            >
              Download Export
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

