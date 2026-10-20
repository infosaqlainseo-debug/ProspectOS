"use client";

import { useEffect, useState, useMemo } from "react";
import {
  api,
  PipelineColumn,
  UnifiedProspectSummary,
  UnifiedProspectDetail,
  CRMDeal,
  CRMTask,
  CRMActivity,
  CRMNote,
  CRMReportMetrics,
  SalesStage,
  Company
} from "@/lib/api";
import {
  Kanban,
  Building2,
  DollarSign,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  Plus,
  ChevronRight,
  X,
  User,
  Phone,
  Calendar,
  RefreshCw,
  FileText,
  Search,
  Filter,
  TrendingUp,
  BarChart3,
  Layers,
  Check,
  Briefcase,
  Mail,
  Send,
  MessageSquare,
  Globe,
  Award,
  ExternalLink,
  ShieldAlert,
  HardDrive,
  Share2,
  PhoneCall
} from "lucide-react";

function FacebookIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
    </svg>
  );
}

function InstagramIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  );
}

const STAGE_ORDER: SalesStage[] = [
  "NEW",
  "RESEARCHED",
  "QUALIFIED",
  "CONTACTED",
  "REPLIED",
  "MEETING_SCHEDULED",
  "PROPOSAL_SENT",
  "NEGOTIATION",
  "WON",
  "LOST",
  "NURTURE"
];

