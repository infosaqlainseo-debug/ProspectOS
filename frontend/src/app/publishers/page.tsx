"use client";

import { useEffect, useState, useMemo } from "react";
import {
  api,
  PublisherRecord,
  PublisherQualitySummary,
  PublisherQualityFinding,
  PublisherQualityScore,
  PublisherDetailedQuality,
  PublisherRefreshLog,
  PublisherObservationTimelineItem
} from "@/lib/api";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  ExternalLink,
  Sliders,
  Database,
  ArrowRight,
  ChevronRight,
  X,
  Plus,
  Edit3,
  FileText,
  AlertCircle,
  Eye,
  Check,
  TrendingUp,
  Layers,
  HelpCircle,
  History,
  Activity,
  DollarSign,
  BarChart3
} from "lucide-react";

export default function PublishersPage() {
  // Navigation / Tabs
  const [activeTab, setActiveTab] = useState<"inventory" | "findings" | "logs">("inventory");

  // Summary & Stats
  const [summary, setSummary] = useState<PublisherQualitySummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  // Main Lists
  const [publishers, setPublishers] = useState<PublisherRecord[]>([]);
  const [loadingPublishers, setLoadingPublishers] = useState(true);
  const [findings, setFindings] = useState<PublisherQualityFinding[]>([]);
  const [loadingFindings, setLoadingFindings] = useState(false);
  const [refreshLogs, setRefreshLogs] = useState<PublisherRefreshLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");
  const [findingIssueFilter, setFindingIssueFilter] = useState("ALL");
  const [findingSeverityFilter, setFindingSeverityFilter] = useState("ALL");
  const [findingStatusFilter, setFindingStatusFilter] = useState("OPEN");

  // Interactive Action States
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  // Detail Drawer State
  const [selectedPublisherId, setSelectedPublisherId] = useState<string | null>(null);
  const [publisherDetail, setPublisherDetail] = useState<PublisherDetailedQuality | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [drawerSubTab, setDrawerSubTab] = useState<"overview" | "observations" | "findings" | "logs">("overview");

  // Modals
  const [resolvingFinding, setResolvingFinding] = useState<PublisherQualityFinding | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState("RESOLVED");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [resolutionOperator, setResolutionOperator] = useState("Lead Quality Auditor");

  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [correctionField, setCorrectionField] = useState("price");
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionCurrency, setCorrectionCurrency] = useState("USD");
  const [correctionReason, setCorrectionReason] = useState("");
  const [correctionOperator, setCorrectionOperator] = useState("Inventory Specialist");

  // Load Initial Data
  useEffect(() => {
    loadSummary();
    loadPublishers();
  }, [verdictFilter]);

  useEffect(() => {
    if (activeTab === "findings") {
      loadFindings();
    } else if (activeTab === "logs") {
      loadLogs();
    }
  }, [activeTab, findingIssueFilter, findingSeverityFilter, findingStatusFilter]);

  const loadSummary = async () => {
    try {
      setLoadingSummary(true);
      const data = await api.getPublisherQualitySummary();
      setSummary(data);
    } catch (err: any) {
      console.error("Failed to load publisher quality summary:", err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const loadPublishers = async () => {
    try {
      setLoadingPublishers(true);
      const params: any = { limit: 100 };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (verdictFilter !== "ALL") params.quality_verdict = verdictFilter;
      const data = await api.getPublishers(params);
      setPublishers(data || []);
    } catch (err: any) {
      console.error("Failed to load publishers:", err);
      showNotification("error", "Failed to load publishers inventory");
    } finally {
      setLoadingPublishers(false);
    }
  };

  const loadFindings = async () => {
    try {
      setLoadingFindings(true);
      const params: any = { limit: 100 };
      if (findingIssueFilter !== "ALL") params.issue_type = findingIssueFilter;
      if (findingSeverityFilter !== "ALL") params.severity = findingSeverityFilter;
      if (findingStatusFilter !== "ALL") params.status = findingStatusFilter;
      const data = await api.getPublisherQualityFindings(params);
      setFindings(data || []);
    } catch (err: any) {
      console.error("Failed to load findings:", err);
      showNotification("error", "Failed to load quality findings");
    } finally {
      setLoadingFindings(false);
    }
  };

  const loadLogs = async () => {
    try {
      setLoadingLogs(true);
      const data = await api.getPublisherRefreshLogs(undefined, 100);
      setRefreshLogs(data || []);
    } catch (err: any) {
      console.error("Failed to load refresh logs:", err);
    } finally {
      setLoadingLogs(false);
    }
  };

  const showNotification = (type: "success" | "error" | "info", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // Inspect Publisher Drawer
  const handleInspectPublisher = async (pubId: string) => {
    setSelectedPublisherId(pubId);
    setDrawerSubTab("overview");
    try {
      setLoadingDetail(true);
      const detail = await api.getPublisherQualityDetail(pubId);
      setPublisherDetail(detail);
    } catch (err: any) {
      console.error("Failed to load publisher detail:", err);
      showNotification("error", "Failed to fetch publisher quality detail");
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleRefreshPublisher = async (pubId: string) => {
    try {
      setActionLoading(true);
      const res = await api.refreshPublisher(pubId, { force_refresh: true });
      showNotification("success", res.message || "Publisher refresh completed");
      // Reload detail and list
      if (selectedPublisherId === pubId) {
        const updated = await api.getPublisherQualityDetail(pubId);
        setPublisherDetail(updated);
      }
      loadPublishers();
      loadSummary();
    } catch (err: any) {
      console.error("Refresh failed:", err);
      showNotification("error", err.message || "Publisher refresh attempt encountered an error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchAudit = async () => {
    try {
      setActionLoading(true);
      showNotification("info", "Starting batch quality audit on publishers...");
      const res = await api.runBatchPublisherQualityAudit(50);
      showNotification("success", `Batch audit evaluated ${res.audited_count} publishers in ${res.duration_ms}ms`);
      loadSummary();
      loadPublishers();
      if (activeTab === "findings") loadFindings();
    } catch (err: any) {
      console.error("Batch audit failed:", err);
      showNotification("error", err.message || "Failed to run batch audit");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunSingleAudit = async (pubId: string) => {
    try {
      setActionLoading(true);
      const res = await api.runPublisherQualityAudit(pubId);
      showNotification("success", `Audited publisher: score ${res.quality_score.overall_quality_score}/100 (${res.quality_score.verdict})`);
      const updated = await api.getPublisherQualityDetail(pubId);
      setPublisherDetail(updated);
      loadPublishers();
      loadSummary();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to audit publisher");
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveFindingSubmit = async () => {
    if (!resolvingFinding) return;
    if (!resolutionNotes.trim()) {
      showNotification("error", "Please provide a resolution note or justification");
      return;
    }
    try {
      setActionLoading(true);
      await api.resolvePublisherQualityFinding(resolvingFinding.id, {
        resolution_status: resolutionStatus,
        resolution_notes: resolutionNotes.trim(),
        operator_name: resolutionOperator.trim() || "Auditor"
      });
      showNotification("success", `Finding resolved successfully as ${resolutionStatus}`);
      setResolvingFinding(null);
      setResolutionNotes("");
      // Refresh views
      if (selectedPublisherId) {
        const updated = await api.getPublisherQualityDetail(selectedPublisherId);
        setPublisherDetail(updated);
      }
      loadFindings();
      loadSummary();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to resolve finding");
    } finally {
      setActionLoading(false);
    }
  };

  const handleApplyCorrectionSubmit = async () => {
    if (!selectedPublisherId) return;
    if (!correctionValue.trim()) {
      showNotification("error", "Please specify a new value");
      return;
    }
    if (!correctionReason.trim()) {
      showNotification("error", "Correction reason is strictly mandatory for auditability");
      return;
    }
    try {
      setActionLoading(true);
      const res = await api.applyPublisherManualCorrection(selectedPublisherId, {
        field_name: correctionField,
        new_value: correctionValue.trim(),
        correction_reason: correctionReason.trim(),
        operator_name: correctionOperator.trim() || "Operator",
        currency: correctionField === "price" ? correctionCurrency : undefined
      });
      showNotification("success", res.message || "Manual correction recorded safely with provenance");
      setCorrectionModalOpen(false);
      setCorrectionValue("");
      setCorrectionReason("");
      // Reload
      const updated = await api.getPublisherQualityDetail(selectedPublisherId);
      setPublisherDetail(updated);
      loadPublishers();
      loadSummary();
    } catch (err: any) {
      showNotification("error", err.message || "Failed to record manual correction");
    } finally {
      setActionLoading(false);
    }
  };

  // Filtered inventory list
  const filteredPublishers = useMemo(() => {
    if (!searchQuery.trim()) return publishers;
    const q = searchQuery.toLowerCase();
    return publishers.filter(
      p =>
        (p.publisher_name && p.publisher_name.toLowerCase().includes(q)) ||
        (p.canonical_domain && p.canonical_domain.toLowerCase().includes(q)) ||
        (p.original_submitted_url && p.original_submitted_url.toLowerCase().includes(q))
    );
  }, [publishers, searchQuery]);

  // Helper Badge Renderers
  const renderVerdictBadge = (verdict?: string | null) => {
    switch (verdict) {
      case "EXCELLENT":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Excellent
          </span>
        );
      case "ACCEPTABLE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
            <ShieldCheck className="w-3 h-3 text-blue-600" /> Acceptable
          </span>
        );
      case "POOR":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> Needs Review
          </span>
        );
      case "CRITICAL":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
            <XCircle className="w-3 h-3 text-rose-600" /> Critical Issues
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
            <Clock className="w-3 h-3 text-gray-400" /> Unaudited
          </span>
        );
    }
  };

  const renderSeverityBadge = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-100 text-rose-700">CRITICAL</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-700">HIGH</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">MEDIUM</span>;
      case "LOW":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">LOW</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">{severity}</span>;
    }
  };

  const renderIssueTypeBadge = (issueType: string) => {
    switch (issueType) {
      case "DUPLICATE_RECORD":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">Duplicate Record</span>;
      case "CONFLICTING_DATA":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">Domain Conflict</span>;
      case "STALE_DATA":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">Stale Observation</span>;
      case "INVALID_DATA":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">Invalid Value</span>;
      case "MISSING_FIELD":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">Missing Field</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">{issueType}</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 ${
            notification.type === "success"
              ? "bg-emerald-600 text-white"
              : notification.type === "error"
              ? "bg-rose-600 text-white"
              : "bg-indigo-600 text-white"
          }`}
        >
          {notification.type === "success" && <CheckCircle2 className="w-4 h-4" />}
          {notification.type === "error" && <AlertTriangle className="w-4 h-4" />}
          {notification.type === "info" && <Activity className="w-4 h-4 animate-spin" />}
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} className="ml-2 hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700">
                Phase 3.1 Live
              </span>
              <span className="text-xs text-gray-500 font-medium">Persistent Quality Engine</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">Publisher Intelligence & Data Quality Monitoring</h1>
            <p className="text-sm text-gray-600 mt-1">
              Continuous domain validation, multi-field freshness verification, duplicate detection, and auditable non-destructive updates.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleBatchAudit}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${actionLoading ? "animate-spin" : ""}`} />
              Run Batch Quality Audit
            </button>
            <a
              href="/publishers/import"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Import Inventory
            </a>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {/* Health Score Card */}
          <div className="p-4 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50/50 to-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Average Quality Score</span>
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-950">
                {summary ? `${summary.average_quality_score}/100` : "-"}
              </span>
              <span className="text-xs text-emerald-700">
                avg across {summary ? summary.audited_publishers : "-"} audited
              </span>
            </div>
            <div className="mt-2 text-xs text-emerald-600 flex items-center gap-1">
              <span className="font-semibold">{summary?.total_publishers || 0}</span> total publishers tracked
            </div>
          </div>

          {/* Attention Required Card */}
          <div className="p-4 rounded-xl border border-rose-100 bg-gradient-to-br from-rose-50/50 to-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-800 uppercase tracking-wider">Critical Flagged</span>
              <AlertTriangle className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-950">
                {summary ? summary.publishers_with_critical_issues : "-"}
              </span>
              <span className="text-xs text-rose-700">publishers flagged</span>
            </div>
            <div className="mt-2 text-xs text-rose-600 flex items-center gap-1">
              <span className="font-semibold">{summary?.publishers_with_duplicates || 0}</span> duplicate domain collisions
            </div>
          </div>

          {/* Stale Observations Card */}
          <div className="p-4 rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50/50 to-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-800 uppercase tracking-wider">Stale Observations</span>
              <Clock className="w-4 h-4 text-blue-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-blue-950">
                {summary ? summary.publishers_with_stale_data : "-"}
              </span>
              <span className="text-xs text-blue-700">stale prices / metrics</span>
            </div>
            <div className="mt-2 text-xs text-blue-600 flex items-center gap-1">
              Price threshold: 30d | SEO metrics: 60d
            </div>
          </div>

          {/* Open Findings Card */}
          <div className="p-4 rounded-xl border border-purple-100 bg-gradient-to-br from-purple-50/50 to-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-800 uppercase tracking-wider">Open Findings</span>
              <AlertCircle className="w-4 h-4 text-purple-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-purple-950">
                {summary ? summary.total_open_findings : "-"}
              </span>
              <span className="text-xs text-purple-700">active issues</span>
            </div>
            <div className="mt-2 text-xs text-purple-600 flex items-center gap-2">
              <span className="px-1.5 py-0.5 rounded bg-purple-100 font-semibold">
                {summary?.severity_breakdown.critical || 0} Crit
              </span>
              <span className="px-1.5 py-0.5 rounded bg-purple-100 font-semibold">
                {summary?.severity_breakdown.high || 0} High
              </span>
              <span className="px-1.5 py-0.5 rounded bg-purple-100 font-semibold">
                {summary?.publishers_with_conflicts || 0} Conflicts
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center border-b border-gray-200">
        <button
          onClick={() => setActiveTab("inventory")}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "inventory"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <Database className="w-4 h-4" />
          Publisher Directory ({publishers.length})
        </button>

        <button
          onClick={() => setActiveTab("findings")}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "findings"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          Quality Findings & Issues
          {summary && summary.total_open_findings > 0 && (
            <span className="ml-1.5 px-2 py-0.5 text-xs font-bold rounded-full bg-rose-100 text-rose-700">
              {summary.total_open_findings}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("logs")}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "logs"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <History className="w-4 h-4" />
          Provider Refresh Logs
        </button>
      </div>

      {/* TAB 1: PUBLISHER DIRECTORY */}
      {activeTab === "inventory" && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="bg-white p-4 rounded-xl border border-gray-200 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-96">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, canonical domain, or URL..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto">
              <span className="text-xs font-medium text-gray-500 whitespace-nowrap">Filter by Quality:</span>
              <select
                value={verdictFilter}
                onChange={e => setVerdictFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ALL">All Verdicts</option>
                <option value="EXCELLENT">Excellent (90-100)</option>
                <option value="ACCEPTABLE">Acceptable (70-89)</option>
                <option value="POOR">Needs Review (50-69)</option>
                <option value="CRITICAL">Critical Issues (&lt;50)</option>
                <option value="NOT_AUDITED">Not Audited</option>
              </select>

              <button
                onClick={loadPublishers}
                className="p-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50"
                title="Refresh list"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Publishers Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {loadingPublishers ? (
              <div className="py-20 flex flex-col items-center justify-center text-gray-400">
                <Activity className="w-8 h-8 animate-spin text-indigo-600 mb-2" />
                <p className="text-sm">Loading publisher records with quality status...</p>
              </div>
            ) : filteredPublishers.length === 0 ? (
              <div className="py-16 text-center text-gray-500">
                <p className="text-base font-medium">No publishers found matching your filters.</p>
                <p className="text-sm mt-1">Try adjusting the search query or quality verdict filter.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Publisher / Domain</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Price & Currency</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">SEO Metrics</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Quality Verdict</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Freshness Status</th>
                      <th className="px-6 py-3.5 text-right font-semibold text-gray-600">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredPublishers.map(pub => (
                      <tr key={pub.id} className="hover:bg-gray-50/80 transition-colors">
                        {/* Domain & URL */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-gray-900">
                              {pub.publisher_name || pub.canonical_domain || "Unknown Publisher"}
                            </span>
                            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-gray-500">
                              <span className="font-mono text-gray-700">{pub.canonical_domain || "-"}</span>
                              {pub.original_submitted_url && (
                                <a
                                  href={pub.original_submitted_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-indigo-600 hover:text-indigo-800"
                                  title={pub.original_submitted_url}
                                >
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            {pub.audience_focus && (
                              <span className="mt-1 text-xs text-gray-400">Audience: {pub.audience_focus}</span>
                            )}
                          </div>
                        </td>

                        {/* Price */}
                        <td className="px-6 py-4">
                          {pub.price !== null && pub.price !== undefined ? (
                            <div className="flex flex-col">
                              <span className="font-semibold text-gray-900">
                                {pub.currency || "USD"} {Number(pub.price).toLocaleString()}
                              </span>
                              <span className="text-xs text-emerald-600 font-medium">Valid Price</span>
                            </div>
                          ) : (
                            <span className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                              Missing Price
                            </span>
                          )}
                        </td>

                        {/* SEO Metrics */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3 text-xs">
                            <div className="flex flex-col">
                              <span className="text-gray-400 font-medium">DA</span>
                              <span className="font-bold text-gray-800">
                                {pub.metric_da !== null && pub.metric_da !== undefined ? pub.metric_da : "-"}
                              </span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-gray-400 font-medium">DR</span>
                              <span className="font-bold text-gray-800">
                                {pub.metric_dr !== null && pub.metric_dr !== undefined ? pub.metric_dr : "-"}
                              </span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-gray-400 font-medium">Traffic</span>
                              <span className="font-bold text-gray-800">
                                {pub.metric_traffic !== null && pub.metric_traffic !== undefined
                                  ? Number(pub.metric_traffic).toLocaleString()
                                  : "-"}
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Quality Verdict & Score */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1 items-start">
                            {renderVerdictBadge(pub.quality_verdict)}
                            {pub.quality_overall_score !== null && pub.quality_overall_score !== undefined && (
                              <div className="w-24 bg-gray-200 rounded-full h-1.5 overflow-hidden mt-1">
                                <div
                                  className={`h-1.5 rounded-full ${
                                    pub.quality_overall_score >= 85
                                      ? "bg-emerald-500"
                                      : pub.quality_overall_score >= 70
                                      ? "bg-blue-500"
                                      : pub.quality_overall_score >= 50
                                      ? "bg-amber-500"
                                      : "bg-rose-500"
                                  }`}
                                  style={{ width: `${pub.quality_overall_score}%` }}
                                />
                              </div>
                            )}
                          </div>
                        </td>

                        {/* Freshness Status */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1 text-xs">
                            {pub.is_stale ? (
                              <span className="inline-flex items-center gap-1 font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded w-max">
                                <Clock className="w-3 h-3 text-amber-600" /> Stale Observations
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded w-max">
                                <Check className="w-3 h-3 text-emerald-600" /> Fresh
                              </span>
                            )}
                            {pub.has_duplicates && (
                              <span className="inline-flex items-center gap-1 font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded w-max">
                                Duplicate Domain
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Actions */}
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleInspectPublisher(pub.id)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Inspect Quality
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: QUALITY FINDINGS & ISSUES */}
      {activeTab === "findings" && (
        <div className="space-y-4">
          {/* Findings Filter Bar */}
          <div className="bg-white p-4 rounded-xl border border-gray-200 flex flex-wrap gap-4 items-center justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Issue Type
                </label>
                <select
                  value={findingIssueFilter}
                  onChange={e => setFindingIssueFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="ALL">All Issue Types</option>
                  <option value="DUPLICATE_RECORD">Duplicate Record</option>
                  <option value="CONFLICTING_DATA">Domain Conflict</option>
                  <option value="STALE_DATA">Stale Data</option>
                  <option value="INVALID_DATA">Invalid Data</option>
                  <option value="MISSING_FIELD">Missing Field</option>
                  <option value="UNSUPPORTED_CURRENCY">Unsupported Currency</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Severity
                </label>
                <select
                  value={findingSeverityFilter}
                  onChange={e => setFindingSeverityFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Status</label>
                <select
                  value={findingStatusFilter}
                  onChange={e => setFindingStatusFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="OPEN">Open Only</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="IGNORED">Ignored</option>
                  <option value="ALL">All Statuses</option>
                </select>
              </div>
            </div>

            <button
              onClick={loadFindings}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              <RefreshCw className="w-4 h-4" /> Refresh Findings
            </button>
          </div>

          {/* Findings Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {loadingFindings ? (
              <div className="py-20 flex flex-col items-center justify-center text-gray-400">
                <Activity className="w-8 h-8 animate-spin text-indigo-600 mb-2" />
                <p className="text-sm">Fetching publisher quality findings...</p>
              </div>
            ) : findings.length === 0 ? (
              <div className="py-16 text-center text-gray-500">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                <p className="text-base font-semibold text-gray-800">No active findings matching criteria</p>
                <p className="text-sm text-gray-500 mt-1">Publisher inventory satisfies all configured quality rules.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Severity</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Finding Title & Field</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Publisher</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Recommended Action</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Status</th>
                      <th className="px-6 py-3.5 text-right font-semibold text-gray-600">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {findings.map(finding => (
                      <tr key={finding.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-1.5">{renderSeverityBadge(finding.severity)}</div>
                        </td>

                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-gray-900">{finding.title}</span>
                            <span className="text-xs text-gray-500 mt-0.5">{finding.description}</span>
                            <div className="flex items-center gap-2 mt-1.5">
                              {renderIssueTypeBadge(finding.issue_type)}
                              <span className="font-mono text-xs text-gray-400">field: {finding.field_name}</span>
                            </div>
                          </div>
                        </td>

                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-medium text-gray-800">
                              {finding.publisher_name || finding.canonical_domain || "Publisher"}
                            </span>
                            <span className="font-mono text-xs text-gray-500">{finding.canonical_domain || "-"}</span>
                          </div>
                        </td>

                        <td className="px-6 py-4 text-xs text-gray-700 max-w-xs">{finding.recommended_action}</td>

                        <td className="px-6 py-4">
                          {finding.status === "OPEN" ? (
                            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700">
                              OPEN
                            </span>
                          ) : finding.status === "RESOLVED" ? (
                            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700">
                              RESOLVED
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">
                              IGNORED
                            </span>
                          )}
                        </td>

                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleInspectPublisher(finding.publisher_id)}
                              className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-gray-100 rounded"
                              title="Inspect publisher"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            {finding.status === "OPEN" && (
                              <button
                                onClick={() => setResolvingFinding(finding)}
                                className="px-3 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100 transition-colors"
                              >
                                Resolve
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: REFRESH & AUDIT LOGS */}
      {activeTab === "logs" && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-sm font-bold text-gray-900">Provider Refresh & Enrichment Logs</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Every external refresh attempt preserves previous observations, provider attribution, durations, and errors.
              </p>
            </div>
            <button
              onClick={loadLogs}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-700 bg-gray-50 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Logs
            </button>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {loadingLogs ? (
              <div className="py-20 flex flex-col items-center justify-center text-gray-400">
                <Activity className="w-8 h-8 animate-spin text-indigo-600 mb-2" />
                <p className="text-sm">Loading refresh audit records...</p>
              </div>
            ) : refreshLogs.length === 0 ? (
              <div className="py-16 text-center text-gray-500">
                <p className="text-sm font-medium">No refresh logs recorded yet.</p>
                <p className="text-xs text-gray-400 mt-1">Logs are created when running authorized provider refresh jobs.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Timestamp</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Provider & Target Field</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Execution Status</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Value Transition</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Duration & Retries</th>
                      <th className="px-6 py-3.5 text-left font-semibold text-gray-600">Notes / Errors</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {refreshLogs.map(log => (
                      <tr key={log.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs text-gray-500">
                          {new Date(log.attempted_at).toLocaleString()}
                        </td>

                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-gray-900">{log.provider}</span>
                            <span className="text-xs font-mono text-gray-500">field: {log.field_refreshed}</span>
                          </div>
                        </td>

                        <td className="px-6 py-4">
                          {log.status === "COMPLETED" ? (
                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                              COMPLETED
                            </span>
                          ) : log.status === "PROVIDER_NOT_CONFIGURED" ? (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                              NOT CONFIGURED
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-100 text-rose-800">
                              {log.status}
                            </span>
                          )}
                        </td>

                        <td className="px-6 py-4 text-xs font-mono">
                          <div className="flex items-center gap-1.5">
                            <span className="text-gray-400">{log.previous_value || "None"}</span>
                            <ArrowRight className="w-3 h-3 text-gray-400" />
                            <span className="font-bold text-gray-800">{log.new_value || "Unchanged"}</span>
                          </div>
                        </td>

                        <td className="px-6 py-4 text-xs text-gray-600">
                          {log.duration_ms ? `${log.duration_ms} ms` : "-"} (retries: {log.retry_count})
                        </td>

                        <td className="px-6 py-4 text-xs text-gray-500 max-w-sm truncate">
                          {log.error_message || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SLIDE-OVER INSPECTION DRAWER */}
      {selectedPublisherId && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end transition-opacity">
          <div className="w-full max-w-3xl bg-white h-full shadow-2xl flex flex-col overflow-y-auto">
            {/* Drawer Header */}
            <div className="p-6 border-b border-gray-200 bg-gray-50 flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-100 text-indigo-700">
                    Publisher Intelligence Record
                  </span>
                  {publisherDetail?.quality_score && renderVerdictBadge(publisherDetail.quality_score.verdict)}
                </div>
                <h2 className="text-xl font-bold text-gray-900 mt-1">
                  {publisherDetail?.publisher_name || publisherDetail?.company_name || "Publisher Details"}
                </h2>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 font-mono">
                  <span>Domain: {publisherDetail?.canonical_domain || "Unassigned"}</span>
                  {publisherDetail?.original_submitted_url && (
                    <a
                      href={publisherDetail.original_submitted_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-0.5"
                    >
                      <ExternalLink className="w-3 h-3" /> URL
                    </a>
                  )}
                </div>
              </div>

              <button
                onClick={() => setSelectedPublisherId(null)}
                className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingDetail ? (
              <div className="p-16 flex flex-col items-center justify-center text-gray-400">
                <Activity className="w-8 h-8 animate-spin text-indigo-600 mb-2" />
                <p className="text-sm">Loading publisher quality details and provenance...</p>
              </div>
            ) : publisherDetail ? (
              <div className="p-6 space-y-6 flex-1">
                {/* Actions Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-indigo-50/50 rounded-xl border border-indigo-100">
                  <span className="text-xs font-semibold text-indigo-900">Publisher Quality Operations:</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRunSingleAudit(publisherDetail.publisher_id)}
                      disabled={actionLoading}
                      className="px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-white border border-indigo-200 rounded-md hover:bg-indigo-50 disabled:opacity-50"
                    >
                      Audit Record
                    </button>
                    <button
                      onClick={() => handleRefreshPublisher(publisherDetail.publisher_id)}
                      disabled={actionLoading}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                    >
                      Refresh Authorized Sources
                    </button>
                    <button
                      onClick={() => setCorrectionModalOpen(true)}
                      className="px-3 py-1.5 text-xs font-semibold text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-1"
                    >
                      <Edit3 className="w-3.5 h-3.5" /> Manual Correction
                    </button>
                  </div>
                </div>

                {/* Score Breakdown Cards */}
                {publisherDetail.quality_score && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-center">
                      <span className="text-xs text-gray-500 font-medium">Overall Score</span>
                      <div className="text-xl font-bold text-gray-900 mt-1">
                        {publisherDetail.quality_score.overall_quality_score} / 100
                      </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-center">
                      <span className="text-xs text-gray-500 font-medium">Completeness</span>
                      <div className="text-xl font-bold text-gray-900 mt-1">
                        {publisherDetail.quality_score.completeness_score} %
                      </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-center">
                      <span className="text-xs text-gray-500 font-medium">Validity</span>
                      <div className="text-xl font-bold text-gray-900 mt-1">
                        {publisherDetail.quality_score.validity_score} %
                      </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-center">
                      <span className="text-xs text-gray-500 font-medium">Freshness</span>
                      <div className="text-xl font-bold text-gray-900 mt-1">
                        {publisherDetail.quality_score.freshness_score} %
                      </div>
                    </div>
                  </div>
                )}

                {/* Field Freshness Breakdown */}
                <div className="bg-white p-4 rounded-xl border border-gray-200 space-y-3">
                  <h3 className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-indigo-600" /> Field-Level Freshness Indicators
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    {/* Price Freshness */}
                    <div className="p-3 rounded-lg border border-gray-100 bg-gray-50">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-700">Pricing Freshness</span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            publisherDetail.freshness_status?.price?.status === "FRESH"
                              ? "bg-emerald-100 text-emerald-800"
                              : publisherDetail.freshness_status?.price?.status === "STALE"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-gray-200 text-gray-700"
                          }`}
                        >
                          {publisherDetail.freshness_status?.price?.status || "UNKNOWN"}
                        </span>
                      </div>
                      <p className="text-gray-500 mt-1">
                        Age: {publisherDetail.freshness_status?.price?.age_days ?? "-"} days (Threshold: 30 days)
                      </p>
                    </div>

                    {/* Metrics Freshness */}
                    <div className="p-3 rounded-lg border border-gray-100 bg-gray-50">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-700">Domain Metrics Freshness</span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            publisherDetail.freshness_status?.domain_metrics?.status === "FRESH"
                              ? "bg-emerald-100 text-emerald-800"
                              : publisherDetail.freshness_status?.domain_metrics?.status === "STALE"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-gray-200 text-gray-700"
                          }`}
                        >
                          {publisherDetail.freshness_status?.domain_metrics?.status || "UNKNOWN"}
                        </span>
                      </div>
                      <p className="text-gray-500 mt-1">
                        Age: {publisherDetail.freshness_status?.domain_metrics?.age_days ?? "-"} days (Threshold: 60 days)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Drawer Sub-tabs */}
                <div className="border-b border-gray-200 flex gap-4 text-xs font-semibold">
                  <button
                    onClick={() => setDrawerSubTab("overview")}
                    className={`pb-2 border-b-2 ${
                      drawerSubTab === "overview"
                        ? "border-indigo-600 text-indigo-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Current Observations
                  </button>
                  <button
                    onClick={() => setDrawerSubTab("findings")}
                    className={`pb-2 border-b-2 flex items-center gap-1 ${
                      drawerSubTab === "findings"
                        ? "border-indigo-600 text-indigo-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Findings ({publisherDetail.findings.length})
                  </button>
                  <button
                    onClick={() => setDrawerSubTab("observations")}
                    className={`pb-2 border-b-2 flex items-center gap-1 ${
                      drawerSubTab === "observations"
                        ? "border-indigo-600 text-indigo-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Historical Provenance ({publisherDetail.historical_observations.length})
                  </button>
                  <button
                    onClick={() => setDrawerSubTab("logs")}
                    className={`pb-2 border-b-2 flex items-center gap-1 ${
                      drawerSubTab === "logs"
                        ? "border-indigo-600 text-indigo-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    Refresh Logs ({publisherDetail.refresh_logs.length})
                  </button>
                </div>

                {/* SubTab 1: Current Observation Details */}
                {drawerSubTab === "overview" && (
                  <div className="space-y-4">
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
                      <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                        Latest Verified Observation
                      </h4>
                      {publisherDetail.latest_observation ? (
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <span className="text-gray-400">Price:</span>
                            <p className="font-semibold text-gray-900 mt-0.5">
                              {publisherDetail.latest_observation.currency || "USD"}{" "}
                              {publisherDetail.latest_observation.price ?? "Not Specified"}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-400">Verification Status:</span>
                            <p className="font-semibold text-gray-900 mt-0.5">
                              {publisherDetail.latest_observation.verification_status}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-400">SEO Metrics:</span>
                            <p className="font-semibold text-gray-900 mt-0.5">
                              DA: {publisherDetail.latest_observation.metric_da ?? "-"} | DR:{" "}
                              {publisherDetail.latest_observation.metric_dr ?? "-"} | Traffic:{" "}
                              {publisherDetail.latest_observation.metric_traffic ?? "-"}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-400">Source:</span>
                            <p className="font-semibold text-gray-900 mt-0.5">
                              {publisherDetail.latest_observation.source_name || "Unknown"}
                            </p>
                          </div>
                          <div className="col-span-2">
                            <span className="text-gray-400">Observed Timestamp:</span>
                            <p className="font-mono text-gray-700 mt-0.5">
                              {new Date(publisherDetail.latest_observation.observation_timestamp).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-gray-500">No observations recorded yet for this publisher.</p>
                      )}
                    </div>
                  </div>
                )}

                {/* SubTab 2: Findings */}
                {drawerSubTab === "findings" && (
                  <div className="space-y-3">
                    {publisherDetail.findings.length === 0 ? (
                      <p className="text-xs text-gray-500">No active findings on this publisher record.</p>
                    ) : (
                      publisherDetail.findings.map(f => (
                        <div key={f.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {renderSeverityBadge(f.severity)}
                              <span className="font-bold text-gray-900">{f.title}</span>
                            </div>
                            {f.status === "OPEN" && (
                              <button
                                onClick={() => setResolvingFinding(f)}
                                className="px-2 py-0.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100"
                              >
                                Resolve
                              </button>
                            )}
                          </div>
                          <p className="text-gray-600">{f.description}</p>
                          <p className="text-indigo-700 font-medium">Recommended: {f.recommended_action}</p>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* SubTab 3: Historical Provenance (Timeline) */}
                {drawerSubTab === "observations" && (
                  <div className="space-y-3">
                    <p className="text-xs text-gray-500">
                      Historical audit trail preserving all observed price and metric points with non-destructive timestamps.
                    </p>
                    <div className="divide-y divide-gray-100">
                      {publisherDetail.historical_observations.map(obs => (
                        <div key={obs.id} className="py-2.5 text-xs flex justify-between items-start">
                          <div>
                            <span className="font-semibold text-gray-900">
                              {obs.currency || "USD"} {obs.price ?? "N/A"}
                            </span>
                            <span className="text-gray-500 ml-2">
                              (DA: {obs.metric_da ?? "-"}, DR: {obs.metric_dr ?? "-"})
                            </span>
                            <div className="text-gray-400 mt-0.5">
                              Source: {obs.source_name || "Internal"} | Status: {obs.verification_status}
                            </div>
                          </div>
                          <span className="font-mono text-gray-400 text-right">
                            {new Date(obs.observation_timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SubTab 4: Refresh Logs */}
                {drawerSubTab === "logs" && (
                  <div className="space-y-3">
                    {publisherDetail.refresh_logs.length === 0 ? (
                      <p className="text-xs text-gray-500">No refresh logs for this publisher.</p>
                    ) : (
                      publisherDetail.refresh_logs.map(log => (
                        <div key={log.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-gray-900">
                              {log.provider} ({log.field_refreshed})
                            </span>
                            <span className="font-mono text-gray-400">
                              {new Date(log.attempted_at).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{log.status}</span>
                            <span className="text-gray-500">
                              {log.previous_value || "None"} &rarr; {log.new_value || "None"}
                            </span>
                          </div>
                          {log.error_message && <p className="text-rose-600">{log.error_message}</p>}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* RESOLUTION MODAL */}
      {resolvingFinding && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                  Safe Finding Resolution
                </span>
                <h3 className="text-lg font-bold text-gray-900 mt-0.5">{resolvingFinding.title}</h3>
              </div>
              <button onClick={() => setResolvingFinding(null)} className="text-gray-400 hover:text-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-200">
              {resolvingFinding.description}
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Resolution Outcome</label>
                <select
                  value={resolutionStatus}
                  onChange={e => setResolutionStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
                >
                  <option value="RESOLVED">RESOLVED (Issue verified and corrected)</option>
                  <option value="IGNORED">IGNORED (Accepted risk / verified intentional)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Operator Justification / Notes <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={e => setResolutionNotes(e.target.value)}
                  placeholder="Explain why this finding is being resolved or ignored for audit trail..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Auditor Attribution Name</label>
                <input
                  type="text"
                  value={resolutionOperator}
                  onChange={e => setResolutionOperator(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => setResolvingFinding(null)}
                className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveFindingSubmit}
                disabled={actionLoading}
                className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MANUAL CORRECTION MODAL */}
      {correctionModalOpen && selectedPublisherId && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                  Audited Human Correction
                </span>
                <h3 className="text-lg font-bold text-gray-900 mt-0.5">Correct Publisher Observation</h3>
              </div>
              <button onClick={() => setCorrectionModalOpen(false)} className="text-gray-400 hover:text-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-500">
              Preserves historical records and records a new observation marked as <strong>HUMAN_VERIFIED</strong>, with
              attribution logged to CRM activity.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Field to Correct</label>
                <select
                  value={correctionField}
                  onChange={e => setCorrectionField(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
                >
                  <option value="price">Price</option>
                  <option value="currency">Currency</option>
                  <option value="metric_da">Domain Authority (DA)</option>
                  <option value="metric_dr">Domain Rating (DR)</option>
                  <option value="metric_traffic">Organic Traffic</option>
                  <option value="website_url">Website URL</option>
                </select>
              </div>

              {correctionField === "price" && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Currency</label>
                  <select
                    value={correctionCurrency}
                    onChange={e => setCorrectionCurrency(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="CAD">CAD (C$)</option>
                    <option value="AUD">AUD (A$)</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">New Value</label>
                <input
                  type="text"
                  placeholder="e.g. 750 or https://verified-domain.com"
                  value={correctionValue}
                  onChange={e => setCorrectionValue(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Correction Reason / Provenance <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={correctionReason}
                  onChange={e => setCorrectionReason(e.target.value)}
                  placeholder="Reason for correction (e.g. Direct quote from publisher media kit, corrected typo)..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Operator Name</label>
                <input
                  type="text"
                  value={correctionOperator}
                  onChange={e => setCorrectionOperator(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => setCorrectionModalOpen(false)}
                className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleApplyCorrectionSubmit}
                disabled={actionLoading}
                className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Apply & Save Observation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
