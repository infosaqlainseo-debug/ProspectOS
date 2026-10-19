"use client";

import { useEffect, useState, useMemo } from "react";
import {
  getRevenueSummary,
  getServiceRevenue,
  getClientRevenue,
  getCampaignROI,
  getFunnelAnalysis,
  getRevenueTrends,
  getRevenueDealsDrilldown,
  createAnalyticsSnapshot,
  getAnalyticsSnapshots,
  RevenueSummary,
  ServiceRevenueBreakdown,
  ClientRevenueBreakdown,
  CampaignROIBreakdown,
  FunnelAnalysis,
  RevenueTrendItem,
  RevenueDrilldownResponse,
  SnapshotResponse
} from "@/lib/api";
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  PieChart,
  Calendar,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  Info,
  ShieldAlert,
  Archive,
  Download,
  Building,
  Target,
  FileSpreadsheet,
  ChevronRight,
  HelpCircle,
  Percent,
  CreditCard,
  Receipt
} from "lucide-react";

export default function RevenueAnalyticsPage() {
  // Global Filter State
  const [periodType, setPeriodType] = useState<string>("ALL_TIME");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [serviceCategory, setServiceCategory] = useState<string>("ALL");
  const [currencyFilter, setCurrencyFilter] = useState<string>("ALL");

  // Tab State
  const [activeTab, setActiveTab] = useState<"overview" | "funnel" | "services_clients" | "campaigns" | "drilldown" | "snapshots">("overview");

  // Data States
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const [summary, setSummary] = useState<RevenueSummary | null>(null);
  const [services, setServices] = useState<ServiceRevenueBreakdown[]>([]);
  const [clients, setClients] = useState<ClientRevenueBreakdown[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignROIBreakdown[]>([]);
  const [funnel, setFunnel] = useState<FunnelAnalysis | null>(null);
  const [trends, setTrends] = useState<RevenueTrendItem[]>([]);
  const [drilldownData, setDrilldownData] = useState<RevenueDrilldownResponse | null>(null);
  const [drilldownPage, setDrilldownPage] = useState<number>(1);
  const [drilldownStage, setDrilldownStage] = useState<string>("ALL");
  const [drilldownOutcome, setDrilldownOutcome] = useState<string>("ALL");
  const [snapshots, setSnapshots] = useState<SnapshotResponse[]>([]);

  // Snapshot modal
  const [showSnapshotModal, setShowSnapshotModal] = useState<boolean>(false);
  const [snapshotAuthor, setSnapshotAuthor] = useState<string>("finance_reviewer");
  const [snapshotLoading, setSnapshotLoading] = useState<boolean>(false);

  // Compute filter params dictionary
  const filterParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = new Date(startDate).toISOString();
    if (endDate) params.end_date = new Date(endDate).toISOString();
    if (serviceCategory !== "ALL") params.service_category = serviceCategory;
    if (currencyFilter !== "ALL") params.currency = currencyFilter;
    return params;
  }, [startDate, endDate, serviceCategory, currencyFilter]);

  // Handle preset period changes
  const handlePeriodChange = (val: string) => {
    setPeriodType(val);
    const now = new Date();
    if (val === "ALL_TIME") {
      setStartDate("");
      setEndDate("");
    } else if (val === "30D") {
      const past = new Date();
      past.setDate(now.getDate() - 30);
      setStartDate(past.toISOString().split("T")[0]);
      setEndDate(now.toISOString().split("T")[0]);
    } else if (val === "90D") {
      const past = new Date();
      past.setDate(now.getDate() - 90);
      setStartDate(past.toISOString().split("T")[0]);
      setEndDate(now.toISOString().split("T")[0]);
    } else if (val === "180D") {
      const past = new Date();
      past.setDate(now.getDate() - 180);
      setStartDate(past.toISOString().split("T")[0]);
      setEndDate(now.toISOString().split("T")[0]);
    } else if (val === "YTD") {
      const yearStart = new Date(now.getFullYear(), 0, 1);
      setStartDate(yearStart.toISOString().split("T")[0]);
      setEndDate(now.toISOString().split("T")[0]);
    }
  };

  // Main fetch function
  const fetchAnalyticsData = async (isRefresh: boolean = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [sumRes, srvRes, cliRes, campRes, fnlRes, trdRes, ddRes, snapRes] = await Promise.all([
        getRevenueSummary(filterParams),
        getServiceRevenue(filterParams),
        getClientRevenue(filterParams),
        getCampaignROI(filterParams),
        getFunnelAnalysis(filterParams),
        getRevenueTrends(filterParams),
        getRevenueDealsDrilldown({
          ...filterParams,
          page: String(drilldownPage),
          page_size: "25",
          ...(drilldownStage !== "ALL" ? { stage: drilldownStage } : {}),
          ...(drilldownOutcome !== "ALL" ? { outcome: drilldownOutcome } : {})
        }),
        getAnalyticsSnapshots(15)
      ]);

      setSummary(sumRes);
      setServices(srvRes);
      setClients(cliRes);
      setCampaigns(campRes);
      setFunnel(fnlRes);
      setTrends(trdRes);
      setDrilldownData(ddRes);
      setSnapshots(snapRes);
    } catch (err: any) {
      console.error("Failed to load revenue analytics:", err);
      setError(err.message || "Failed to load revenue analytics records.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [filterParams, drilldownPage, drilldownStage, drilldownOutcome]);

  const handleCreateSnapshot = async () => {
    setSnapshotLoading(true);
    try {
      const newSnap = await createAnalyticsSnapshot({
        period_type: periodType,
        period_start: startDate ? new Date(startDate).toISOString() : undefined,
        period_end: endDate ? new Date(endDate).toISOString() : undefined,
        created_by: snapshotAuthor
      });
      setSnapshots(prev => [newSnap, ...prev]);
      setShowSnapshotModal(false);
      setNotification({
        type: "success",
        message: `Persistent analytics snapshot created successfully (ID: ${newSnap.id.substring(0, 8)}).`
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: `Snapshot creation failed: ${err.message || "Unknown error"}`
      });
    } finally {
      setSnapshotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Header Banner */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                  Phase 3.2
                </span>
                <span className="text-xs font-medium text-gray-500">Persistent Intelligence</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mt-1 flex items-center gap-2">
                <BarChart3 className="w-7 h-7 text-emerald-600" />
                Revenue & Performance Analytics
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Audited CRM revenue realization, separated open pipeline valuation, profitability, and bottleneck analytics.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => fetchAnalyticsData(true)}
                disabled={loading || refreshing}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin text-emerald-600" : ""}`} />
                {refreshing ? "Refreshing..." : "Refresh"}
              </button>
              <button
                onClick={() => setShowSnapshotModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-emerald-600 hover:bg-emerald-700"
              >
                <Archive className="w-4 h-4 mr-2" />
                Capture Snapshot
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="mt-6 pt-4 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Period Preset</label>
              <select
                value={periodType}
                onChange={(e) => handlePeriodChange(e.target.value)}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              >
                <option value="ALL_TIME">All Time</option>
                <option value="30D">Last 30 Days</option>
                <option value="90D">Last 90 Days</option>
                <option value="180D">Last 180 Days</option>
                <option value="YTD">Year to Date (YTD)</option>
                <option value="CUSTOM">Custom Range</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setPeriodType("CUSTOM");
                }}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setPeriodType("CUSTOM");
                }}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Service Category</label>
              <select
                value={serviceCategory}
                onChange={(e) => setServiceCategory(e.target.value)}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              >
                <option value="ALL">All Services</option>
                <option value="TECHNICAL_SEO">Technical SEO</option>
                <option value="LINK_BUILDING">Link Building</option>
                <option value="CONTENT_STRATEGY">Content Strategy</option>
                <option value="DIGITAL_PR">Digital PR</option>
                <option value="FULL_SERVICE">Full Service</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Native Currency</label>
              <select
                value={currencyFilter}
                onChange={(e) => setCurrencyFilter(e.target.value)}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              >
                <option value="ALL">All Currencies (USD Normalized)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="CAD">CAD ($)</option>
                <option value="AUD">AUD ($)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Notification Banner */}
        {notification && (
          <div className={`mb-6 p-4 rounded-md flex items-center justify-between ${
            notification.type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" :
            notification.type === "error" ? "bg-red-50 text-red-800 border border-red-200" :
            "bg-blue-50 text-blue-800 border border-blue-200"
          }`}>
            <div className="flex items-center gap-2">
              {notification.type === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
              {notification.type === "error" && <AlertTriangle className="w-5 h-5 text-red-600" />}
              {notification.type === "info" && <Info className="w-5 h-5 text-blue-600" />}
              <span className="text-sm font-medium">{notification.message}</span>
            </div>
            <button onClick={() => setNotification(null)} className="text-gray-400 hover:text-gray-600 text-sm">
              Dismiss
            </button>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-6 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-800">Analytics Query Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Executive KPI Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
            {/* Realized Won Revenue */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Realized Revenue</span>
                <span className="p-2 rounded-full bg-emerald-50 text-emerald-600">
                  <DollarSign className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  ${summary.total_realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-xs text-emerald-700 font-medium mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Closed-Won Realized ({summary.deal_count_won} deals)
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Net Revenue (After Adj.):</span>
                  <span className="font-semibold text-gray-800">
                    ${summary.net_realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                {(summary.total_discounts > 0 || summary.total_taxes > 0 || summary.total_refunds > 0) && (
                  <div className="text-[11px] text-gray-400">
                    Discounts: -${summary.total_discounts.toFixed(2)} | Refunds: -${summary.total_refunds.toFixed(2)}
                  </div>
                )}
              </div>
            </div>

            {/* Open Pipeline Value (Strict Separation) */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Open Pipeline Value</span>
                <span className="p-2 rounded-full bg-blue-50 text-blue-600">
                  <TrendingUp className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  ${summary.total_open_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-xs text-blue-700 font-medium mt-1 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  Active Unearned ({summary.deal_count_open} open deals)
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
                <span>Weighted Pipeline:</span>
                <span className="font-semibold text-blue-800">
                  ${summary.weighted_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Win Rate & Performance */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Conversion & Win Rate</span>
                <span className="p-2 rounded-full bg-purple-50 text-purple-600">
                  <Percent className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  {summary.win_rate_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-purple-700 font-medium mt-1">
                  {summary.deal_count_won} Won / {summary.deal_count_lost} Lost (of {summary.deal_count_won + summary.deal_count_lost} closed)
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
                <span>Total Tracked Deals:</span>
                <span className="font-semibold text-gray-800">{summary.deal_count_total}</span>
              </div>
            </div>

            {/* Average Deal Size & Sales Cycle */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Deal Velocity & Size</span>
                <span className="p-2 rounded-full bg-amber-50 text-amber-600">
                  <Clock className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  {summary.average_deal_size_won != null
                    ? `$${summary.average_deal_size_won.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                    : "—"}
                </div>
                <div className="text-xs text-amber-700 font-medium mt-1">
                  Average Closed-Won Deal Size
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
                <span>Avg. Sales Cycle Duration:</span>
                <span className="font-semibold text-gray-800">
                  {summary.average_sales_cycle_days != null ? `${summary.average_sales_cycle_days} days` : "Unknown (missing close dates)"}
                </span>
              </div>
            </div>

            {/* Profitability & Margins (Zero Fabrication) */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Profitability & Margin</span>
                <span className="p-2 rounded-full bg-teal-50 text-teal-600">
                  <PieChart className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  {summary.gross_margin_pct != null ? `${summary.gross_margin_pct.toFixed(1)}%` : "N/A"}
                </div>
                <div className="text-xs text-teal-700 font-medium mt-1">
                  {summary.gross_profit != null
                    ? `Gross Profit: $${summary.gross_profit.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                    : "Costs Not Recorded"}
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
                <span>Verified Cost Coverage:</span>
                <span className={`font-semibold ${summary.cost_coverage_pct > 0 ? "text-emerald-700" : "text-amber-700"}`}>
                  {summary.cost_coverage_pct.toFixed(1)}% of won deals
                </span>
              </div>
            </div>

            {/* Invoicing & Collections */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Invoicing & Receivables</span>
                <span className="p-2 rounded-full bg-indigo-50 text-indigo-600">
                  <Receipt className="w-5 h-5" />
                </span>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-extrabold text-gray-900">
                  {summary.total_invoiced_amount != null
                    ? `$${summary.total_invoiced_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                    : "Uninvoiced"}
                </div>
                <div className="text-xs text-indigo-700 font-medium mt-1">
                  {summary.total_paid_amount != null
                    ? `Paid: $${summary.total_paid_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                    : "No payment records"}
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between">
                <span>Outstanding Balance:</span>
                <span className="font-semibold text-gray-800">
                  {summary.total_outstanding_amount != null ? `$${summary.total_outstanding_amount.toFixed(2)}` : "—"}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Data Limitations & Disclosures */}
        {summary && summary.data_limitations && summary.data_limitations.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                  Audit Disclosures & Data Integrity Safeguards
                </h4>
                <ul className="mt-1 space-y-1 text-xs text-amber-800">
                  {summary.data_limitations.map((lim, idx) => (
                    <li key={idx} className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-600 flex-shrink-0"></span>
                      <span>{lim}</span>
                    </li>
                  ))}
                  <li className="flex items-center gap-1.5 text-amber-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600 flex-shrink-0"></span>
                    <span>Exchange rate baseline: USD normalization via ECB benchmark reference table.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6 bg-white rounded-t-lg shadow-sm px-4">
          <nav className="flex space-x-6 overflow-x-auto" aria-label="Tabs">
            {[
              { id: "overview", label: "Trends & Currency", icon: TrendingUp },
              { id: "funnel", label: "Funnel & Bottlenecks", icon: Layers },
              { id: "services_clients", label: "Services & Clients", icon: Building },
              { id: "campaigns", label: "Campaign ROI", icon: Target },
              { id: "drilldown", label: "Deals Ledger & Audit", icon: FileSpreadsheet },
              { id: "snapshots", label: "Snapshots Archive", icon: Archive },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 whitespace-nowrap transition-colors ${
                    isActive
                      ? "border-emerald-600 text-emerald-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* TAB 1: Trends & Currency */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Historical Monthly Trends */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Historical Revenue Realization & Pipeline Creation</h3>
                  <p className="text-xs text-gray-500">Monthly chronological ledger of closed-won revenue alongside newly originated pipeline.</p>
                </div>
                <span className="text-xs font-medium px-2 py-1 bg-gray-100 text-gray-600 rounded">
                  {trends.length} periods recorded
                </span>
              </div>

              {trends.length === 0 ? (
                <div className="py-12 text-center text-gray-400 text-sm">
                  No historical deal trends found matching selected filters.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-gray-600">
                        <th className="py-3 px-4 text-left font-semibold">Period</th>
                        <th className="py-3 px-4 text-right font-semibold">Realized Won ($)</th>
                        <th className="py-3 px-4 text-center font-semibold">Deals Won</th>
                        <th className="py-3 px-4 text-right font-semibold">Pipeline Originated ($)</th>
                        <th className="py-3 px-4 text-center font-semibold">Deals Originated</th>
                        <th className="py-3 px-4 text-left font-semibold">Realization Ratio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {trends.map((item, idx) => {
                        const maxVal = Math.max(...trends.map(t => Math.max(t.realized_revenue, t.pipeline_created_value)), 1);
                        const revWidth = Math.min(100, Math.round((item.realized_revenue / maxVal) * 100));
                        return (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="py-3 px-4 font-medium text-gray-900">{item.period}</td>
                            <td className="py-3 px-4 text-right font-bold text-emerald-700">
                              ${item.realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3 px-4 text-center font-medium text-gray-700">{item.deals_won}</td>
                            <td className="py-3 px-4 text-right font-medium text-blue-700">
                              ${item.pipeline_created_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3 px-4 text-center text-gray-600">{item.deals_created}</td>
                            <td className="py-3 px-4">
                              <div className="w-32 bg-gray-100 rounded-full h-2 overflow-hidden">
                                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${revWidth}%` }}></div>
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

            {/* Currency Breakdown Cards */}
            {summary && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Native Currency Breakdown — Realized Won</h4>
                  <p className="text-xs text-gray-500 mb-4">Un-normalized source currency totals before benchmark conversion.</p>
                  <div className="space-y-3">
                    {Object.entries(summary.currency_breakdown_realized).map(([curr, amt]) => (
                      <div key={curr} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                        <span className="font-bold text-gray-800">{curr}</span>
                        <div className="text-right">
                          <span className="font-mono text-sm font-semibold text-emerald-700">{amt.toLocaleString("en-US", { minimumFractionDigits: 2 })} {curr}</span>
                          <div className="text-[11px] text-gray-400">
                            Rate: {summary.exchange_rates_used[curr] || 1.0} USD per {curr}
                          </div>
                        </div>
                      </div>
                    ))}
                    {Object.keys(summary.currency_breakdown_realized).length === 0 && (
                      <p className="text-xs text-gray-400">No realized transactions found.</p>
                    )}
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Native Currency Breakdown — Open Pipeline</h4>
                  <p className="text-xs text-gray-500 mb-4">Un-normalized active pipeline amounts currently in negotiation or proposal.</p>
                  <div className="space-y-3">
                    {Object.entries(summary.currency_breakdown_pipeline).map(([curr, amt]) => (
                      <div key={curr} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                        <span className="font-bold text-gray-800">{curr}</span>
                        <div className="text-right">
                          <span className="font-mono text-sm font-semibold text-blue-700">{amt.toLocaleString("en-US", { minimumFractionDigits: 2 })} {curr}</span>
                          <div className="text-[11px] text-gray-400">
                            Rate: {summary.exchange_rates_used[curr] || 1.0} USD per {curr}
                          </div>
                        </div>
                      </div>
                    ))}
                    {Object.keys(summary.currency_breakdown_pipeline).length === 0 && (
                      <p className="text-xs text-gray-400">No open pipeline deals found.</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Funnel & Bottlenecks */}
        {activeTab === "funnel" && funnel && (
          <div className="space-y-6">
            {/* Bottleneck Diagnosis Alert */}
            {funnel.bottleneck_stage && (
              <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-bold text-amber-900">
                      Pipeline Bottleneck Detected: Stage {funnel.bottleneck_stage}
                    </h3>
                    <p className="text-xs text-amber-800 mt-1">
                      {funnel.bottleneck_reason}
                    </p>
                    <p className="text-[11px] text-amber-700 mt-2">
                      Recommendation: Inspect deals stagnating in {funnel.bottleneck_stage}. Refine outreach discovery briefs or proposal pitch decks to increase qualification-to-proposal velocity.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Funnel Table & Metrics */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Sales Funnel Progression & Conversion Rates</h3>
                  <p className="text-xs text-gray-500">
                    Progression flow across sequential sales stages ({funnel.total_deals_analyzed} deals evaluated).
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500 block">Overall Conversion</span>
                  <span className="text-lg font-bold text-emerald-700">{funnel.overall_conversion_rate}%</span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-3 px-4 text-left font-semibold">Stage</th>
                      <th className="py-3 px-4 text-center font-semibold">Deals</th>
                      <th className="py-3 px-4 text-right font-semibold">Total Value ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Prob. Weight</th>
                      <th className="py-3 px-4 text-right font-semibold">Weighted Value ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Conv. Rate to Next</th>
                      <th className="py-3 px-4 text-center font-semibold">Drop-off Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {funnel.stages.map((st, idx) => {
                      const isBottleneck = st.stage === funnel.bottleneck_stage;
                      return (
                        <tr key={idx} className={isBottleneck ? "bg-amber-50/60 font-medium" : "hover:bg-gray-50"}>
                          <td className="py-3 px-4 flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-gray-200 text-gray-700 text-xs flex items-center justify-center font-bold">
                              {st.order}
                            </span>
                            <span className={st.stage === "WON" ? "font-bold text-emerald-700" : st.stage === "LOST" ? "text-red-700 font-medium" : "text-gray-900"}>
                              {st.stage}
                            </span>
                            {isBottleneck && (
                              <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-200 text-amber-800 rounded">
                                Bottleneck
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center font-semibold">{st.deal_count}</td>
                          <td className="py-3 px-4 text-right font-mono font-medium">
                            ${st.total_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 text-center text-xs text-gray-500">
                            {(st.probability_weight * 100).toFixed(0)}%
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-gray-700">
                            ${st.weighted_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 text-center font-semibold">
                            {st.conversion_rate_to_next != null ? (
                              <span className={st.conversion_rate_to_next < 50 ? "text-amber-600" : "text-emerald-600"}>
                                {st.conversion_rate_to_next}%
                              </span>
                            ) : "—"}
                          </td>
                          <td className="py-3 px-4 text-center text-xs text-gray-500">
                            {st.dropoff_rate != null ? `${st.dropoff_rate}%` : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: Services & Clients */}
        {activeTab === "services_clients" && (
          <div className="space-y-6">
            {/* Service Breakdown */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <h3 className="text-base font-semibold text-gray-900 mb-1">Revenue by Service Category</h3>
              <p className="text-xs text-gray-500 mb-4">Segmented closed-won revenue, average deal size, active open pipeline, and fulfillment costs.</p>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-3 px-4 text-left font-semibold">Service</th>
                      <th className="py-3 px-4 text-right font-semibold">Realized Revenue ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Deals Won</th>
                      <th className="py-3 px-4 text-right font-semibold">Avg. Deal Size ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Open Pipeline ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Open Deals</th>
                      <th className="py-3 px-4 text-right font-semibold">Costs ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Margin %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {services.map((srv, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="py-3 px-4 font-semibold text-gray-900">{srv.service_category}</td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-700 font-mono">
                          ${srv.realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center font-medium">{srv.deals_won}</td>
                        <td className="py-3 px-4 text-right font-mono text-gray-700">
                          {srv.average_deal_size != null ? `$${srv.average_deal_size.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "—"}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-blue-700">
                          ${srv.open_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center text-gray-600">{srv.open_deal_count}</td>
                        <td className="py-3 px-4 text-right font-mono text-gray-600">
                          {srv.recorded_costs != null ? `$${srv.recorded_costs.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "N/A"}
                        </td>
                        <td className="py-3 px-4 text-right font-semibold">
                          {srv.gross_margin_pct != null ? `${srv.gross_margin_pct.toFixed(1)}%` : "N/A"}
                        </td>
                      </tr>
                    ))}
                    {services.length === 0 && (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-gray-400">No service categories found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Client Breakdown */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <h3 className="text-base font-semibold text-gray-900 mb-1">Top Clients by Realized Revenue</h3>
              <p className="text-xs text-gray-500 mb-4">Leaderboard of client accounts with realized revenue and active ongoing pipeline.</p>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-3 px-4 text-left font-semibold">Company</th>
                      <th className="py-3 px-4 text-left font-semibold">Sales Stage</th>
                      <th className="py-3 px-4 text-right font-semibold">Realized Won ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Deals Won</th>
                      <th className="py-3 px-4 text-right font-semibold">Active Pipeline ($)</th>
                      <th className="py-3 px-4 text-center font-semibold">Active Deals</th>
                      <th className="py-3 px-4 text-left font-semibold">Last Deal Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {clients.map((cli, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-gray-900">{cli.company_name}</div>
                          {cli.domain && <div className="text-xs text-gray-400">{cli.domain}</div>}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                            cli.sales_stage === "WON" ? "bg-emerald-100 text-emerald-800" :
                            cli.sales_stage === "LOST" ? "bg-red-100 text-red-800" :
                            "bg-blue-100 text-blue-800"
                          }`}>
                            {cli.sales_stage}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-700 font-mono">
                          ${cli.realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center font-medium">{cli.deals_won}</td>
                        <td className="py-3 px-4 text-right font-mono text-blue-700">
                          ${cli.open_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center text-gray-600">{cli.open_deal_count}</td>
                        <td className="py-3 px-4 text-xs text-gray-500">
                          {cli.last_deal_date ? new Date(cli.last_deal_date).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))}
                    {clients.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-gray-400">No client records found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Campaign ROI */}
        {activeTab === "campaigns" && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Campaign Attribution & ROI Analysis</h3>
                  <p className="text-xs text-gray-500">
                    Calculated returns for outbound campaigns with explicit sample size disclosures and causality warnings.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-3 px-4 text-left font-semibold">Campaign</th>
                      <th className="py-3 px-4 text-center font-semibold">Sample (Deals)</th>
                      <th className="py-3 px-4 text-right font-semibold">Attributed Won ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Fulfillment Cost ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Net Profit ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">ROI %</th>
                      <th className="py-3 px-4 text-left font-semibold">Attribution Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {campaigns.map((camp, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className="font-semibold text-gray-900 block">{camp.campaign_name}</span>
                          <span className="text-[11px] text-gray-400">{camp.attribution_model}</span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                            camp.has_sufficient_sample ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                          }`}>
                            {camp.sample_size} deals {camp.has_sufficient_sample ? "✓" : "(N<5)"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-700 font-mono">
                          ${camp.realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-gray-600">
                          {camp.recorded_costs != null ? `$${camp.recorded_costs.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "N/A"}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-medium">
                          {camp.net_profit != null ? `$${camp.net_profit.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "N/A"}
                        </td>
                        <td className="py-3 px-4 text-right font-bold">
                          {camp.roi_pct != null ? (
                            <span className={camp.roi_pct >= 100 ? "text-emerald-600" : "text-blue-600"}>
                              {camp.roi_pct.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-gray-400 font-normal">N/A</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-500">
                          <ul className="space-y-0.5">
                            {camp.caveats.map((c, cIdx) => (
                              <li key={cIdx} className="text-[11px] text-gray-500">• {c}</li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    ))}
                    {campaigns.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-gray-400">No campaign records found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: Deals Ledger & Calculation Provenance */}
        {activeTab === "drilldown" && drilldownData && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Audited Deal Records Ledger</h3>
                  <p className="text-xs text-gray-500">
                    Individual deal audit trails with explicit currency normalization, cost records, and sales cycle duration.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-gray-500 block mb-0.5">Filter Stage</label>
                    <select
                      value={drilldownStage}
                      onChange={(e) => {
                        setDrilldownStage(e.target.value);
                        setDrilldownPage(1);
                      }}
                      className="text-xs border-gray-300 rounded shadow-sm bg-white"
                    >
                      <option value="ALL">All Stages</option>
                      <option value="DISCOVERY">Discovery</option>
                      <option value="QUALIFICATION">Qualification</option>
                      <option value="PROPOSAL">Proposal</option>
                      <option value="NEGOTIATION">Negotiation</option>
                      <option value="WON">Won</option>
                      <option value="LOST">Lost</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-gray-500 block mb-0.5">Filter Outcome</label>
                    <select
                      value={drilldownOutcome}
                      onChange={(e) => {
                        setDrilldownOutcome(e.target.value);
                        setDrilldownPage(1);
                      }}
                      className="text-xs border-gray-300 rounded shadow-sm bg-white"
                    >
                      <option value="ALL">All Outcomes</option>
                      <option value="WON">WON</option>
                      <option value="LOST">LOST</option>
                      <option value="IN_PROGRESS">IN_PROGRESS</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-xs">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-2.5 px-3 text-left font-semibold">Deal Name / Client</th>
                      <th className="py-2.5 px-3 text-left font-semibold">Service</th>
                      <th className="py-2.5 px-3 text-left font-semibold">Stage</th>
                      <th className="py-2.5 px-3 text-right font-semibold">Native Val</th>
                      <th className="py-2.5 px-3 text-right font-semibold">USD Realized ($)</th>
                      <th className="py-2.5 px-3 text-right font-semibold">Cost ($)</th>
                      <th className="py-2.5 px-3 text-right font-semibold">Margin %</th>
                      <th className="py-2.5 px-3 text-center font-semibold">Sales Cycle</th>
                      <th className="py-2.5 px-3 text-left font-semibold">Invoicing</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {drilldownData.drilldown_records.map((deal) => (
                      <tr key={deal.id} className="hover:bg-gray-50">
                        <td className="py-2.5 px-3">
                          <span className="font-semibold text-gray-900 block">{deal.deal_name}</span>
                          <span className="text-[11px] text-gray-500">{deal.company_name}</span>
                        </td>
                        <td className="py-2.5 px-3 text-gray-700">{deal.service_category}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            deal.stage === "WON" ? "bg-emerald-100 text-emerald-800" :
                            deal.stage === "LOST" ? "bg-red-100 text-red-800" :
                            "bg-blue-100 text-blue-800"
                          }`}>
                            {deal.stage}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono">
                          {deal.stage === "WON" ? deal.native_closed_amount : deal.native_estimated_value} {deal.currency}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-gray-900">
                          {deal.normalized_closed_amount != null
                            ? `$${deal.normalized_closed_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                            : `$${deal.normalized_estimated_value.toLocaleString("en-US", { minimumFractionDigits: 2 })} (Est)`}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-gray-600">
                          {deal.cost_amount != null ? `$${deal.cost_amount.toFixed(2)}` : "—"}
                        </td>
                        <td className="py-2.5 px-3 text-right font-semibold">
                          {deal.gross_margin_pct != null ? `${deal.gross_margin_pct.toFixed(1)}%` : "—"}
                        </td>
                        <td className="py-2.5 px-3 text-center text-gray-600">
                          {deal.sales_cycle_days != null ? `${deal.sales_cycle_days}d` : "—"}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-[11px] text-gray-500 block">
                            {deal.invoice_status || "UNINVOICED"}
                          </span>
                          {deal.invoiced_amount && (
                            <span className="text-[10px] text-gray-400">
                              Inv: ${deal.invoiced_amount.toFixed(0)} | Paid: ${deal.paid_amount || 0}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {drilldownData.drilldown_records.length === 0 && (
                      <tr>
                        <td colSpan={9} className="py-8 text-center text-gray-400">No deal records match query.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <span>
                  Showing {drilldownData.drilldown_records.length} of {drilldownData.total_records} records (Page {drilldownData.page} of {drilldownData.total_pages})
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={drilldownPage <= 1}
                    onClick={() => setDrilldownPage(prev => Math.max(1, prev - 1))}
                    className="px-2.5 py-1 border border-gray-300 rounded bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    disabled={drilldownPage >= drilldownData.total_pages}
                    onClick={() => setDrilldownPage(prev => prev + 1)}
                    className="px-2.5 py-1 border border-gray-300 rounded bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: Snapshots Archive */}
        {activeTab === "snapshots" && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Audited Historical Snapshots Archive</h3>
                  <p className="text-xs text-gray-500">
                    Immutable snapshots stored in persistent database table <code className="bg-gray-100 px-1 py-0.5 rounded">revenue_analytics_snapshots</code>.
                  </p>
                </div>
                <button
                  onClick={() => setShowSnapshotModal(true)}
                  className="px-3 py-1.5 bg-emerald-600 text-white rounded text-xs font-medium hover:bg-emerald-700"
                >
                  New Snapshot
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600">
                      <th className="py-3 px-4 text-left font-semibold">Snapshot ID / Date</th>
                      <th className="py-3 px-4 text-left font-semibold">Period Type</th>
                      <th className="py-3 px-4 text-right font-semibold">Realized Won ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Open Pipeline ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Weighted ($)</th>
                      <th className="py-3 px-4 text-right font-semibold">Margin %</th>
                      <th className="py-3 px-4 text-center font-semibold">Deals (Won/Open)</th>
                      <th className="py-3 px-4 text-left font-semibold">Auditor</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {snapshots.map((snap) => (
                      <tr key={snap.id} className="hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className="font-mono text-xs font-semibold text-gray-900 block">{snap.id.substring(0, 8)}</span>
                          <span className="text-[11px] text-gray-400">{new Date(snap.created_at).toLocaleString()}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            {snap.period_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-emerald-700">
                          ${snap.total_realized_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-blue-700">
                          ${snap.total_open_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-gray-700">
                          ${snap.weighted_pipeline_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-semibold">
                          {snap.gross_margin_pct != null ? `${snap.gross_margin_pct.toFixed(1)}%` : "N/A"}
                        </td>
                        <td className="py-3 px-4 text-center text-xs">
                          {snap.deal_count_won} won / {snap.deal_count_open} open
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-600">{snap.created_by}</td>
                      </tr>
                    ))}
                    {snapshots.length === 0 && (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-gray-400">No snapshots recorded yet. Capture a snapshot above.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Snapshot Capture Modal */}
      {showSnapshotModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-900/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
              <Archive className="w-5 h-5 text-emerald-600" />
              Capture Audited Revenue Snapshot
            </h3>
            <p className="text-xs text-gray-600 mb-4">
              Persists an immutable historical snapshot of current realized revenue, pipeline value, margins, and breakdown matrices to database.
            </p>

            <div className="space-y-3 mb-5">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Target Period</label>
                <div className="text-sm font-medium text-gray-900 bg-gray-50 p-2 rounded border border-gray-200">
                  {periodType} {startDate && endDate ? `(${startDate} to ${endDate})` : ""}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Auditor / Reviewer Username</label>
                <input
                  type="text"
                  value={snapshotAuthor}
                  onChange={(e) => setSnapshotAuthor(e.target.value)}
                  className="w-full text-sm border-gray-300 rounded shadow-sm focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g. finance_director"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowSnapshotModal(false)}
                className="px-4 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateSnapshot}
                disabled={snapshotLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm font-medium disabled:opacity-50"
              >
                {snapshotLoading ? "Capturing..." : "Confirm & Save Snapshot"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