const STAGE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NEW: { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-300" },
  RESEARCHED: { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-300" },
  QUALIFIED: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-300" },
  CONTACTED: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-300" },
  REPLIED: { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-300" },
  MEETING_SCHEDULED: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-300" },
  PROPOSAL_SENT: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-300" },
  NEGOTIATION: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-300" },
  WON: { bg: "bg-green-100", text: "text-green-800", border: "border-green-400" },
  LOST: { bg: "bg-rose-100", text: "text-rose-800", border: "border-rose-400" },
  NURTURE: { bg: "bg-zinc-100", text: "text-zinc-700", border: "border-zinc-300" }
};

export default function CRMPage() {
  const [activeView, setActiveView] = useState<"kanban" | "prospects" | "deals" | "tasks" | "reports">("kanban");
  
  // Data
  const [metrics, setMetrics] = useState<CRMReportMetrics | null>(null);
  const [board, setBoard] = useState<PipelineColumn[]>([]);
  const [prospects, setProspects] = useState<UnifiedProspectSummary[]>([]);
  const [totalProspectsCount, setTotalProspectsCount] = useState(0);
  const [deals, setDeals] = useState<CRMDeal[]>([]);
  const [tasks, setTasks] = useState<CRMTask[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);

  // Loading & notification states
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<string>("ALL");
  const [taskStatusFilter, setTaskStatusFilter] = useState<string>("ALL");
  const [taskOverdueOnly, setTaskOverdueOnly] = useState(false);
  const [dealOutcomeFilter, setDealOutcomeFilter] = useState<string>("ALL");

  // Drawers & Modals
  const [selectedProspectId, setSelectedProspectId] = useState<string | null>(null);
  const [prospectDetail, setProspectDetail] = useState<UnifiedProspectDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Modal: Change Stage
  const [stageModalData, setStageModalData] = useState<{ companyId: string; companyName: string; currentStage: string; targetStage: string } | null>(null);
  const [stageReason, setStageReason] = useState("");
  const [stageNotes, setStageNotes] = useState("");

  // Modal: Create Deal
  const [dealModalOpen, setDealModalOpen] = useState(false);
  const [dealForm, setDealForm] = useState({
    company_id: "",
    deal_name: "",
    service_category: "FULL_SERVICE",
    stage: "DISCOVERY",
    estimated_value: 5000,
    currency: "USD",
    expected_close_date: "",
    notes: ""
  });

  // Modal: Edit Deal / Update Outcome
  const [editDeal, setEditDeal] = useState<CRMDeal | null>(null);
  const [dealOutcome, setDealOutcome] = useState<string>("OPEN");
  const [dealClosedAmount, setDealClosedAmount] = useState<number>(0);
  const [dealReasonText, setDealReasonText] = useState<string>("");

  // Modal: Create Task
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [taskForm, setTaskForm] = useState({
    company_id: "",
    title: "",
    description: "",
    task_type: "FOLLOW_UP",
    priority: "MEDIUM",
    due_date: "",
    deal_id: ""
  });

  // Modal: Complete Task
  const [completeTaskData, setCompleteTaskData] = useState<{ id: string; title: string } | null>(null);
  const [taskCompletionNotes, setTaskCompletionNotes] = useState("");

  // Note addition in detail view
  const [newNoteText, setNewNoteText] = useState("");

  const showNotice = (type: "success" | "error" | "info", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 6000);
  };

  // Initial Data Fetch
  const loadData = async () => {
    setLoading(true);
    try {
      const [m, b, pRes, dList, tList, cList] = await Promise.all([
        api.getCrmReportMetrics().catch(() => null),
        api.getPipelineBoard().catch(() => []),
        api.getCrmProspects({ limit: 100 }).catch(() => ({ total: 0, limit: 100, offset: 0, items: [] })),
        api.getCrmDeals({ limit: 100 }).catch(() => []),
        api.getCrmTasks({ limit: 100 }).catch(() => []),
        api.getCompanies(100).catch(() => [])
      ]);

      if (m) setMetrics(m);
      setBoard(b);
      setProspects(pRes.items || []);
      setTotalProspectsCount(pRes.total || 0);
      setDeals(dList);
      setTasks(tList);
      setCompanies(cList);
      if (cList.length > 0 && !dealForm.company_id) {
        setDealForm(prev => ({ ...prev, company_id: cList[0].id }));
        setTaskForm(prev => ({ ...prev, company_id: cList[0].id }));
      }
    } catch (err: any) {
      showNotice("error", err?.message || "Failed to load CRM data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Fetch Unified Prospect Detail when drawer opens
  const openProspectDetail = async (companyId: string) => {
    setSelectedProspectId(companyId);
    setDetailLoading(true);
    try {
      const detail = await api.getUnifiedProspectDetail(companyId);
      setProspectDetail(detail);
    } catch (err: any) {
      showNotice("error", `Could not load prospect dossier: ${err.message}`);
      setSelectedProspectId(null);
    } finally {
      setDetailLoading(false);
    }
  };

  // Handle Stage Transition Submit
  const handleStageUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stageModalData) return;
    setActionLoading(true);
    try {
      await api.updateProspectStage(stageModalData.companyId, {
        new_stage: stageModalData.targetStage,
        reason: stageReason || undefined,
        notes: stageNotes || undefined
      });
      showNotice("success", `Prospect stage transitioned to ${stageModalData.targetStage}`);
      setStageModalData(null);
      setStageReason("");
      setStageNotes("");
      await loadData();
      if (selectedProspectId === stageModalData.companyId) {
        await openProspectDetail(stageModalData.companyId);
      }
    } catch (err: any) {
      showNotice("error", `Stage update failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Deal Creation
  const handleCreateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dealForm.company_id || !dealForm.deal_name) {
      showNotice("error", "Company and Deal Name are required");
      return;
    }
    setActionLoading(true);
    try {
      await api.createCrmDeal({
        ...dealForm,
        estimated_value: Number(dealForm.estimated_value) || 0,
        expected_close_date: dealForm.expected_close_date ? new Date(dealForm.expected_close_date).toISOString() : undefined
      });
      showNotice("success", `Deal "${dealForm.deal_name}" created successfully`);
      setDealModalOpen(false);
      setDealForm(prev => ({
        ...prev,
        deal_name: "",
        estimated_value: 5000,
        notes: ""
      }));
      await loadData();
      if (selectedProspectId === dealForm.company_id) {
        await openProspectDetail(dealForm.company_id);
      }
    } catch (err: any) {
      showNotice("error", `Failed to create deal: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Deal Update / Close
  const handleUpdateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editDeal) return;
    setActionLoading(true);
    try {
      const updatePayload: any = {
        outcome: dealOutcome,
        closed_amount: dealOutcome === "WON" ? Number(dealClosedAmount) : undefined,
        win_reason: dealOutcome === "WON" ? dealReasonText : undefined,
        loss_reason: dealOutcome === "LOST" ? dealReasonText : undefined,
        stage: dealOutcome === "WON" ? "WON" : dealOutcome === "LOST" ? "LOST" : editDeal.stage
      };
      await api.updateCrmDeal(editDeal.id, updatePayload);
      showNotice("success", `Deal "${editDeal.deal_name}" updated successfully`);
      setEditDeal(null);
      await loadData();
      if (selectedProspectId === editDeal.company_id) {
        await openProspectDetail(editDeal.company_id);
      }
    } catch (err: any) {
      showNotice("error", `Failed to update deal: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Task Creation
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskForm.company_id || !taskForm.title) {
      showNotice("error", "Company and Title are required");
      return;
    }
    setActionLoading(true);
    try {
      const idempotencyKey = `manual_task_${taskForm.company_id}_${Date.now()}`;
      await api.createCrmTask({
        ...taskForm,
        deal_id: taskForm.deal_id || undefined,
        due_date: taskForm.due_date ? new Date(taskForm.due_date).toISOString() : undefined,
        idempotency_key: idempotencyKey
      });
      showNotice("success", "Task created successfully");
      setTaskModalOpen(false);
      setTaskForm(prev => ({ ...prev, title: "", description: "" }));
      await loadData();
      if (selectedProspectId === taskForm.company_id) {
        await openProspectDetail(taskForm.company_id);
      }
    } catch (err: any) {
      showNotice("error", `Failed to create task: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Task Completion
  const handleCompleteTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completeTaskData) return;
    setActionLoading(true);
    try {
      await api.completeCrmTask(completeTaskData.id, {
        completed_by: "human_reviewer",
        completion_notes: taskCompletionNotes || undefined
      });
      showNotice("success", `Task marked complete`);
      setCompleteTaskData(null);
      setTaskCompletionNotes("");
      await loadData();
      if (selectedProspectId) {
        await openProspectDetail(selectedProspectId);
      }
    } catch (err: any) {
      showNotice("error", `Failed to complete task: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Note Submission in Detail View
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProspectId || !newNoteText.trim()) return;
    setActionLoading(true);
    try {
      await api.addProspectNote(selectedProspectId, {
        content: newNoteText.trim(),
        author: "human_reviewer"
      });
      setNewNoteText("");
      showNotice("success", "Internal note added");
      await openProspectDetail(selectedProspectId);
      await loadData();
    } catch (err: any) {
      showNotice("error", `Failed to add note: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Filtered views
  const filteredProspects = useMemo(() => {
    return prospects.filter(p => {
      const matchesSearch = !searchQuery || 
        (p.company_name?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (p.canonical_domain?.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStage = stageFilter === "ALL" || p.sales_stage === stageFilter;
      return matchesSearch && matchesStage;
    });
  }, [prospects, searchQuery, stageFilter]);

  const filteredTasks = useMemo(() => {
    return tasks.filter(t => {
      const matchesStatus = taskStatusFilter === "ALL" || t.status === taskStatusFilter;
      const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== "COMPLETED";
      const matchesOverdue = !taskOverdueOnly || isOverdue;
      return matchesStatus && matchesOverdue;
    });
  }, [tasks, taskStatusFilter, taskOverdueOnly]);

  const filteredDeals = useMemo(() => {
    return deals.filter(d => {
      if (dealOutcomeFilter === "ALL") return true;
      if (dealOutcomeFilter === "OPEN") return d.outcome === "OPEN" || !d.outcome;
      return d.outcome === dealOutcomeFilter;
    });
  }, [deals, dealOutcomeFilter]);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Notifications */}
      {notification && (
        <div className={`p-4 rounded-lg flex items-center justify-between border ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
          notification.type === 'error' ? 'bg-rose-50 text-rose-800 border-rose-200' :
          'bg-blue-50 text-blue-800 border-blue-200'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
            {notification.type === 'error' && <AlertTriangle className="w-5 h-5 text-rose-600" />}
            {notification.type === 'info' && <Clock className="w-5 h-5 text-blue-600" />}
            <span className="text-sm font-medium">{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-200">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <Kanban className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">CRM & Sales Pipeline</h1>
              <p className="text-sm text-gray-500">
                Connected sales management bridging prospect discovery, SEO intelligence, publisher media plans, and outreach
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              if (companies.length > 0) {
                setDealForm(prev => ({ ...prev, company_id: companies[0].id }));
              }
              setDealModalOpen(true);
            }}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm transition"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Deal
          </button>
          <button
            onClick={() => {
              if (companies.length > 0) {
                setTaskForm(prev => ({ ...prev, company_id: companies[0].id }));
              }
              setTaskModalOpen(true);
            }}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 shadow-sm transition"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Task
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg border border-gray-200 transition"
            title="Refresh CRM Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Prospects</div>
          <div className="mt-2 text-2xl font-bold text-gray-900">{metrics?.total_prospects ?? totalProspectsCount}</div>
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <Building2 className="w-3.5 h-3.5 mr-1 text-gray-400" />
            Across 11 stages
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Qualified Prospects</div>
          <div className="mt-2 text-2xl font-bold text-emerald-700">{metrics?.qualified_prospects_count ?? 0}</div>
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <Award className="w-3.5 h-3.5 mr-1 text-emerald-500" />
            Verified SEO criteria
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Outreach Sent</div>
          <div className="mt-2 text-2xl font-bold text-blue-700">{metrics?.outreach_sent_count ?? 0}</div>
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <Send className="w-3.5 h-3.5 mr-1 text-blue-500" />
            {metrics?.replies_received_count ?? 0} replies confirmed
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Won Deals</div>
          <div className="mt-2 text-2xl font-bold text-green-700">{metrics?.won_deals_count ?? 0}</div>
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <Check className="w-3.5 h-3.5 mr-1 text-green-500" />
            {metrics?.conversion_rates?.["WON_RATE"] != null ? `${metrics.conversion_rates["WON_RATE"]}% win rate` : 'Closed authorized'}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/40 shadow-xs">
          <div className="text-xs font-semibold text-blue-800 uppercase tracking-wider">Open Pipeline</div>
          <div className="mt-2 text-2xl font-bold text-blue-900">
            ${(metrics?.open_pipeline_value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
          <div className="mt-1 text-xs text-blue-700 flex items-center">
            <TrendingUp className="w-3.5 h-3.5 mr-1 text-blue-600" />
            Estimated value (USD)
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/40 shadow-xs">
          <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Closed Revenue</div>
          <div className="mt-2 text-2xl font-bold text-emerald-900">
            ${(metrics?.closed_won_revenue ?? 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
          <div className="mt-1 text-xs text-emerald-700 flex items-center">
            <DollarSign className="w-3.5 h-3.5 mr-1 text-emerald-600" />
            Actual earned (USD)
          </div>
        </div>
      </div>

      {/* View Switcher Tabs */}
      <div className="border-b border-gray-200 flex space-x-8">
        <button
          onClick={() => setActiveView("kanban")}
          className={`pb-4 px-1 text-sm font-medium border-b-2 flex items-center transition ${
            activeView === "kanban"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <Kanban className="w-4 h-4 mr-2" />
          Pipeline Board
        </button>

        <button
          onClick={() => setActiveView("prospects")}
          className={`pb-4 px-1 text-sm font-medium border-b-2 flex items-center transition ${
            activeView === "prospects"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <Building2 className="w-4 h-4 mr-2" />
          Prospect Directory ({prospects.length})
        </button>

        <button
          onClick={() => setActiveView("deals")}
          className={`pb-4 px-1 text-sm font-medium border-b-2 flex items-center transition ${
            activeView === "deals"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <DollarSign className="w-4 h-4 mr-2" />
          Deals & Revenue ({deals.length})
        </button>

        <button
          onClick={() => setActiveView("tasks")}
          className={`pb-4 px-1 text-sm font-medium border-b-2 flex items-center transition ${
            activeView === "tasks"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <Clock className="w-4 h-4 mr-2" />
          Tasks & Follow-ups ({tasks.filter(t => t.status !== "COMPLETED").length} open)
        </button>

        <button
          onClick={() => setActiveView("reports")}
          className={`pb-4 px-1 text-sm font-medium border-b-2 flex items-center transition ${
            activeView === "reports"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          Conversion Reports
        </button>
      </div>

      {/* 1. KANBAN PIPELINE VIEW */}
      {activeView === "kanban" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Showing 11 sales pipeline stages. Click "Move" on any card to transition stage with validated rules and audit history.
            </p>
          </div>

          <div className="flex space-x-4 overflow-x-auto pb-6 pt-2">
            {board.map((col) => {
              const style = STAGE_COLORS[col.stage] || STAGE_COLORS.NEW;
              return (
                <div
                  key={col.stage}
                  className="w-72 shrink-0 bg-gray-50 rounded-xl border border-gray-200 flex flex-col max-h-[750px]"
                >
                  {/* Column Header */}
                  <div className={`p-3.5 border-b rounded-t-xl ${style.bg} ${style.border}`}>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-bold tracking-wider uppercase ${style.text}`}>
                        {col.stage_name}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-white text-gray-700 shadow-xs">
                        {col.prospects_count}
                      </span>
                    </div>
                    {col.total_pipeline_value > 0 && (
                      <div className="mt-1 text-xs font-semibold text-gray-600">
                        ${col.total_pipeline_value.toLocaleString()} value
                      </div>
                    )}
                  </div>

                  {/* Cards Container */}
                  <div className="p-2.5 flex-1 overflow-y-auto space-y-3">
                    {col.prospects.length === 0 ? (
                      <div className="py-8 text-center text-xs text-gray-400">
                        No prospects in this stage
                      </div>
                    ) : (
                      col.prospects.map((p) => (
                        <div
                          key={p.id}
                          className="bg-white p-3.5 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition cursor-pointer space-y-2.5"
                          onClick={() => openProspectDetail(p.id)}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="text-sm font-semibold text-gray-900 leading-tight">
                                {p.company_name || p.canonical_domain || "Unnamed Prospect"}
                              </h4>
                              <p className="text-xs text-gray-400 mt-0.5">{p.canonical_domain || "No domain"}</p>
                            </div>
                            {p.opportunity_score != null && (
                              <span className="text-xs font-bold px-1.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
                                {Math.round(p.opportunity_score)}/100
                              </span>
                            )}
                          </div>

                          {p.industry && (
                            <div className="text-xs text-gray-500 flex items-center">
                              <Building2 className="w-3 h-3 mr-1 text-gray-400" />
                              {p.industry}
                            </div>
                          )}

                          <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                            <span>
                              {p.total_deals > 0 ? (
                                <span className="font-semibold text-gray-700">
                                  ${p.open_deal_value.toLocaleString()}
                                </span>
                              ) : (
                                "No deals"
                              )}
                            </span>

                            <div className="flex items-center space-x-1.5" onClick={(e) => e.stopPropagation()}>
                              <select
                                value={p.sales_stage}
                                onChange={(e) => {
                                  const target = e.target.value;
                                  if (target !== p.sales_stage) {
                                    setStageModalData({
                                      companyId: p.id,
                                      companyName: p.company_name || p.canonical_domain || "Prospect",
                                      currentStage: p.sales_stage,
                                      targetStage: target
                                    });
                                  }
                                }}
                                className="text-xs bg-gray-50 border border-gray-300 text-gray-700 rounded px-1.5 py-0.5 hover:bg-gray-100 cursor-pointer"
                              >
                                {STAGE_ORDER.map(s => (
                                  <option key={s} value={s}>{s.replace("_", " ")}</option>
                                ))}
                              </select>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. PROSPECTS DIRECTORY VIEW */}
      {activeView === "prospects" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-4 rounded-xl border border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search by company name or domain..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-500 font-medium">Stage:</span>
                <select
                  value={stageFilter}
                  onChange={(e) => setStageFilter(e.target.value)}
                  className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ALL">All Stages</option>
                  {STAGE_ORDER.map(s => (
                    <option key={s} value={s}>{s.replace("_", " ")}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Prospects Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Company & Domain</th>
                  <th className="px-6 py-3">Sales Stage</th>
                  <th className="px-6 py-3">SEO Opp. Score</th>
                  <th className="px-6 py-3">Deals</th>
                  <th className="px-6 py-3">Tasks</th>
                  <th className="px-6 py-3">Contacts</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {filteredProspects.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-400 text-sm">
                      No prospects match current filters
                    </td>
                  </tr>
                ) : (
                  filteredProspects.map((p) => {
                    const stageStyle = STAGE_COLORS[p.sales_stage] || STAGE_COLORS.NEW;
                    return (
                      <tr key={p.id} className="hover:bg-gray-50 transition cursor-pointer" onClick={() => openProspectDetail(p.id)}>
                        <td className="px-6 py-4">
                          <div className="font-semibold text-gray-900">{p.company_name || p.canonical_domain}</div>
                          <div className="text-xs text-gray-500">{p.canonical_domain || "—"}</div>
                          {p.industry && <div className="text-xs text-gray-400 mt-0.5">{p.industry}</div>}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${stageStyle.bg} ${stageStyle.text} ${stageStyle.border}`}>
                            {p.sales_stage.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {p.opportunity_score != null ? (
                            <span className="font-semibold text-emerald-700">{Math.round(p.opportunity_score)}/100</span>
                          ) : (
                            <span className="text-gray-400 text-xs">Unscored</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {p.total_deals > 0 ? (
                            <div>
                              <div className="font-medium text-gray-900">${p.open_deal_value.toLocaleString()}</div>
                              <div className="text-xs text-gray-500">{p.total_deals} deal(s)</div>
                            </div>
                          ) : (
                            <span className="text-gray-400 text-xs">None</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {p.pending_tasks_count > 0 ? (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-amber-50 text-amber-800 rounded">
                              {p.pending_tasks_count} pending
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs">0</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs text-gray-600">
                          {p.verified_contacts_count > 0 ? `${p.verified_contacts_count} verified` : "None verified"}
                        </td>
                        <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => openProspectDetail(p.id)}
                            className="text-xs font-medium text-blue-600 hover:text-blue-800"
                          >
                            Dossier →
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. DEALS & REVENUE VIEW */}
      {activeView === "deals" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500 font-medium">Filter Outcome:</span>
              <select
                value={dealOutcomeFilter}
                onChange={(e) => setDealOutcomeFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
              >
                <option value="ALL">All Deals</option>
                <option value="OPEN">Open Deals</option>
                <option value="WON">Won Deals</option>
                <option value="LOST">Lost Deals</option>
              </select>
            </div>
            <button
              onClick={() => {
                if (companies.length > 0) {
                  setDealForm(prev => ({ ...prev, company_id: companies[0].id }));
                }
                setDealModalOpen(true);
              }}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              New Deal
            </button>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Deal Name</th>
                  <th className="px-6 py-3">Service Category</th>
                  <th className="px-6 py-3">Stage</th>
                  <th className="px-6 py-3">Estimated Value</th>
                  <th className="px-6 py-3">Closed Revenue</th>
                  <th className="px-6 py-3">Outcome</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {filteredDeals.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-400 text-sm">
                      No deals recorded. Click "New Deal" to associate a sales opportunity with a company.
                    </td>
                  </tr>
                ) : (
                  filteredDeals.map((d) => (
                    <tr key={d.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 font-semibold text-gray-900">{d.deal_name}</td>
                      <td className="px-6 py-4 text-xs text-gray-600">{d.service_category.replace("_", " ")}</td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-700">{d.stage}</td>
                      <td className="px-6 py-4 text-gray-900 font-semibold">${d.estimated_value.toLocaleString()} {d.currency}</td>
                      <td className="px-6 py-4 text-emerald-800 font-semibold">
                        {d.closed_amount != null ? `$${d.closed_amount.toLocaleString()} ${d.currency}` : "—"}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 text-xs font-bold rounded ${
                          d.outcome === "WON" ? "bg-emerald-100 text-emerald-800" :
                          d.outcome === "LOST" ? "bg-rose-100 text-rose-800" :
                          "bg-blue-50 text-blue-800"
                        }`}>
                          {d.outcome || "OPEN"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button
                          onClick={() => {
                            setEditDeal(d);
                            setDealOutcome(d.outcome || "OPEN");
                            setDealClosedAmount(d.closed_amount || d.estimated_value);
                            setDealReasonText(d.win_reason || d.loss_reason || "");
                          }}
                          className="text-xs font-medium text-blue-600 hover:text-blue-800"
                        >
                          Manage Outcome →
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. TASKS & FOLLOW-UPS VIEW */}
      {activeView === "tasks" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500 font-medium">Status:</span>
                <select
                  value={taskStatusFilter}
                  onChange={(e) => setTaskStatusFilter(e.target.value)}
                  className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="PENDING">Pending</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>

              <label className="flex items-center space-x-1.5 text-xs text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={taskOverdueOnly}
                  onChange={(e) => setTaskOverdueOnly(e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span>Overdue Only</span>
              </label>
            </div>

            <button
              onClick={() => {
                if (companies.length > 0) {
                  setTaskForm(prev => ({ ...prev, company_id: companies[0].id }));
                }
                setTaskModalOpen(true);
              }}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              New Task
            </button>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Task Title</th>
                  <th className="px-6 py-3">Type</th>
                  <th className="px-6 py-3">Priority</th>
                  <th className="px-6 py-3">Due Date</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {filteredTasks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400 text-sm">
                      No tasks found. Use "New Task" to create follow-up reminders.
                    </td>
                  </tr>
                ) : (
                  filteredTasks.map((t) => {
                    const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== "COMPLETED";
                    return (
                      <tr key={t.id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-gray-900">{t.title}</div>
                          {t.description && <div className="text-xs text-gray-500">{t.description}</div>}
                        </td>
                        <td className="px-6 py-4 text-xs text-gray-600">{t.task_type.replace("_", " ")}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-bold rounded ${
                            t.priority === "URGENT" ? "bg-rose-100 text-rose-800" :
                            t.priority === "HIGH" ? "bg-amber-100 text-amber-800" :
                            t.priority === "MEDIUM" ? "bg-blue-50 text-blue-800" :
                            "bg-gray-100 text-gray-700"
                          }`}>
                            {t.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs">
                          {t.due_date ? (
                            <span className={isOverdue ? "font-bold text-rose-600 flex items-center" : "text-gray-700"}>
                              {isOverdue && <AlertTriangle className="w-3.5 h-3.5 mr-1" />}
                              {new Date(t.due_date).toLocaleDateString()}
                            </span>
                          ) : (
                            <span className="text-gray-400">No due date</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-bold rounded ${
                            t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" :
                            t.status === "IN_PROGRESS" ? "bg-blue-100 text-blue-800" :
                            "bg-gray-100 text-gray-700"
                          }`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {t.status !== "COMPLETED" && (
                            <button
                              onClick={() => setCompleteTaskData({ id: t.id, title: t.title })}
                              className="text-xs font-semibold text-emerald-600 hover:text-emerald-800 inline-flex items-center"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                              Mark Complete
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. CONVERSION REPORTS VIEW */}
      {activeView === "reports" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-6 shadow-xs">
            <div>
              <h3 className="text-base font-bold text-gray-900">Sales Conversion Funnel</h3>
              <p className="text-xs text-gray-500">
                Honest transition rates calculated against real database records. Zero activity indicates unconfigured integration or pending outreach.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase">Qualified → Contacted</div>
                <div className="text-xl font-bold text-blue-700 mt-1">
                  {metrics?.conversion_rates?.["QUALIFIED_TO_CONTACTED"] != null ? `${metrics.conversion_rates["QUALIFIED_TO_CONTACTED"]}%` : "—"}
                </div>
                <div className="text-xs text-gray-400 mt-1">Provider-verified sends</div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase">Contacted → Replied</div>
                <div className="text-xl font-bold text-indigo-700 mt-1">
                  {metrics?.conversion_rates?.["CONTACTED_TO_REPLIED"] != null ? `${metrics.conversion_rates["CONTACTED_TO_REPLIED"]}%` : "—"}
                </div>
                <div className="text-xs text-gray-400 mt-1">Inbound verified replies</div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase">Replied → Meeting</div>
                <div className="text-xl font-bold text-purple-700 mt-1">
                  {metrics?.conversion_rates?.["REPLIED_TO_MEETING"] != null ? `${metrics.conversion_rates["REPLIED_TO_MEETING"]}%` : "—"}
                </div>
                <div className="text-xs text-gray-400 mt-1">Scheduled calls/demos</div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-xs font-semibold text-gray-500 uppercase">Overall Win Rate</div>
                <div className="text-xl font-bold text-emerald-700 mt-1">
                  {metrics?.conversion_rates?.["WON_RATE"] != null ? `${metrics.conversion_rates["WON_RATE"]}%` : "—"}
                </div>
                <div className="text-xs text-gray-400 mt-1">Won deals / Total closed</div>
              </div>
            </div>

            {metrics?.notes && metrics.notes.length > 0 && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5 text-xs text-slate-600">
                <div className="font-semibold text-slate-800">Data Integrity Notice:</div>
                {metrics.notes.map((note, idx) => (
                  <div key={idx} className="flex items-start space-x-1.5">
                    <span className="text-slate-400">•</span>
                    <span>{note}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* UNIFIED PROSPECT DETAIL DRAWER / MODAL */}
      {selectedProspectId && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 flex justify-end">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col">
            {/* Drawer Header */}
            <div className="p-6 border-b border-gray-200 flex items-start justify-between bg-gray-50">
              <div>
                <div className="flex items-center space-x-3">
                  <h2 className="text-xl font-bold text-gray-900">
                    {prospectDetail?.company?.name || prospectDetail?.company?.company_name || "Company Dossier"}
                  </h2>
                  {prospectDetail && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                      STAGE_COLORS[prospectDetail.sales_stage]?.bg || "bg-gray-100"
                    } ${STAGE_COLORS[prospectDetail.sales_stage]?.text || "text-gray-800"}`}>
                      {prospectDetail.sales_stage.replace("_", " ")}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {prospectDetail?.company?.normalized_domain || prospectDetail?.company?.canonical_domain || "No domain specified"}
                </p>
              </div>

              <button
                onClick={() => {
                  setSelectedProspectId(null);
                  setProspectDetail(null);
                }}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 flex-1 overflow-y-auto space-y-6">
              {detailLoading ? (
                <div className="py-24 text-center text-gray-400 flex flex-col items-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mb-2" />
                  <span>Loading unified prospect records...</span>
                </div>
              ) : prospectDetail ? (
                <>
                  {/* Quick Action Bar */}
                  <div className="flex items-center space-x-2 pb-4 border-b border-gray-100">
                    <button
                      onClick={() => {
                        setStageModalData({
                          companyId: prospectDetail.company.id,
                          companyName: prospectDetail.company.name || "Prospect",
                          currentStage: prospectDetail.sales_stage,
                          targetStage: prospectDetail.sales_stage
                        });
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-100"
                    >
                      Update Stage
                    </button>
                    <button
                      onClick={() => {
                        setDealForm(prev => ({ ...prev, company_id: prospectDetail.company.id }));
                        setDealModalOpen(true);
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-gray-50 text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100"
                    >
                      + Deal
                    </button>
                    <button
                      onClick={() => {
                        setTaskForm(prev => ({ ...prev, company_id: prospectDetail.company.id }));
                        setTaskModalOpen(true);
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-gray-50 text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100"
                    >
                      + Task
                    </button>
                  </div>

                  {/* 1. Opportunity & Website Signals */}
                  <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">SEO Opportunity & Technical Health</h4>
                      {prospectDetail.opportunity_profile?.opportunity_score != null && (
                        <span className="text-xs font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">
                          Score: {Math.round(prospectDetail.opportunity_profile.opportunity_score)}/100
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-gray-400">Priority Tier:</span>{" "}
                        <span className="font-semibold text-gray-800">
                          {prospectDetail.opportunity_profile?.priority_tier || "Unassigned"}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Recommended Service:</span>{" "}
                        <span className="font-semibold text-gray-800">
                          {prospectDetail.opportunity_profile?.recommended_service || "None"}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">CMS Detected:</span>{" "}
                        <span className="font-semibold text-gray-800">
                          {prospectDetail.website_scan?.cms_detected || "Unknown"}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">HTTP Status:</span>{" "}
                        <span className="font-semibold text-gray-800">
                          {prospectDetail.website_scan?.http_status || "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Google Drive & Outreach Channels Card */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <HardDrive className="w-3.5 h-3.5 text-blue-600" /> Google Drive & Outreach Channels
                      </h4>
                      {prospectDetail.company?.gdrive_sync_status && (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          prospectDetail.company.gdrive_sync_status === "SYNCED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                        }`}>
                          Drive: {prospectDetail.company.gdrive_sync_status}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      {prospectDetail.company?.gdrive_file_url && (
                        <div className="sm:col-span-2">
                          <a
                            href={prospectDetail.company.gdrive_file_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center text-blue-600 hover:underline font-semibold"
                          >
                            <HardDrive className="w-3.5 h-3.5 mr-1" /> View Google Drive Record <ExternalLink className="w-3 h-3 ml-1" />
                          </a>
                        </div>
                      )}

                      {prospectDetail.company?.whatsapp_number && (
                        <div>
                          <span className="text-slate-400">WhatsApp:</span>{" "}
                          <span className="font-mono text-slate-800">{prospectDetail.company.whatsapp_number}</span>
                          {prospectDetail.company?.whatsapp_click_url && (
                            <a
                              href={prospectDetail.company.whatsapp_click_url}
                              target="_blank"
                              rel="noreferrer"
                              className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-600 text-white hover:bg-emerald-700"
                            >
                              <PhoneCall className="w-2.5 h-2.5 mr-1" /> wa.me
                            </a>
                          )}
                        </div>
                      )}

                      {prospectDetail.company?.phone_number && !prospectDetail.company?.whatsapp_number && (
                        <div>
                          <span className="text-slate-400">Phone:</span>{" "}
                          <span className="font-mono text-slate-800">{prospectDetail.company.phone_number}</span>
                        </div>
                      )}

                      {prospectDetail.company?.facebook_url && (
                        <div>
                          <a
                            href={prospectDetail.company.facebook_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center text-blue-600 hover:underline"
                          >
                            <FacebookIcon className="w-3 h-3 mr-1" /> Facebook Page <ExternalLink className="w-2.5 h-2.5 ml-1" />
                          </a>
                        </div>
                      )}

                      {prospectDetail.company?.instagram_url && (
                        <div>
                          <a
                            href={prospectDetail.company.instagram_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center text-pink-600 hover:underline"
                          >
                            <InstagramIcon className="w-3 h-3 mr-1" /> Instagram Profile <ExternalLink className="w-2.5 h-2.5 ml-1" />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 2. Associated Verified Contacts */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Associated Contacts ({prospectDetail.contacts.length})</h4>
                    </div>
                    {prospectDetail.contacts.length === 0 ? (
                      <div className="p-3 bg-gray-50 rounded-lg text-xs text-gray-400 text-center">
                        No contacts discovered yet
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {prospectDetail.contacts.map((c) => (
                          <div key={c.id} className="p-3 bg-white border border-gray-200 rounded-lg flex items-center justify-between text-xs">
                            <div>
                              <div className="font-semibold text-gray-900">{c.name || "Unnamed Contact"}</div>
                              <div className="text-gray-500">{c.email}</div>
                              {c.job_title && <div className="text-gray-400">{c.job_title}</div>}
                            </div>
                            <span className={`px-2 py-0.5 rounded font-bold ${
                              c.verification_status === "VERIFIED" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" :
                              "bg-gray-100 text-gray-600"
                            }`}>
                              {c.verification_status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 3. Outreach & Messages History */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Outreach Messages ({prospectDetail.outreach_messages.length})</h4>
                    {prospectDetail.outreach_messages.length === 0 ? (
                      <div className="p-3 bg-gray-50 rounded-lg text-xs text-gray-400 text-center">
                        No messages sent yet. Contacted status requires confirmed provider delivery.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {prospectDetail.outreach_messages.map((m) => (
                          <div key={m.id} className="p-3 bg-blue-50/50 border border-blue-200 rounded-lg text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-blue-900">{m.subject_line}</span>
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-200 text-blue-800">
                                {m.status}
                              </span>
                            </div>
                            <div className="text-gray-600">To: {m.recipient_email} via {m.provider}</div>
                            <div className="text-gray-400 text-[10px]">Sent: {new Date(m.sent_at).toLocaleString()}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 4. Deals & Revenue */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Deals ({prospectDetail.deals.length})</h4>
                    {prospectDetail.deals.length === 0 ? (
                      <div className="p-3 bg-gray-50 rounded-lg text-xs text-gray-400 text-center">
                        No deals associated with this prospect
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {prospectDetail.deals.map((d) => (
                          <div key={d.id} className="p-3 bg-white border border-gray-200 rounded-lg flex items-center justify-between text-xs">
                            <div>
                              <div className="font-semibold text-gray-900">{d.deal_name}</div>
                              <div className="text-gray-500">{d.service_category} • {d.stage}</div>
                            </div>
                            <div className="text-right">
                              <div className="font-bold text-gray-900">${d.estimated_value.toLocaleString()}</div>
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                d.outcome === "WON" ? "bg-emerald-100 text-emerald-800" :
                                d.outcome === "LOST" ? "bg-rose-100 text-rose-800" :
                                "bg-gray-100 text-gray-700"
                              }`}>
                                {d.outcome || "OPEN"}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 5. Tasks */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Tasks & Follow-ups ({prospectDetail.tasks.length})</h4>
                    {prospectDetail.tasks.length === 0 ? (
                      <div className="p-3 bg-gray-50 rounded-lg text-xs text-gray-400 text-center">
                        No open tasks for this prospect
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {prospectDetail.tasks.map((t) => (
                          <div key={t.id} className="p-3 bg-white border border-gray-200 rounded-lg flex items-center justify-between text-xs">
                            <div>
                              <div className="font-semibold text-gray-900">{t.title}</div>
                              <div className="text-gray-500">{t.task_type} • Due: {t.due_date ? new Date(t.due_date).toLocaleDateString() : 'None'}</div>
                            </div>
                            <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                              t.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                            }`}>
                              {t.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 6. Internal Notes */}
                  <div className="space-y-3 pt-2 border-t border-gray-200">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Internal Notes</h4>
                    <form onSubmit={handleAddNote} className="space-y-2">
                      <textarea
                        value={newNoteText}
                        onChange={(e) => setNewNoteText(e.target.value)}
                        placeholder="Add private sales notes, negotiation context, or feedback..."
                        rows={2}
                        className="w-full text-xs p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={actionLoading || !newNoteText.trim()}
                          className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                          Add Note
                        </button>
                      </div>
                    </form>

                    <div className="space-y-2">
                      {prospectDetail.notes.map((n) => (
                        <div key={n.id} className="p-3 bg-yellow-50/60 border border-yellow-200 rounded-lg text-xs space-y-1">
                          <div className="flex items-center justify-between text-gray-500 text-[10px]">
                            <span>Author: {n.author}</span>
                            <span>{new Date(n.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-gray-800 whitespace-pre-wrap">{n.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 7. Activity Audit Timeline */}
                  <div className="space-y-3 pt-2 border-t border-gray-200">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Activity Audit Timeline</h4>
                    <div className="space-y-2 border-l-2 border-gray-200 pl-3">
                      {prospectDetail.activities.map((a) => (
                        <div key={a.id} className="text-xs space-y-0.5">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-gray-800">{a.title}</span>
                            <span className="text-[10px] text-gray-400">({a.actor})</span>
                          </div>
                          <div className="text-[10px] text-gray-400">{new Date(a.created_at).toLocaleString()}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: STAGE TRANSITION */}
      {stageModalData && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Change Sales Stage</h3>
              <button onClick={() => setStageModalData(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleStageUpdate} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Company</label>
                <div className="text-gray-900 font-medium">{stageModalData.companyName}</div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Current Stage</label>
                <div className="text-gray-600">{stageModalData.currentStage.replace("_", " ")}</div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">New Target Stage</label>
                <select
                  value={stageModalData.targetStage}
                  onChange={(e) => setStageModalData(prev => prev ? { ...prev, targetStage: e.target.value } : null)}
                  className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                >
                  {STAGE_ORDER.map(s => (
                    <option key={s} value={s}>{s.replace("_", " ")}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Reason for Transition (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Completed initial discovery call, proposal requested"
                  value={stageReason}
                  onChange={(e) => setStageReason(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Qualification Notes (Optional)</label>
                <textarea
                  placeholder="Key observations or criteria met..."
                  value={stageNotes}
                  onChange={(e) => setStageNotes(e.target.value)}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setStageModalData(null)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Confirm Transition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE DEAL */}
      {dealModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Create New Deal</h3>
              <button onClick={() => setDealModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateDeal} className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Company *</label>
                <select
                  value={dealForm.company_id}
                  onChange={(e) => setDealForm(prev => ({ ...prev, company_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                  required
                >
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.company_name || c.name || c.normalized_domain}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Deal Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Q4 SEO Growth & Link Building"
                  value={dealForm.deal_name}
                  onChange={(e) => setDealForm(prev => ({ ...prev, deal_name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Service Category</label>
                  <select
                    value={dealForm.service_category}
                    onChange={(e) => setDealForm(prev => ({ ...prev, service_category: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg p-2"
                  >
                    <option value="TECHNICAL_SEO">Technical SEO</option>
                    <option value="LINK_BUILDING">Link Building</option>
                    <option value="CONTENT_STRATEGY">Content Strategy</option>
                    <option value="DIGITAL_PR">Digital PR</option>
                    <option value="FULL_SERVICE">Full Service</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Estimated Value ($)</label>
                  <input
                    type="number"
                    value={dealForm.estimated_value}
                    onChange={(e) => setDealForm(prev => ({ ...prev, estimated_value: Number(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-lg p-2"
                    min="0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Expected Close Date</label>
                <input
                  type="date"
                  value={dealForm.expected_close_date}
                  onChange={(e) => setDealForm(prev => ({ ...prev, expected_close_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Notes</label>
                <textarea
                  value={dealForm.notes}
                  onChange={(e) => setDealForm(prev => ({ ...prev, notes: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setDealModalOpen(false)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Create Deal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT DEAL / OUTCOME */}
      {editDeal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Manage Deal: {editDeal.deal_name}</h3>
              <button onClick={() => setEditDeal(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateDeal} className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Outcome Status</label>
                <select
                  value={dealOutcome}
                  onChange={(e) => setDealOutcome(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2"
                >
                  <option value="OPEN">Open (In Progress)</option>
                  <option value="WON">Closed Won</option>
                  <option value="LOST">Closed Lost</option>
                </select>
              </div>

              {dealOutcome === "WON" && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Actual Closed Revenue Amount ($) *</label>
                  <input
                    type="number"
                    value={dealClosedAmount}
                    onChange={(e) => setDealClosedAmount(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-lg p-2 font-semibold text-emerald-800"
                    required
                  />
                  <p className="text-[11px] text-gray-500 mt-0.5">
                    Authorized actual revenue earned. Clearly recorded in closed metrics.
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {dealOutcome === "WON" ? "Win Reason" : dealOutcome === "LOST" ? "Loss Reason" : "Update Reason"}
                </label>
                <input
                  type="text"
                  placeholder="e.g. Budget approved, superior technical audit evidence"
                  value={dealReasonText}
                  onChange={(e) => setDealReasonText(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setEditDeal(null)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Save Deal Outcome
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE TASK */}
      {taskModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Create Follow-up Task</h3>
              <button onClick={() => setTaskModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Company *</label>
                <select
                  value={taskForm.company_id}
                  onChange={(e) => setTaskForm(prev => ({ ...prev, company_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                  required
                >
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.company_name || c.name || c.normalized_domain}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Task Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Schedule SEO audit walk-through"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Type</label>
                  <select
                    value={taskForm.task_type}
                    onChange={(e) => setTaskForm(prev => ({ ...prev, task_type: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg p-2"
                  >
                    <option value="CALL">Call</option>
                    <option value="MEETING">Meeting</option>
                    <option value="RESEARCH">Research</option>
                    <option value="FOLLOW_UP">Follow Up</option>
                    <option value="EMAIL">Email</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Priority</label>
                  <select
                    value={taskForm.priority}
                    onChange={(e) => setTaskForm(prev => ({ ...prev, priority: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg p-2"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={taskForm.due_date}
                  onChange={(e) => setTaskForm(prev => ({ ...prev, due_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Description / Notes</label>
                <textarea
                  value={taskForm.description}
                  onChange={(e) => setTaskForm(prev => ({ ...prev, description: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setTaskModalOpen(false)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: COMPLETE TASK */}
      {completeTaskData && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-gray-900">Complete Task</h3>
              <button onClick={() => setCompleteTaskData(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCompleteTask} className="space-y-3 text-sm">
              <p className="text-gray-700 font-medium">{completeTaskData.title}</p>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Completion Notes</label>
                <textarea
                  placeholder="Record call outcome, agreed action items, or meeting notes..."
                  value={taskCompletionNotes}
                  onChange={(e) => setTaskCompletionNotes(e.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setCompleteTaskData(null)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                >
                  Confirm Completion
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
