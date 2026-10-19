"use client";

import { useEffect, useState, useMemo } from "react";
import {
  api,
  PrioritizedProspectItem,
  SalesIntelligenceScore,
  SalesOpportunity,
  SalesBrief,
  ProspectComparisonDetail
} from "@/lib/api";
import {
  Target,
  Search,
  Filter,
  RefreshCw,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  ArrowUpDown,
  BookOpen,
  FileText,
  Sliders,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Check,
  X,
  Plus,
  Edit3,
  Download,
  Info,
  Calendar,
  User,
  Kanban
} from "lucide-react";

export default function SalesIntelligencePage() {
  // Main Data States
  const [queueItems, setQueueItems] = useState<PrioritizedProspectItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [industryFilter, setIndustryFilter] = useState("ALL");
  const [serviceFilter, setServiceFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [reviewStatusFilter, setReviewStatusFilter] = useState("ALL");
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>("overall_priority_score");
  const [sortDesc, setSortDesc] = useState<boolean>(true);

  // Selection for Comparison
  const [selectedProspectIds, setSelectedProspectIds] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<ProspectComparisonDetail[] | null>(null);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Active Selected Prospect & Modal States
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(null);
  const [activeScoreData, setActiveScoreData] = useState<SalesIntelligenceScore | null>(null);
  const [activeOpportunities, setActiveOpportunities] = useState<SalesOpportunity[]>([]);
  const [activeBrief, setActiveBrief] = useState<SalesBrief | null>(null);

  // Modals visibility
  const [showScoreModal, setShowScoreModal] = useState(false);
  const [showOppsModal, setShowOppsModal] = useState(false);
  const [showBriefModal, setShowBriefModal] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);

  // Modal Input States
  const [overrideScoreInput, setOverrideScoreInput] = useState<number>(75);
  const [overrideReasonInput, setOverrideReasonInput] = useState<string>("");
  const [overrideActorInput, setOverrideActorInput] = useState<string>("sales_executive");

  // Brief Editing State
  const [briefMarkdownEdit, setBriefMarkdownEdit] = useState<string>("");
  const [isEditingBrief, setIsEditingBrief] = useState<boolean>(false);

  // Task Creation State
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDueDate, setTaskDueDate] = useState("");
  const [taskPriority, setTaskPriority] = useState("HIGH");

  // Load Queue Data
  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await api.getPrioritizedQueue({
        industry: industryFilter !== "ALL" ? industryFilter : undefined,
        service_fit: serviceFilter !== "ALL" ? serviceFilter : undefined,
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
        review_status: reviewStatusFilter !== "ALL" ? reviewStatusFilter : undefined,
        min_score: minScoreFilter > 0 ? minScoreFilter : undefined,
        sort_by: sortBy,
        sort_desc: sortDesc,
        limit: 100,
        offset: 0
      });
      setQueueItems(res.items || []);
      setTotalCount(res.total || 0);
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to load prioritized sales queue."
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [industryFilter, serviceFilter, categoryFilter, reviewStatusFilter, minScoreFilter, sortBy, sortDesc]);

  // Derived filter for client search
  const filteredQueueItems = useMemo(() => {
    if (!searchQuery.trim()) return queueItems;
    const q = searchQuery.toLowerCase();
    return queueItems.filter(
      (item) =>
        item.company_name.toLowerCase().includes(q) ||
        (item.canonical_domain && item.canonical_domain.toLowerCase().includes(q))
    );
  }, [queueItems, searchQuery]);

  // Metrics KPI calculations
  const highPriorityCount = useMemo(() => {
    return queueItems.filter((i) => i.effective_score >= 70).length;
  }, [queueItems]);

  const criticalIssuesCount = useMemo(() => {
    return queueItems.reduce((acc, curr) => acc + (curr.critical_opportunities_count || 0), 0);
  }, [queueItems]);

  const uniqueIndustries = useMemo(() => {
    const set = new Set<string>();
    queueItems.forEach((i) => {
      if (i.industry) set.add(i.industry);
    });
    return Array.from(set).sort();
  }, [queueItems]);

  // Handlers
  const handleOpenScore = async (companyId: string) => {
    try {
      setActionLoading(true);
      setActiveCompanyId(companyId);
      const score = await api.getSalesIntelligenceScore(companyId);
      setActiveScoreData(score);
      setShowScoreModal(true);
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to fetch score breakdown." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenOpportunities = async (companyId: string) => {
    try {
      setActionLoading(true);
      setActiveCompanyId(companyId);
      const opps = await api.getSalesOpportunities(companyId);
      setActiveOpportunities(opps);
      setShowOppsModal(true);
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to fetch opportunities." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenBrief = async (companyId: string) => {
    try {
      setActionLoading(true);
      setActiveCompanyId(companyId);
      const brief = await api.getSalesBrief(companyId);
      setActiveBrief(brief);
      setBriefMarkdownEdit(brief.full_brief_markdown);
      setIsEditingBrief(false);
      setShowBriefModal(true);
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to generate sales brief." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveBrief = async () => {
    if (!activeCompanyId) return;
    try {
      setActionLoading(true);
      const updated = await api.updateSalesBrief(activeCompanyId, {
        markdown: briefMarkdownEdit,
        edited_by: "account_executive"
      });
      setActiveBrief(updated);
      setIsEditingBrief(false);
      setNotification({ type: "success", message: "Sales intelligence brief customized & saved." });
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to update sales brief." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenOverride = (item: PrioritizedProspectItem) => {
    setActiveCompanyId(item.company_id);
    setOverrideScoreInput(item.human_override_score ?? item.overall_priority_score);
    setOverrideReasonInput(item.human_override_reason || "");
    setShowOverrideModal(true);
  };

  const handleSubmitOverride = async () => {
    if (!activeCompanyId) return;
    if (!overrideReasonInput.trim()) {
      setNotification({ type: "error", message: "A documented override reason is required." });
      return;
    }
    try {
      setActionLoading(true);
      await api.overrideProspectScore(activeCompanyId, {
        score: Number(overrideScoreInput),
        reason: overrideReasonInput.trim(),
        actor: overrideActorInput.trim() || "sales_executive"
      });
      setShowOverrideModal(false);
      setNotification({ type: "success", message: "Priority score override recorded with audit history." });
      loadQueue();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to submit score override." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateReviewStatus = async (companyId: string, newStatus: string) => {
    try {
      setActionLoading(true);
      await api.updateReviewStatus(companyId, {
        review_status: newStatus,
        reviewer: "sales_lead"
      });
      setNotification({ type: "success", message: `Prospect marked as ${newStatus}.` });
      loadQueue();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to update review status." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleSelectProspect = (companyId: string) => {
    if (selectedProspectIds.includes(companyId)) {
      setSelectedProspectIds(selectedProspectIds.filter((id) => id !== companyId));
    } else {
      if (selectedProspectIds.length >= 5) {
        setNotification({ type: "info", message: "You can compare up to 5 prospects simultaneously." });
        return;
      }
      setSelectedProspectIds([...selectedProspectIds, companyId]);
    }
  };

  const handleOpenComparison = async () => {
    if (selectedProspectIds.length < 2) {
      setNotification({ type: "info", message: "Select at least 2 prospects to compare side-by-side." });
      return;
    }
    try {
      setActionLoading(true);
      const res = await api.compareProspects(selectedProspectIds);
      setComparisonData(res.compared_prospects);
      setShowComparisonModal(true);
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to compare prospects." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenTaskModal = (companyId: string, companyName: string) => {
    setActiveCompanyId(companyId);
    setTaskTitle(`Follow up on SEO findings for ${companyName}`);
    setTaskPriority("HIGH");
    const d = new Date();
    d.setDate(d.getDate() + 2);
    setTaskDueDate(d.toISOString().split("T")[0]);
    setShowTaskModal(true);
  };

  const handleCreateTask = async () => {
    if (!activeCompanyId || !taskTitle.trim()) return;
    try {
      setActionLoading(true);
      await api.post("/crm/tasks", {
        company_id: activeCompanyId,
        title: taskTitle.trim(),
        priority: taskPriority,
        due_date: taskDueDate || null
      });
      setShowTaskModal(false);
      setNotification({ type: "success", message: "CRM follow-up task created successfully." });
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Failed to create CRM task." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchEvaluate = async () => {
    try {
      setActionLoading(true);
      const targetIds = queueItems.slice(0, 10).map((i) => i.company_id);
      if (targetIds.length === 0) {
        setNotification({ type: "info", message: "No prospects available for batch evaluation." });
        return;
      }
      await api.batchEvaluateSalesIntelligence(targetIds);
      setNotification({
        type: "success",
        message: `Batch evaluation completed for ${targetIds.length} prospects.`
      });
      loadQueue();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Batch evaluation failed." });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between border ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : notification.type === "error"
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-blue-50 text-blue-800 border-blue-200"
          }`}
        >
          <div className="flex items-center space-x-2">
            {notification.type === "success" && <CheckCircle2 className="w-5 h-5" />}
            {notification.type === "error" && <XCircle className="w-5 h-5" />}
            {notification.type === "info" && <Info className="w-5 h-5" />}
            <span className="text-sm font-medium">{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-gray-500 hover:text-gray-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600 rounded-lg text-white">
              <Target className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Sales Intelligence & Lead Prioritization</h1>
              <p className="text-sm text-gray-500">
                Evidence-driven GrokxSEO service matching, explainable scoring v3.0.0, and intelligence briefs.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {selectedProspectIds.length >= 2 && (
            <button
              onClick={handleOpenComparison}
              disabled={actionLoading}
              className="px-4 py-2 bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <ArrowUpDown className="w-4 h-4" />
              <span>Compare Selected ({selectedProspectIds.length})</span>
            </button>
          )}

          <button
            onClick={handleBatchEvaluate}
            disabled={actionLoading || loading}
            className="px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium flex items-center space-x-2 shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Re-evaluate Top 10</span>
          </button>

          <button
            onClick={loadQueue}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Queue Total</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{totalCount}</div>
            <div className="text-xs text-gray-500 mt-1">Evaluated sales prospects</div>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-emerald-700 uppercase tracking-wider">High Priority Leads</div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">{highPriorityCount}</div>
            <div className="text-xs text-gray-500 mt-1">Score ≥ 70 with strong service fit</div>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-rose-700 uppercase tracking-wider">Critical SEO Deficits</div>
            <div className="text-2xl font-bold text-rose-700 mt-1">{criticalIssuesCount}</div>
            <div className="text-xs text-gray-500 mt-1">Observed server & indexing blockers</div>
          </div>
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-purple-700 uppercase tracking-wider">Review Pipeline</div>
            <div className="text-2xl font-bold text-purple-700 mt-1">
              {queueItems.filter((i) => i.review_status === "QUALIFIED").length}
            </div>
            <div className="text-xs text-gray-500 mt-1">Qualified & ready for outreach</div>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search prospects by company name or domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Industry Filter */}
          <select
            value={industryFilter}
            onChange={(e) => setIndustryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Industries</option>
            {uniqueIndustries.map((ind) => (
              <option key={ind} value={ind}>
                {ind}
              </option>
            ))}
          </select>

          {/* Service Fit Filter */}
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Services</option>
            <option value="TECHNICAL_SEO">Technical SEO</option>
            <option value="LINK_BUILDING">Link Building & Authority</option>
            <option value="DIGITAL_PR">Digital PR & Outreach</option>
            <option value="CONTENT_STRATEGY">Content Strategy</option>
            <option value="CONTENT_ARCHITECTURE">Content Architecture</option>
            <option value="SEO_STRATEGY">SEO Strategy</option>
            <option value="CONVERSION_OPTIMIZATION">Conversion Optimization</option>
            <option value="LOCAL_SEO">Local SEO</option>
            <option value="WEBSITE_REDESIGN">Website Redesign</option>
          </select>

          {/* Review Status Filter */}
          <select
            value={reviewStatusFilter}
            onChange={(e) => setReviewStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Review Statuses</option>
            <option value="UNREVIEWED">Unreviewed</option>
            <option value="IN_REVIEW">In Review</option>
            <option value="QUALIFIED">Qualified</option>
            <option value="REJECTED">Rejected</option>
          </select>

          {/* Score Threshold */}
          <select
            value={minScoreFilter}
            onChange={(e) => setMinScoreFilter(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={0}>Min Score: Any</option>
            <option value={50}>Min Score: 50+</option>
            <option value={70}>Min Score: 70+ (High)</option>
            <option value={85}>Min Score: 85+ (Tier 1)</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="overall_priority_score">Sort: Priority Score</option>
            <option value="seo_severity_score">Sort: SEO Severity</option>
            <option value="service_fit_score">Sort: Service Fit</option>
            <option value="publisher_fit_score">Sort: Publisher Fit</option>
            <option value="company_name">Sort: Company Name</option>
          </select>

          <button
            onClick={() => setSortDesc(!sortDesc)}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600 text-sm flex items-center"
            title="Toggle sort direction"
          >
            <ArrowUpDown className="w-4 h-4" />
          </button>
        </div>

        {selectedProspectIds.length > 0 && (
          <div className="flex items-center justify-between text-xs text-indigo-700 bg-indigo-50 px-3 py-2 rounded-lg">
            <span>
              {selectedProspectIds.length} prospect(s) selected for comparison. Click &quot;Compare Selected&quot; to inspect side-by-side.
            </span>
            <button
              onClick={() => setSelectedProspectIds([])}
              className="text-indigo-600 hover:text-indigo-900 font-medium underline"
            >
              Clear selection
            </button>
          </div>
        )}
      </div>

      {/* Prioritized Sales Queue Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
            <p className="text-sm">Calculating explainable priority scores & evaluating lead opportunities...</p>
          </div>
        ) : filteredQueueItems.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-base font-medium text-gray-700">No prospects match the configured filters.</p>
            <p className="text-sm text-gray-400 mt-1">Try resetting the industry, service, or minimum score criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-4 w-10 text-center">
                    <span className="sr-only">Select</span>
                  </th>
                  <th className="py-3 px-4">Priority Score</th>
                  <th className="py-3 px-4">Prospect & Domain</th>
                  <th className="py-3 px-4">Industry / CRM Stage</th>
                  <th className="py-3 px-4">Primary Service Fit</th>
                  <th className="py-3 px-4">Observed Deficits</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4 text-right">Intelligence Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredQueueItems.map((item, idx) => {
                  const isSelected = selectedProspectIds.includes(item.company_id);
                  const isOverridden = item.human_override_score !== null && item.human_override_score !== undefined;
                  const score = item.effective_score;

                  return (
                    <tr
                      key={item.company_id}
                      className={`hover:bg-gray-50 transition-colors ${isSelected ? "bg-indigo-50/40" : ""}`}
                    >
                      {/* Checkbox */}
                      <td className="py-3 px-4 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelectProspect(item.company_id)}
                          className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4 border-gray-300"
                        />
                      </td>

                      {/* Score Badge */}
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold ${
                              score >= 80
                                ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                                : score >= 60
                                ? "bg-indigo-100 text-indigo-800 border border-indigo-300"
                                : score >= 40
                                ? "bg-amber-100 text-amber-800 border border-amber-300"
                                : "bg-gray-100 text-gray-700 border border-gray-300"
                            }`}
                          >
                            {score.toFixed(1)}
                          </span>

                          {isOverridden && (
                            <span
                              className="p-1 bg-amber-50 text-amber-700 border border-amber-200 rounded text-[10px] font-semibold"
                              title={`Human override applied by ${item.human_override_reason || "account lead"}`}
                            >
                              OVERRIDE
                            </span>
                          )}
                        </div>

                        {/* Mini score breakdown bars */}
                        <div className="flex items-center space-x-1 mt-1 text-[10px] text-gray-400">
                          <span>SEO: {item.seo_severity_score.toFixed(0)}</span>
                          <span>•</span>
                          <span>Fit: {item.service_fit_score.toFixed(0)}</span>
                          <span>•</span>
                          <span>Pub: {item.publisher_fit_score.toFixed(0)}</span>
                        </div>
                      </td>

                      {/* Prospect & Domain */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gray-900">{item.company_name}</div>
                        {item.canonical_domain ? (
                          <div className="text-xs text-gray-500 flex items-center space-x-1">
                            <span>{item.canonical_domain}</span>
                            {item.website_url && (
                              <a
                                href={item.website_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-gray-400 hover:text-indigo-600"
                              >
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400 italic">Domain not available</span>
                        )}
                      </td>

                      {/* Industry & Sales Stage */}
                      <td className="py-3 px-4">
                        <div className="text-xs font-medium text-gray-700">{item.industry || "Uncategorized"}</div>
                        <span className="inline-block px-2 py-0.5 mt-1 bg-gray-100 text-gray-600 rounded text-[10px] font-medium">
                          {item.sales_stage}
                        </span>
                      </td>

                      {/* Primary Service Fit */}
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 text-xs font-medium">
                          {item.primary_recommended_service.replace(/_/g, " ")}
                        </span>
                      </td>

                      {/* Observed Deficits */}
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-700 font-medium">
                            {item.total_opportunities_count} found
                          </span>
                          {item.critical_opportunities_count > 0 && (
                            <span className="px-1.5 py-0.5 bg-rose-100 text-rose-800 rounded text-[10px] font-bold">
                              {item.critical_opportunities_count} Critical
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Review Status Dropdown */}
                      <td className="py-3 px-4">
                        <select
                          value={item.review_status}
                          onChange={(e) => handleUpdateReviewStatus(item.company_id, e.target.value)}
                          className={`text-xs font-medium rounded px-2 py-1 border ${
                            item.review_status === "QUALIFIED"
                              ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                              : item.review_status === "IN_REVIEW"
                              ? "bg-blue-50 text-blue-800 border-blue-300"
                              : item.review_status === "REJECTED"
                              ? "bg-rose-50 text-rose-800 border-rose-300"
                              : "bg-gray-50 text-gray-700 border-gray-300"
                          }`}
                        >
                          <option value="UNREVIEWED">UNREVIEWED</option>
                          <option value="IN_REVIEW">IN REVIEW</option>
                          <option value="QUALIFIED">QUALIFIED</option>
                          <option value="REJECTED">REJECTED</option>
                        </select>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <button
                            onClick={() => handleOpenScore(item.company_id)}
                            className="p-1.5 hover:bg-gray-100 text-gray-600 rounded"
                            title="Explainable Score & Weights"
                          >
                            <Sliders className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => handleOpenOpportunities(item.company_id)}
                            className="p-1.5 hover:bg-gray-100 text-gray-600 rounded"
                            title="View Opportunities & Evidence"
                          >
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                          </button>

                          <button
                            onClick={() => handleOpenBrief(item.company_id)}
                            className="p-1.5 hover:bg-gray-100 text-indigo-600 rounded"
                            title="Sales Intelligence Brief"
                          >
                            <FileText className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => handleOpenOverride(item)}
                            className="p-1.5 hover:bg-gray-100 text-gray-600 rounded"
                            title="Human Override Score"
                          >
                            <Edit3 className="w-4 h-4 text-gray-500" />
                          </button>

                          <button
                            onClick={() => handleOpenTaskModal(item.company_id, item.company_name)}
                            className="p-1.5 hover:bg-gray-100 text-emerald-600 rounded"
                            title="Create CRM Follow-Up Task"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* MODAL 1: EXPLAINABLE SCORE & FACTOR BREAKDOWN */}
      {/* ========================================================================= */}
      {showScoreModal && activeScoreData && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Explainable Scoring & Factor Breakdown</h2>
                <p className="text-xs text-gray-500">
                  Model: {activeScoreData.scoring_version} • Evaluated:{" "}
                  {new Date(activeScoreData.evaluated_at).toLocaleString()}
                </p>
              </div>
              <button onClick={() => setShowScoreModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Overall Score Banner */}
            <div className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-100 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Overall Priority Score</div>
                <div className="text-3xl font-extrabold text-indigo-900 mt-1">
                  {activeScoreData.overall_priority_score.toFixed(1)} / 100
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Primary Recommendation:{" "}
                  <strong className="text-indigo-900">
                    {activeScoreData.primary_recommended_service.replace(/_/g, " ")}
                  </strong>
                </div>
              </div>
              {activeScoreData.human_override_score !== null && activeScoreData.human_override_score !== undefined && (
                <div className="text-right p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="text-[10px] font-bold text-amber-800 uppercase">Human Override Active</div>
                  <div className="text-lg font-bold text-amber-900">{activeScoreData.human_override_score.toFixed(1)}</div>
                  <div className="text-[10px] text-amber-700">by {activeScoreData.human_override_by}</div>
                </div>
              )}
            </div>

            {/* Factor Weights & Component Scores */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-900">Configured Component Scoring</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between font-medium text-gray-700">
                    <span>SEO Deficit Severity</span>
                    <span>{activeScoreData.seo_severity_score.toFixed(1)} / 100</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2">
                    <div
                      className="bg-rose-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, activeScoreData.seo_severity_score)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">
                    Weight: {(activeScoreData.scoring_weights_used?.seo_severity * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between font-medium text-gray-700">
                    <span>GrokxSEO Service Fit</span>
                    <span>{activeScoreData.service_fit_score.toFixed(1)} / 100</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2">
                    <div
                      className="bg-indigo-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, activeScoreData.service_fit_score)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">
                    Weight: {(activeScoreData.scoring_weights_used?.service_fit * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between font-medium text-gray-700">
                    <span>Publisher Inventory Alignment</span>
                    <span>{activeScoreData.publisher_fit_score.toFixed(1)} / 100</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, activeScoreData.publisher_fit_score)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">
                    Weight: {(activeScoreData.scoring_weights_used?.publisher_fit * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between font-medium text-gray-700">
                    <span>Evidence Confidence</span>
                    <span>{(activeScoreData.evidence_confidence_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2">
                    <div
                      className="bg-emerald-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, activeScoreData.evidence_confidence_score * 100)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1">
                    Weight: {(activeScoreData.scoring_weights_used?.evidence_confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Positive Indicators */}
            {activeScoreData.positive_indicators?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-2">
                  Observed Positive Indicators
                </h4>
                <ul className="space-y-1 text-xs text-gray-700">
                  {activeScoreData.positive_indicators.map((ind, i) => (
                    <li key={i} className="flex items-start space-x-2">
                      <Check className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                      <span>{ind}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Limitations & Missing Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-2">
                  Known Limitations
                </h4>
                <ul className="space-y-1 text-xs text-gray-600">
                  {activeScoreData.limitations?.map((lim, i) => (
                    <li key={i} className="flex items-start space-x-1.5">
                      <span className="text-amber-500 font-bold">•</span>
                      <span>{lim}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
                  Data Gaps & Missing Info
                </h4>
                <ul className="space-y-1 text-xs text-gray-600">
                  {activeScoreData.missing_information?.map((gap, i) => (
                    <li key={i} className="flex items-start space-x-1.5">
                      <span className="text-gray-400 font-bold">•</span>
                      <span>{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommended Next Action */}
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-xs text-indigo-900">
              <strong className="block font-semibold mb-0.5">Recommended Next Action:</strong>
              {activeScoreData.recommended_next_action}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: OPPORTUNITIES & SUPPORTING EVIDENCE */}
      {/* ========================================================================= */}
      {showOppsModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Detected SEO Opportunities & Evidence</h2>
                <p className="text-xs text-gray-500">
                  {activeOpportunities.length} opportunities detected from observable scan & metric data.
                </p>
              </div>
              <button onClick={() => setShowOppsModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {activeOpportunities.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No distinct opportunities detected from current scans.
              </div>
            ) : (
              <div className="space-y-4">
                {activeOpportunities.map((opp) => (
                  <div key={opp.id} className="p-4 border rounded-xl space-y-2 bg-gray-50/50">
                    <div className="flex items-center justify-between">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          opp.severity === "CRITICAL"
                            ? "bg-rose-100 text-rose-800"
                            : opp.severity === "HIGH"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {opp.severity} • {opp.category.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-indigo-700 font-medium">
                        Service: {opp.recommended_service.replace(/_/g, " ")}
                      </span>
                    </div>

                    <h3 className="text-sm font-semibold text-gray-900">{opp.title}</h3>
                    <p className="text-xs text-gray-600">{opp.description}</p>

                    <div className="text-xs text-gray-700 bg-white p-2.5 rounded border border-gray-200">
                      <strong>Impact Rationale:</strong> {opp.impact_rationale}
                    </div>

                    {opp.supporting_evidence && opp.supporting_evidence.length > 0 && (
                      <div className="text-xs text-gray-500 bg-gray-100 p-2.5 rounded font-mono">
                        <div className="text-[10px] font-sans font-semibold text-gray-700 uppercase mb-1">
                          Traceable Evidence Trace:
                        </div>
                        {opp.supporting_evidence.map((ev, evIdx) => (
                          <div key={evIdx} className="truncate">
                            {JSON.stringify(ev)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: SALES INTELLIGENCE BRIEF VIEWER & EDITOR */}
      {/* ========================================================================= */}
      {showBriefModal && activeBrief && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[92vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl font-bold text-gray-900">{activeBrief.title}</h2>
                  {activeBrief.is_customized && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-[10px] font-bold">
                      CUSTOMIZED v{activeBrief.version}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  Ready-to-pitch briefing with discovery questions and matched publishers.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <a
                  href={api.exportSalesBriefUrl(activeBrief.company_id)}
                  target="_blank"
                  rel="noreferrer"
                  download
                  className="px-3 py-1.5 border border-gray-300 hover:bg-gray-50 rounded-lg text-xs font-medium flex items-center space-x-1.5"
                >
                  <Download className="w-3.5 h-3.5 text-gray-600" />
                  <span>Export .MD</span>
                </a>

                {isEditingBrief ? (
                  <button
                    onClick={handleSaveBrief}
                    disabled={actionLoading}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium flex items-center space-x-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Save Brief</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setIsEditingBrief(true)}
                    className="px-3 py-1.5 border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg text-xs font-medium flex items-center space-x-1"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Edit Markdown</span>
                  </button>
                )}

                <button onClick={() => setShowBriefModal(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Matched Publishers Preview Strip */}
            {activeBrief.matched_publishers && activeBrief.matched_publishers.length > 0 && (
              <div className="p-3 bg-purple-50 border border-purple-100 rounded-lg">
                <div className="text-xs font-semibold text-purple-900 uppercase tracking-wider mb-2">
                  Aligned Publishers from GrokxSEO Inventory ({activeBrief.matched_publishers.length})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {activeBrief.matched_publishers.map((pub, pIdx) => (
                    <div key={pIdx} className="bg-white p-2 rounded border border-purple-200 text-xs">
                      <div className="font-semibold text-gray-900 truncate">{pub.publisher_name}</div>
                      <div className="text-[10px] text-gray-500">
                        {pub.canonical_domain ? `Domain: ${pub.canonical_domain}` : "Vetted Publisher"}
                      </div>
                      <div className="text-[10px] text-purple-700 font-bold mt-1">
                        DA {pub.da ?? "N/A"} • {pub.price ? `$${pub.price}` : "Direct Contact"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Brief Content (View or Edit) */}
            {isEditingBrief ? (
              <div className="space-y-2">
                <div className="text-xs text-gray-500 font-medium">Edit structured brief in Markdown format:</div>
                <textarea
                  value={briefMarkdownEdit}
                  onChange={(e) => setBriefMarkdownEdit(e.target.value)}
                  rows={18}
                  className="w-full p-4 border border-gray-300 rounded-xl font-mono text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            ) : (
              <div className="prose prose-sm max-w-none p-5 bg-gray-50 rounded-xl border border-gray-200 overflow-x-auto whitespace-pre-wrap font-sans text-xs text-gray-800 leading-relaxed">
                {activeBrief.full_brief_markdown}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 4: SIDE-BY-SIDE PROSPECT COMPARISON */}
      {/* ========================================================================= */}
      {showComparisonModal && comparisonData && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Side-by-Side Lead Comparison</h2>
                <p className="text-xs text-gray-500">
                  Comparing {comparisonData.length} selected prospects on service fit and opportunity severity.
                </p>
              </div>
              <button onClick={() => setShowComparisonModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comparisonData.map((comp) => (
                <div key={comp.company_id} className="p-4 border rounded-xl bg-gray-50/50 space-y-3">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="font-bold text-sm text-gray-900 truncate">{comp.company_name}</span>
                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded font-bold text-xs">
                      {comp.effective_score.toFixed(1)}
                    </span>
                  </div>

                  <div className="text-xs text-gray-600">
                    <div>
                      <strong>Domain:</strong> {comp.canonical_domain || "N/A"}
                    </div>
                    <div>
                      <strong>Industry:</strong> {comp.industry || "Uncategorized"}
                    </div>
                    <div>
                      <strong>CRM Stage:</strong> {comp.sales_stage}
                    </div>
                    <div>
                      <strong>Review Status:</strong> {comp.review_status}
                    </div>
                  </div>

                  <div className="text-xs">
                    <strong className="block text-indigo-900 mb-1">Primary Recommended Service:</strong>
                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded text-[11px] font-semibold">
                      {comp.primary_recommended_service.replace(/_/g, " ")}
                    </span>
                  </div>

                  {comp.top_opportunities?.length > 0 && (
                    <div className="text-xs space-y-1">
                      <strong className="block text-gray-700">Top Deficits:</strong>
                      <ul className="list-disc pl-4 text-gray-600 space-y-0.5 text-[11px]">
                        {comp.top_opportunities.map((opp, oIdx) => (
                          <li key={oIdx}>{opp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="text-xs text-purple-700 pt-2 border-t border-gray-200">
                    <strong>Inventory Match:</strong> {comp.matched_publisher_count} aligned publishers
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 5: HUMAN OVERRIDE */}
      {/* ========================================================================= */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Record Human Priority Override</h3>
              <button onClick={() => setShowOverrideModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-500">
              Adjust this prospect&apos;s priority score. Overrides are audited in CRM activity history.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Override Score (0 - 100):</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.5}
                  value={overrideScoreInput}
                  onChange={(e) => setOverrideScoreInput(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Reason for Override (Required):</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Verified high enterprise budget during initial discovery call..."
                  value={overrideReasonInput}
                  onChange={(e) => setOverrideReasonInput(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Reviewer / Actor:</label>
                <input
                  type="text"
                  value={overrideActorInput}
                  onChange={(e) => setOverrideActorInput(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t">
              <button
                onClick={() => setShowOverrideModal(false)}
                className="px-3 py-1.5 border rounded-lg text-xs text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitOverride}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium"
              >
                Save Override
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 6: CREATE QUICK CRM TASK */}
      {/* ========================================================================= */}
      {showTaskModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Create Follow-up CRM Task</h3>
              <button onClick={() => setShowTaskModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Task Title:</label>
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Due Date:</label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Priority:</label>
                <select
                  value={taskPriority}
                  onChange={(e) => setTaskPriority(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t">
              <button
                onClick={() => setShowTaskModal(false)}
                className="px-3 py-1.5 border rounded-lg text-xs text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTask}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium"
              >
                Create Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
