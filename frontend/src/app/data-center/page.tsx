"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Database,
  Search,
  Filter,
  Download,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  RefreshCw,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  X,
  FileSpreadsheet,
  Users,
  Check,
  UserPlus
} from "lucide-react";
import { scraperApi, ExtractedRecord } from "@/lib/scraperApi";
import { crmApi, ScraperImportResponse } from "@/lib/crmApi";

export default function DataCenterPage() {
  const [records, setRecords] = useState<ExtractedRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [validationFilter, setValidationFilter] = useState("ALL");
  const [qualityFilter, setQualityFilter] = useState("ALL");
  const [duplicateFilter, setDuplicateFilter] = useState("ALL");
  const [page, setPage] = useState(1);
  const limit = 25;

  // Selection for bulk actions & Save to CRM
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [savingToCrm, setSavingToCrm] = useState(false);
  const [crmImportResult, setCrmImportResult] = useState<ScraperImportResponse | null>(null);

  // Record Inspector Modal State
  const [selectedRecord, setSelectedRecord] = useState<ExtractedRecord | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const res = await scraperApi.getData({
        search: searchQuery || undefined,
        validation_status: validationFilter === "ALL" ? undefined : validationFilter,
        quality_status: qualityFilter === "ALL" ? undefined : qualityFilter,
        is_duplicate: duplicateFilter === "ALL" ? undefined : duplicateFilter === "DUPLICATES",
        limit,
        offset: (page - 1) * limit
      });
      if (res && res.items) {
        setRecords(res.items);
        setTotal(res.total);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [page, validationFilter, qualityFilter, duplicateFilter]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(records.map((r) => r.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleSaveToCrm = async (recordIds?: string[]) => {
    try {
      setSavingToCrm(true);
      const targetIds = recordIds || (selectedIds.size > 0 ? Array.from(selectedIds) : undefined);
      const res = await crmApi.importFromScraper({
        extracted_record_ids: targetIds,
        auto_save_valid_only: true,
        conflict_resolution: "MERGE"
      });
      setCrmImportResult(res);
      setSelectedIds(new Set());
    } catch (e: any) {
      alert(e.message || "Failed to save leads to CRM");
    } finally {
      setSavingToCrm(false);
    }
  };

  const handleCleanAll = async () => {
    try {
      setActionMessage("Running data cleaning & normalization pipeline...");
      const res = await scraperApi.cleanData();
      setActionMessage(res.message);
      await fetchRecords();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDeduplicate = async () => {
    try {
      setActionMessage("Scanning dataset for duplicates via cryptographic hashes...");
      const res = await scraperApi.deduplicateData();
      setActionMessage(res.message);
      await fetchRecords();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleInspectRow = async (id: string) => {
    try {
      const rec = await scraperApi.getRecord(id);
      setSelectedRecord(rec);
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              Module J & M: Centralized Data Center
            </span>
            <span className="text-xs text-slate-400 font-mono">{total} Structured Leads</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Extracted Records & Lead Intelligence</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Query, validate, inspect raw vs normalized values, and save qualified leads directly into the CRM database.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Save to CRM button */}
          <button
            onClick={() => handleSaveToCrm()}
            disabled={savingToCrm}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition shadow-sm shadow-indigo-500/20"
          >
            <Users className="w-3.5 h-3.5" />
            {savingToCrm
              ? "Saving to CRM..."
              : selectedIds.size > 0
              ? `Save Selected (${selectedIds.size}) to CRM`
              : "Save All Valid to CRM"}
          </button>
          <button
            onClick={handleCleanAll}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            Clean Data
          </button>
          <button
            onClick={handleDeduplicate}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
          >
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            Deduplicate
          </button>
          <Link
            href="/export-center"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm shadow-blue-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            Export Center
          </Link>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs font-medium text-blue-700 flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-slate-600">×</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchRecords()}
              placeholder="Search company name, domain, email, industry..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <select
              value={validationFilter}
              onChange={(e) => { setValidationFilter(e.target.value); setPage(1); }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              <option value="ALL">All Validations</option>
              <option value="VALID">Valid (Verified)</option>
              <option value="PARTIAL">Partial</option>
              <option value="FAILED">Failed</option>
            </select>

            <select
              value={qualityFilter}
              onChange={(e) => { setQualityFilter(e.target.value); setPage(1); }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              <option value="ALL">All Quality Levels</option>
              <option value="HIGH">High (Score ≥ 70)</option>
              <option value="MEDIUM">Medium (Score 45-69)</option>
              <option value="LOW">Low (Score &lt; 45)</option>
            </select>

            <select
              value={duplicateFilter}
              onChange={(e) => { setDuplicateFilter(e.target.value); setPage(1); }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              <option value="ALL">All Records</option>
              <option value="UNIQUE">Unique Only</option>
              <option value="DUPLICATES">Flagged Duplicates</option>
            </select>

            <button
              onClick={fetchRecords}
              className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-100 rounded-lg transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* High-Density Data Table */}
      <div className="bg-white rounded-xl border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 text-slate-500 uppercase tracking-wider text-[11px] font-medium border-b border-slate-200/75">
              <tr>
                <th className="py-3 px-3 w-8">
                  <input
                    type="checkbox"
                    checked={records.length > 0 && selectedIds.size === records.length}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="py-3 px-3">Company Name</th>
                <th className="py-3 px-3">Website / Domain</th>
                <th className="py-3 px-3">Email</th>
                <th className="py-3 px-3">Phone</th>
                <th className="py-3 px-3">Address</th>
                <th className="py-3 px-3">Quality Score</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/80">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    Loading records from Data Center...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No records match the active search criteria. Run an extraction task to populate records!
                  </td>
                </tr>
              ) : (
                records.map((r) => {
                  const isSelected = selectedIds.has(r.id);
                  return (
                    <tr key={r.id} className={`hover:bg-slate-50/60 transition-colors ${isSelected ? "bg-blue-50/20" : ""}`}>
                      <td className="py-3 px-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(r.id)}
                          className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="py-3 px-3 font-medium text-slate-900 text-[13px] max-w-[200px] truncate">
                        {r.company_name || "Untitled Entity"}
                      </td>
                      <td className="py-3 px-3">
                        {r.website ? (
                          <a
                            href={r.website}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline flex items-center gap-1 font-mono text-[11px]"
                          >
                            <span className="truncate max-w-[180px]">{r.domain || r.website}</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        ) : (
                          <span className="text-slate-400 font-mono">--</span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                        {r.email || <span className="text-slate-400">--</span>}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                        {r.phone || <span className="text-slate-400">--</span>}
                      </td>
                      <td className="py-3 px-3 text-slate-600 max-w-[180px] truncate">
                        {r.address || <span className="text-slate-400">--</span>}
                      </td>
                      <td className="py-3 px-3 font-mono">
                        <span className="font-semibold text-slate-900 text-[13px] tabular-nums">{r.quality_score}</span>
                        <span className="text-[10px] text-slate-400">/100</span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${
                            r.validation_status === "VALID"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/50"
                              : r.validation_status === "PARTIAL"
                              ? "bg-amber-50 text-amber-700 border border-amber-200/50"
                              : "bg-rose-50 text-rose-700 border border-rose-200/50"
                          }`}
                        >
                          {r.validation_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1.5">
                        <button
                          onClick={() => handleSaveToCrm([r.id])}
                          title="Save single lead to CRM"
                          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded transition"
                        >
                          <UserPlus className="w-3 h-3" />
                          CRM
                        </button>
                        <button
                          onClick={() => handleInspectRow(r.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition"
                        >
                          <Eye className="w-3 h-3" />
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3.5 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing {records.length} of {total} records (Page {page} of {Math.max(1, Math.ceil(total / limit))})
            {selectedIds.size > 0 && (
              <span className="ml-2 font-semibold text-indigo-600">
                • {selectedIds.size} records selected
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 rounded bg-white border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold px-2">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / limit)}
              className="p-1 rounded bg-white border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* CRM Import Result Modal */}
      {crmImportResult && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Leads Saved to CRM</h3>
                <p className="text-xs text-slate-500">Records processed through deduplication & enrichment</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-100 text-center">
              <div>
                <div className="text-xl font-bold text-emerald-600">{crmImportResult.added}</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Added New</div>
              </div>
              <div>
                <div className="text-xl font-bold text-blue-600">{crmImportResult.updated}</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Merged / Updated</div>
              </div>
              <div>
                <div className="text-xl font-bold text-slate-400">{crmImportResult.skipped}</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Duplicates Skipped</div>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {crmImportResult.message}
            </p>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setCrmImportResult(null)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                Close
              </button>
              <Link
                href="/crm"
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm"
              >
                Open in CRM
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Record Inspector Slide-Over / Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-start justify-between pb-4 border-b border-slate-200">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">{selectedRecord.company_name}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    selectedRecord.validation_status === "VALID" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                  }`}>
                    {selectedRecord.validation_status}
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-mono mt-0.5">{selectedRecord.domain || selectedRecord.source_url}</p>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Extracted Details */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">Public Email</span>
                <p className="font-mono text-slate-800">{selectedRecord.email || "Not found"}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">Business Phone</span>
                <p className="font-mono text-slate-800">{selectedRecord.phone || "Not found"}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">Location / Address</span>
                <p className="text-slate-800">{selectedRecord.address || "Not specified"}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">Quality Score</span>
                <p className="font-bold text-slate-900">{selectedRecord.quality_score} / 100</p>
              </div>
            </div>

            {/* Raw JSON Data */}
            <div className="space-y-1.5">
              <h4 className="text-xs font-bold text-slate-700">Raw Extracted Payload</h4>
              <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-[11px] font-mono overflow-x-auto max-h-56">
                {JSON.stringify(selectedRecord.raw_data || selectedRecord.cleaned_data || selectedRecord, null, 2)}
              </pre>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-200">
              <button
                onClick={() => {
                  handleSaveToCrm([selectedRecord.id]);
                  setSelectedRecord(null);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm"
              >
                <Users className="w-4 h-4" />
                Save this Record to CRM
              </button>
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
