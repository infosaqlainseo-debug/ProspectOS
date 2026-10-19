"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Plus,
  CheckCircle2,
  Clock,
  Send,
  Download,
  AlertCircle,
  Eye,
  Calendar,
  Shield,
  RefreshCw,
  X,
  FileCheck,
  Building,
  ExternalLink
} from "lucide-react";
import {
  ClientReport,
  ReportSchedule,
  PortalAuditLog,
  getClientReports,
  generateClientReport,
  approveClientReport,
  deliverClientReport,
  exportClientReport,
  getReportSchedules,
  createReportSchedule,
  triggerReportSchedules,
  getPortalAuditLogs,
  useApi
} from "@/lib/api";

export default function ReportsManagementPage() {
  const [reports, setReports] = useState<ClientReport[]>([]);
  const [schedules, setSchedules] = useState<ReportSchedule[]>([]);
  const [auditLogs, setAuditLogs] = useState<PortalAuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"reports" | "schedules" | "audit">("reports");

  // Selection & Modals
  const [selectedReport, setSelectedReport] = useState<ClientReport | null>(null);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [isDeliverModalOpen, setIsDeliverModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewFormat, setPreviewFormat] = useState<"markdown" | "html">("markdown");

  // Form states
  const [selectedCompanyId, setSelectedCompanyId] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [reportType, setReportType] = useState("MONTHLY_PERFORMANCE");
  const [customNotes, setCustomNotes] = useState("");
  const [deliveryRecipients, setDeliveryRecipients] = useState("");
  const [deliverySimulate, setDeliverySimulate] = useState(true);

  // New Schedule form
  const [schedCompanyId, setSchedCompanyId] = useState("");
  const [schedFrequency, setSchedFrequency] = useState<"WEEKLY" | "MONTHLY" | "QUARTERLY">("MONTHLY");
  const [schedTimeZone, setSchedTimeZone] = useState("UTC");
  const [schedRecipients, setSchedRecipients] = useState("");

  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Fetch companies for dropdowns
  const { data: companiesData } = useApi<{ items?: Array<{ id: string; company_name: string; canonical_domain?: string }> }>(
    "/companies?limit=50"
  );
  const companies = companiesData?.items || [];

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [reps, scheds, audits] = await Promise.all([
        getClientReports(),
        getReportSchedules(),
        getPortalAuditLogs({ limit: 25 })
      ]);
      setReports(reps);
      setSchedules(scheds);
      setAuditLogs(audits);
    } catch (err: unknown) {
      console.error("Failed to load reports data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId || !reportTitle) return;

    try {
      const newReport = await generateClientReport({
        company_id: selectedCompanyId,
        title: reportTitle,
        report_type: reportType,
        custom_notes: customNotes
      });
      setReports([newReport, ...reports]);
      setIsGenerateModalOpen(false);
      setReportTitle("");
      setCustomNotes("");
      setNotification({ type: "success", message: `Generated report "${newReport.title}" in Draft status.` });
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Failed to generate report." });
    }
  };

  const handleApprove = async (reportId: string) => {
    try {
      const updated = await approveClientReport(reportId, {
        approval_status: "APPROVED",
        notes: "Approved by Agency Operator"
      });
      setReports(reports.map(r => r.id === reportId ? updated : r));
      if (selectedReport?.id === reportId) setSelectedReport(updated);
      setNotification({ type: "success", message: `Report "${updated.title}" approved for client presentation.` });
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Approval failed." });
    }
  };

  const handleDeliver = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;

    const emails = deliveryRecipients
      .split(",")
      .map(s => s.trim())
      .filter(Boolean);

    try {
      const logs = await deliverClientReport(selectedReport.id, {
        recipients: emails.length > 0 ? emails : undefined,
        delivery_channel: "EMAIL",
        simulate: deliverySimulate
      });
      setIsDeliverModalOpen(false);
      setNotification({
        type: "success",
        message: `Dispatched report to ${logs.length} recipients (${deliverySimulate ? "Simulated Safe Mode" : "Sent"}).`
      });
      loadData();
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Delivery failed." });
    }
  };

  const handleExport = async (reportId: string, format: "markdown" | "html") => {
    try {
      const text = await exportClientReport(reportId, format);
      setPreviewContent(text);
      setPreviewFormat(format);
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Export failed." });
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schedCompanyId) return;

    try {
      const newSched = await createReportSchedule({
        company_id: schedCompanyId,
        frequency: schedFrequency,
        time_zone: schedTimeZone,
        recipients: schedRecipients.split(",").map(s => s.trim()).filter(Boolean),
        requires_approval: true
      });
      setSchedules([newSched, ...schedules]);
      setIsScheduleModalOpen(false);
      setNotification({ type: "success", message: "Recurring report schedule activated." });
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Schedule creation failed." });
    }
  };

  const handleTriggerSchedules = async () => {
    try {
      const triggered = await triggerReportSchedules();
      setNotification({ type: "success", message: `Triggered scheduled runs. Generated ${triggered.length} reports.` });
      loadData();
    } catch (err: unknown) {
      setNotification({ type: "error", message: err instanceof Error ? err.message : "Trigger failed." });
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
              <FileText className="h-6 w-6" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              Automated Reporting & Client Portals
            </h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Generate evidence-grounded, branded client deliverables with strict approval gates, tenancy isolation, and non-fabrication policies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsScheduleModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-sm"
          >
            <Calendar className="h-4 w-4 text-gray-500" />
            New Schedule
          </button>
          <button
            onClick={() => setIsGenerateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition"
          >
            <Plus className="h-4 w-4" />
            Generate Report
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between ${
            notification.type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          <div className="flex items-center gap-2 text-sm font-medium">
            {notification.type === "success" ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
            {notification.message}
          </div>
          <button onClick={() => setNotification(null)} className="text-gray-500 hover:text-gray-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Reports</div>
          <div className="text-2xl font-bold text-gray-900 mt-2">{reports.length}</div>
          <div className="text-xs text-gray-400 mt-1">Stored across all accounts</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Pending Review</div>
          <div className="text-2xl font-bold text-amber-600 mt-2">
            {reports.filter(r => r.approval_status === "UNAPPROVED").length}
          </div>
          <div className="text-xs text-amber-500 mt-1">Safety boundary enforced</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Approved Deliverables</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2">
            {reports.filter(r => r.approval_status === "APPROVED").length}
          </div>
          <div className="text-xs text-emerald-500 mt-1">Client portal visible</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Schedules</div>
          <div className="text-2xl font-bold text-indigo-600 mt-2">
            {schedules.filter(s => s.is_active).length}
          </div>
          <div className="text-xs text-indigo-500 mt-1">Automated background cadence</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6 -mb-px">
          <button
            onClick={() => setActiveTab("reports")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 ${
              activeTab === "reports"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <FileText className="h-4 w-4" />
            Client Reports ({reports.length})
          </button>
          <button
            onClick={() => setActiveTab("schedules")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 ${
              activeTab === "schedules"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Calendar className="h-4 w-4" />
            Cadence & Schedules ({schedules.length})
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 ${
              activeTab === "audit"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Shield className="h-4 w-4" />
            Security Audit Logs
          </button>
        </nav>
      </div>

      {/* TAB 1: REPORTS TABLE */}
      {activeTab === "reports" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50/50">
            <h2 className="text-sm font-semibold text-gray-800">Generated Client Reports</h2>
            <button
              onClick={loadData}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md bg-white shadow-sm"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase border-b border-gray-200">
                <tr>
                  <th className="py-3 px-4">Title & Company</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Reporting Period</th>
                  <th className="py-3 px-4">Approval Status</th>
                  <th className="py-3 px-4">Delivery</th>
                  <th className="py-3 px-4">Generated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reports.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-400">
                      No reports generated yet. Click &quot;Generate Report&quot; to formulate the first deliverable.
                    </td>
                  </tr>
                ) : (
                  reports.map(report => (
                    <tr key={report.id} className="hover:bg-gray-50 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gray-900">{report.title}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                          <Building className="h-3 w-3" />
                          {report.company_name}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                          {report.report_type.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-600">
                        {report.reporting_period_start ? report.reporting_period_start.slice(0, 10) : "N/A"} to{" "}
                        {report.reporting_period_end ? report.reporting_period_end.slice(0, 10) : "N/A"}
                      </td>
                      <td className="py-3 px-4">
                        {report.approval_status === "APPROVED" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" /> Approved
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                            <Clock className="h-3 w-3" /> Unapproved Draft
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded ${
                          report.delivery_status === "DELIVERED"
                            ? "bg-blue-50 text-blue-700 border border-blue-200"
                            : "bg-gray-100 text-gray-600"
                        }`}>
                          {report.delivery_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-500">
                        {new Date(report.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => handleExport(report.id, "html")}
                            title="Preview HTML"
                            className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-gray-100 rounded"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleExport(report.id, "markdown")}
                            title="Download Markdown"
                            className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-gray-100 rounded"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          {report.approval_status === "UNAPPROVED" && (
                            <button
                              onClick={() => handleApprove(report.id)}
                              title="Approve Report"
                              className="px-2 py-1 text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded shadow-xs"
                            >
                              Approve
                            </button>
                          )}
                          {report.approval_status === "APPROVED" && (
                            <button
                              onClick={() => {
                                setSelectedReport(report);
                                setIsDeliverModalOpen(true);
                              }}
                              title="Deliver to Client"
                              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded shadow-xs"
                            >
                              <Send className="h-3 w-3" /> Deliver
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: SCHEDULES */}
      {activeTab === "schedules" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-800">Configured Cadences</h2>
            <button
              onClick={handleTriggerSchedules}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-100"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Trigger Due Schedules Now
            </button>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase border-b border-gray-200">
                <tr>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Report Type</th>
                  <th className="py-3 px-4">Cadence</th>
                  <th className="py-3 px-4">Timezone</th>
                  <th className="py-3 px-4">Recipients</th>
                  <th className="py-3 px-4">Safety Gate</th>
                  <th className="py-3 px-4">Next Scheduled Run</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {schedules.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-400">
                      No automated schedules configured.
                    </td>
                  </tr>
                ) : (
                  schedules.map(sched => (
                    <tr key={sched.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{sched.company_name || sched.company_id}</td>
                      <td className="py-3 px-4 text-xs text-gray-600">{sched.report_type}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 rounded">
                          {sched.frequency}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-500">{sched.time_zone}</td>
                      <td className="py-3 px-4 text-xs text-gray-600">
                        {sched.recipients?.length > 0 ? sched.recipients.join(", ") : "Default client account"}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Approval Required
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-500">
                        {sched.next_run_at ? new Date(sched.next_run_at).toLocaleString() : "Pending"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: AUDIT LOGS */}
      {activeTab === "audit" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50/50">
            <h2 className="text-sm font-semibold text-gray-800">Security & Administrative Audit Trail</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Immutable server-side event history tracking authentication, approvals, invitations, and access attempts.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase border-b border-gray-200">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {auditLogs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50 text-xs">
                    <td className="py-3 px-4 text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="py-3 px-4 font-mono font-semibold">
                      <span className={`px-2 py-0.5 rounded ${
                        log.action.includes("UNAUTHORIZED")
                          ? "bg-red-50 text-red-700 border border-red-200"
                          : log.action.includes("APPROVE")
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-gray-100 text-gray-700"
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{log.resource_type}</td>
                    <td className="py-3 px-4 text-gray-800">{log.user_email || log.user_id || "System"}</td>
                    <td className="py-3 px-4 text-gray-500 font-mono truncate max-w-xs">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* GENERATE REPORT MODAL */}
      {isGenerateModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Formulate Client Report</h3>
              <button onClick={() => setIsGenerateModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleGenerateReport} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Target Client Company</label>
                <select
                  value={selectedCompanyId}
                  onChange={e => setSelectedCompanyId(e.target.value)}
                  required
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 bg-white text-gray-900 focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a company...</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.company_name} ({c.canonical_domain || "No domain"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Report Title</label>
                <input
                  type="text"
                  value={reportTitle}
                  onChange={e => setReportTitle(e.target.value)}
                  placeholder="e.g. Q4 SEO Intelligence & Media Review"
                  required
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Deliverable Type</label>
                <select
                  value={reportType}
                  onChange={e => setReportType(e.target.value)}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="MONTHLY_PERFORMANCE">Monthly Performance</option>
                  <option value="QUARTERLY_REVIEW">Quarterly Strategic Review</option>
                  <option value="SEO_AUDIT_DELIVERABLE">Technical SEO Audit</option>
                  <option value="EXECUTIVE_SUMMARY">Executive Summary</option>
                  <option value="CAMPAIGN_SUMMARY">Digital PR & Placement Summary</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Agency Executive Notes</label>
                <textarea
                  rows={3}
                  value={customNotes}
                  onChange={e => setCustomNotes(e.target.value)}
                  placeholder="Key strategic insights or context from account team..."
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="p-3 bg-amber-50 rounded-lg text-xs text-amber-800 border border-amber-200 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  <strong>Strict Non-Fabrication:</strong> Real stored crawl scans, placement records, and intent topics will be assembled. Internal agency margins and unverified third-party rankings are excluded.
                </span>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm"
                >
                  Assemble Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELIVER MODAL */}
      {isDeliverModalOpen && selectedReport && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Deliver Client Report</h3>
              <button onClick={() => setIsDeliverModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleDeliver} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Report</label>
                <div className="p-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-800">
                  {selectedReport.title}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Recipient Emails</label>
                <input
                  type="text"
                  value={deliveryRecipients}
                  onChange={e => setDeliveryRecipients(e.target.value)}
                  placeholder="e.g. client@example.com, cfo@example.com"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">Leave blank to dispatch to registered workspace users.</p>
              </div>

              <div className="flex items-center gap-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-900">
                <input
                  type="checkbox"
                  id="simulate"
                  checked={deliverySimulate}
                  onChange={e => setDeliverySimulate(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="simulate" className="font-medium cursor-pointer">
                  Safe Simulation Mode (Logs delivery & idempotency without dispatching real email)
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setIsDeliverModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm flex items-center gap-1.5"
                >
                  <Send className="h-4 w-4" />
                  Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SCHEDULE MODAL */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Configure Cadence Schedule</h3>
              <button onClick={() => setIsScheduleModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreateSchedule} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Client Company</label>
                <select
                  value={schedCompanyId}
                  onChange={e => setSchedCompanyId(e.target.value)}
                  required
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 bg-white text-gray-900 focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a company...</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.company_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Cadence Frequency</label>
                <select
                  value={schedFrequency}
                  onChange={e => setSchedFrequency(e.target.value as "WEEKLY" | "MONTHLY" | "QUARTERLY")}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="QUARTERLY">Quarterly</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Timezone</label>
                <input
                  type="text"
                  value={schedTimeZone}
                  onChange={e => setSchedTimeZone(e.target.value)}
                  placeholder="e.g. America/New_York or UTC"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Recipients</label>
                <input
                  type="text"
                  value={schedRecipients}
                  onChange={e => setSchedRecipients(e.target.value)}
                  placeholder="Comma separated emails"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setIsScheduleModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm"
                >
                  Activate Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PREVIEW EXPORT MODAL */}
      {previewContent && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[85vh] flex flex-col border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-gray-900">
                  Deliverable Export Preview ({previewFormat.toUpperCase()})
                </h3>
              </div>
              <button
                onClick={() => setPreviewContent(null)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 bg-white">
              {previewFormat === "html" ? (
                <div
                  dangerouslySetInnerHTML={{ __html: previewContent }}
                  className="prose max-w-none text-sm"
                />
              ) : (
                <pre className="text-xs font-mono whitespace-pre-wrap text-gray-800 bg-gray-50 p-4 rounded-lg border border-gray-200">
                  {previewContent}
                </pre>
              )}
            </div>
            <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end">
              <button
                onClick={() => setPreviewContent(null)}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
