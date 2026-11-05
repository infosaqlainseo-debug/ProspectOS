"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Users,
  Search,
  Filter,
  Plus,
  Trash2,
  Tag,
  ArrowUpDown,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  SlidersHorizontal,
  Mail,
  Phone,
  CheckCircle2,
  AlertCircle,
  MoreHorizontal,
  RefreshCw,
  X
} from "lucide-react";
import { crmApi, CRMLead } from "@/lib/crmApi";

function LinkedinIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.53 1.53 0 1 0-.01-3.05 1.53 1.53 0 0 0 .01 3.05m1.39 9.74v-8.37H5.07v8.37h2.78Z" />
    </svg>
  );
}

const STAGES = [
  "ALL",
  "NEW",
  "RESEARCHED",
  "QUALIFIED",
  "CONTACTED",
  "REPLIED",
  "INTERESTED",
  "MEETING_SCHEDULED",
  "NEGOTIATION",
  "WON",
  "LOST"
];

const PRIORITIES = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

function AllLeadsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [leads, setLeads] = useState<CRMLead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [stageFilter, setStageFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [countryFilter, setCountryFilter] = useState("");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const limit = 25;

  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Bulk Edit Modal
  const [bulkStageModalOpen, setBulkStageModalOpen] = useState(false);
  const [bulkTagModalOpen, setBulkTagModalOpen] = useState(false);
  const [targetStage, setTargetStage] = useState("QUALIFIED");
  const [targetTag, setTargetTag] = useState("");

  // Create Lead Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newLeadName, setNewLeadName] = useState("");
  const [newLeadDomain, setNewLeadDomain] = useState("");
  const [newLeadIndustry, setNewLeadIndustry] = useState("");
  const [newLeadCountry, setNewLeadCountry] = useState("");
  const [newLeadEmail, setNewLeadEmail] = useState("");
  const [newLeadPhone, setNewLeadPhone] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const res = await crmApi.listLeads({
        q: searchQuery || undefined,
        stage: stageFilter === "ALL" ? undefined : stageFilter,
        priority: priorityFilter === "ALL" ? undefined : priorityFilter,
        country: countryFilter || undefined,
        page,
        page_size: limit,
        sort_by: sortBy,
        sort_dir: sortDir
      });
      setLeads(res.items);
      setTotal(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [page, stageFilter, priorityFilter, countryFilter, sortBy, sortDir]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(leads.map((l) => l.id)));
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

  const handleBulkStageUpdate = async () => {
    try {
      await crmApi.bulkUpdateLeads({
        lead_ids: Array.from(selectedIds),
        sales_stage: targetStage
      });
      setBulkStageModalOpen(false);
      setSelectedIds(new Set());
      await fetchLeads();
    } catch (e: any) {
      alert(e.message || "Bulk stage update failed");
    }
  };

  const handleBulkAddTag = async () => {
    if (!targetTag.trim()) return;
    try {
      await crmApi.bulkUpdateLeads({
        lead_ids: Array.from(selectedIds),
        add_tags: [targetTag.trim().toLowerCase()]
      });
      setTargetTag("");
      setBulkTagModalOpen(false);
      setSelectedIds(new Set());
      await fetchLeads();
    } catch (e: any) {
      alert(e.message || "Bulk tag update failed");
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedIds.size} selected leads? This cannot be undone.`)) return;
    try {
      await crmApi.bulkDeleteLeads(Array.from(selectedIds));
      setSelectedIds(new Set());
      await fetchLeads();
    } catch (e: any) {
      alert(e.message || "Bulk delete failed");
    }
  };

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeadName.trim()) return;
    try {
      setCreating(true);
      await crmApi.createLead({
        company_name: newLeadName.trim(),
        website_url: newLeadDomain.trim() ? (newLeadDomain.startsWith("http") ? newLeadDomain.trim() : `https://${newLeadDomain.trim()}`) : undefined,
        canonical_domain: newLeadDomain.trim() ? newLeadDomain.replace(/^https?:\/\//, "").replace(/\/.*$/, "") : undefined,
        industry: newLeadIndustry.trim() || undefined,
        country: newLeadCountry.trim() || undefined,
        public_email: newLeadEmail.trim() || undefined,
        phone_number: newLeadPhone.trim() || undefined,
        sales_stage: "NEW",
        lead_priority: "MEDIUM",
        lead_source: "MANUAL",
        tags: ["manual-entry"]
      });
      setCreateModalOpen(false);
      setNewLeadName("");
      setNewLeadDomain("");
      setNewLeadIndustry("");
      setNewLeadCountry("");
      setNewLeadEmail("");
      setNewLeadPhone("");
      await fetchLeads();
    } catch (e: any) {
      alert(e.message || "Failed to create lead");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              Lead Management
            </span>
            <span className="text-xs text-slate-400 font-mono tabular-nums">{total} Central CRM Leads</span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">All Leads &amp; Central Directory</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage your discovered prospects, prioritize pipeline stages, inspect AI scoring, and trigger deep research.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/crm/pipeline"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 hover:bg-slate-50 rounded-lg transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
          >
            Pipeline Board
          </Link>
          <Link
            href="/crm/assistant"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50/80 border border-blue-200/60 hover:bg-blue-100/60 rounded-lg transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Intelligence
          </Link>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-[0_1px_2px_rgba(15,23,42,0.06)]"
          >
            <Plus className="w-3.5 h-3.5" />
            New Lead
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchLeads()}
              placeholder="Search company, domain, email, contact..."
              className="w-full bg-slate-50/70 border border-slate-200/80 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white font-normal text-slate-800"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Stage filter */}
            <select
              value={stageFilter}
              onChange={(e) => { setStageFilter(e.target.value); setPage(1); }}
              className="bg-slate-50/70 border border-slate-200/80 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>Stage: {s.replace("_", " ")}</option>
              ))}
            </select>

            {/* Priority filter */}
            <select
              value={priorityFilter}
              onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
              className="bg-slate-50/70 border border-slate-200/80 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>Priority: {p}</option>
              ))}
            </select>

            {/* Sort order */}
            <select
              value={`${sortBy}:${sortDir}`}
              onChange={(e) => {
                const [b, d] = e.target.value.split(":");
                setSortBy(b);
                setSortDir(d);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700"
            >
              <option value="created_at:desc">Newest First</option>
              <option value="created_at:asc">Oldest First</option>
              <option value="lead_score:desc">Highest Score</option>
              <option value="company_name:asc">Company Name (A-Z)</option>
            </select>

            <button
              onClick={fetchLeads}
              className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-100 rounded-lg transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Bulk Action Bar (Visible when rows selected) */}
        {selectedIds.size > 0 && (
          <div className="p-2.5 bg-indigo-50/70 border border-indigo-200/80 rounded-lg flex items-center justify-between text-xs animate-in fade-in">
            <span className="font-semibold text-indigo-900">
              {selectedIds.size} {selectedIds.size === 1 ? "lead" : "leads"} selected
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setBulkStageModalOpen(true)}
                className="px-2.5 py-1 bg-white border border-indigo-200 hover:bg-indigo-50 font-medium text-indigo-700 rounded transition"
              >
                Change Stage
              </button>
              <button
                onClick={() => setBulkTagModalOpen(true)}
                className="px-2.5 py-1 bg-white border border-indigo-200 hover:bg-indigo-50 font-medium text-indigo-700 rounded transition"
              >
                Add Tag
              </button>
              <button
                onClick={handleBulkDelete}
                className="px-2.5 py-1 bg-white border border-rose-200 hover:bg-rose-50 font-medium text-rose-600 rounded transition"
              >
                Delete Selected
              </button>
              <button
                onClick={() => setSelectedIds(new Set())}
                className="text-slate-400 hover:text-slate-600 ml-1 text-xs"
              >
                Clear
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main CRM Leads Table */}
      <div className="bg-white rounded-xl border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 text-slate-500 uppercase tracking-wider text-[11px] font-medium border-b border-slate-200/75">
              <tr>
                <th className="py-3 px-3 w-8">
                  <input
                    type="checkbox"
                    checked={leads.length > 0 && selectedIds.size === leads.length}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="py-3 px-3">Company &amp; Domain</th>
                <th className="py-3 px-3">Industry</th>
                <th className="py-3 px-3">Location</th>
                <th className="py-3 px-3">Contact Info</th>
                <th className="py-3 px-3">Stage</th>
                <th className="py-3 px-3">Lead Score</th>
                <th className="py-3 px-3">Tags</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/80">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-16 text-center text-slate-400">
                    Loading CRM leads...
                  </td>
                </tr>
              ) : leads.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-16 text-center text-slate-400">
                    <p className="font-medium text-slate-600">No leads found in CRM database</p>
                    <p className="text-xs text-slate-400 mt-1">Run an extraction in Lead Discovery or click "New Lead" to add prospects.</p>
                  </td>
                </tr>
              ) : (
                leads.map((lead) => {
                  const isSelected = selectedIds.has(lead.id);
                  const priorityColor =
                    lead.lead_priority === "CRITICAL"
                      ? "text-rose-600 bg-rose-50 border-rose-200"
                      : lead.lead_priority === "HIGH"
                      ? "text-amber-600 bg-amber-50 border-amber-200"
                      : "text-slate-600 bg-slate-50 border-slate-200";

                  return (
                    <tr
                      key={lead.id}
                      className={`hover:bg-slate-50/60 transition-colors ${isSelected ? "bg-blue-50/20" : ""}`}
                    >
                      <td className="py-3 px-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(lead.id)}
                          className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>

                      {/* Company Name & Domain */}
                      <td className="py-3 px-3 max-w-[220px]">
                        <Link
                          href={`/crm/leads/${lead.id}`}
                          className="font-medium text-slate-900 hover:text-blue-600 transition truncate block text-[13px]"
                        >
                          {lead.company_name}
                        </Link>
                        {lead.canonical_domain && (
                          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400 mt-0.5">
                            <span className="truncate max-w-[170px]">{lead.canonical_domain}</span>
                            {lead.website_url && (
                              <a
                                href={lead.website_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-slate-400 hover:text-indigo-600"
                              >
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                        )}
                      </td>

                      {/* Industry */}
                      <td className="py-3 px-3 text-slate-600">
                        {lead.industry || <span className="text-slate-300">--</span>}
                      </td>

                      {/* Location */}
                      <td className="py-3 px-3 text-slate-600">
                        {lead.city && lead.country ? (
                          <span>{lead.city}, {lead.country}</span>
                        ) : (
                          lead.country || lead.city || <span className="text-slate-300">--</span>
                        )}
                      </td>

                      {/* Contact Info */}
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          {lead.public_email ? (
                            <span title={lead.public_email} className="text-emerald-600 bg-emerald-50 p-1 rounded">
                              <Mail className="w-3.5 h-3.5" />
                            </span>
                          ) : (
                            <span className="text-slate-300 p-1">
                              <Mail className="w-3.5 h-3.5" />
                            </span>
                          )}
                          {lead.phone_number ? (
                            <span title={lead.phone_number} className="text-blue-600 bg-blue-50 p-1 rounded">
                              <Phone className="w-3.5 h-3.5" />
                            </span>
                          ) : (
                            <span className="text-slate-300 p-1">
                              <Phone className="w-3.5 h-3.5" />
                            </span>
                          )}
                          {lead.linkedin_url ? (
                            <a
                              href={lead.linkedin_url}
                              target="_blank"
                              rel="noreferrer"
                              title="LinkedIn Profile"
                              className="text-sky-600 bg-sky-50 p-1 rounded hover:bg-sky-100"
                            >
                              <LinkedinIcon className="w-3.5 h-3.5" />
                            </a>
                          ) : (
                            <span className="text-slate-300 p-1">
                              <LinkedinIcon className="w-3.5 h-3.5" />
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Stage Badge */}
                      <td className="py-3 px-3">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200/70">
                          {lead.sales_stage.replace("_", " ")}
                        </span>
                      </td>

                      {/* Lead Score */}
                      <td className="py-3 px-3 font-mono">
                        {lead.lead_score !== undefined && lead.lead_score !== null ? (
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-slate-900 text-[13px] tabular-nums">{Math.round(lead.lead_score)}</span>
                            <span className="text-[10px] text-slate-400">/100</span>
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${priorityColor}`}>
                              {lead.lead_priority}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-300">--</span>
                        )}
                      </td>

                      {/* Tags */}
                      <td className="py-3 px-3 max-w-[160px]">
                        <div className="flex flex-wrap gap-1">
                          {(lead.tags || []).slice(0, 2).map((t, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200/50 truncate max-w-[75px]"
                            >
                              {t}
                            </span>
                          ))}
                          {(lead.tags || []).length > 2 && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              +{(lead.tags || []).length - 2}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/crm/leads/${lead.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 hover:bg-slate-50 hover:text-blue-600 rounded-md transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
                        >
                          View
                        </Link>
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
            Showing {leads.length} of {total} leads (Page {page} of {Math.max(1, Math.ceil(total / limit))})
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

      {/* Bulk Stage Modal */}
      {bulkStageModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-sm w-full p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Move {selectedIds.size} Leads to Stage</h3>
            <select
              value={targetStage}
              onChange={(e) => setTargetStage(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-medium"
            >
              {STAGES.filter((s) => s !== "ALL").map((s) => (
                <option key={s} value={s}>{s.replace("_", " ")}</option>
              ))}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setBulkStageModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkStageUpdate}
                className="px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded shadow-sm"
              >
                Apply Stage
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Tag Modal */}
      {bulkTagModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-sm w-full p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Add Tag to {selectedIds.size} Leads</h3>
            <input
              type="text"
              value={targetTag}
              onChange={(e) => setTargetTag(e.target.value)}
              placeholder="e.g. priority-q1, outreach-ready"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-medium outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setBulkTagModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkAddTag}
                className="px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded shadow-sm"
              >
                Apply Tag
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Lead Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Create New CRM Lead</h3>
              <button onClick={() => setCreateModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateLead} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Company Name *</label>
                <input
                  required
                  type="text"
                  value={newLeadName}
                  onChange={(e) => setNewLeadName(e.target.value)}
                  placeholder="e.g. Acme Health Solutions"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Website URL or Domain</label>
                <input
                  type="text"
                  value={newLeadDomain}
                  onChange={(e) => setNewLeadDomain(e.target.value)}
                  placeholder="e.g. acmehealth.com"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Industry</label>
                  <input
                    type="text"
                    value={newLeadIndustry}
                    onChange={(e) => setNewLeadIndustry(e.target.value)}
                    placeholder="e.g. Healthcare"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Country</label>
                  <input
                    type="text"
                    value={newLeadCountry}
                    onChange={(e) => setNewLeadCountry(e.target.value)}
                    placeholder="e.g. United States"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Public Email</label>
                  <input
                    type="email"
                    value={newLeadEmail}
                    onChange={(e) => setNewLeadEmail(e.target.value)}
                    placeholder="contact@acme.com"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Business Phone</label>
                  <input
                    type="text"
                    value={newLeadPhone}
                    onChange={(e) => setNewLeadPhone(e.target.value)}
                    placeholder="+1-555-0199"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm"
                >
                  {creating ? "Creating..." : "Save Lead"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AllLeadsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-slate-400">Loading Leads...</div>}>
      <AllLeadsContent />
    </Suspense>
  );
}
