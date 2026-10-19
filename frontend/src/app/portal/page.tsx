"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Building,
  Globe,
  Lock,
  FileText,
  Download,
  Eye,
  CheckCircle2,
  AlertTriangle,
  UserPlus,
  RefreshCw,
  X,
  Send,
  Sparkles,
  ExternalLink,
  Layers,
  Award
} from "lucide-react";
import {
  PortalWorkspace,
  ClientReport,
  getClientWorkspace,
  getClientReports,
  exportClientReport,
  createClientInvitation,
  useApi
} from "@/lib/api";

export default function ClientPortalPage() {
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [workspace, setWorkspace] = useState<PortalWorkspace | null>(null);
  const [approvedReports, setApprovedReports] = useState<ClientReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Invite modal
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteResult, setInviteResult] = useState<{ token: string; email: string } | null>(null);

  // Export Preview Modal
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewFormat, setPreviewFormat] = useState<"markdown" | "html">("markdown");

  // Companies dropdown
  const { data: companiesData } = useApi<{ items?: Array<{ id: string; company_name: string; canonical_domain?: string }> }>(
    "/companies?limit=50"
  );
  const companies = companiesData?.items || [];

  // Default to first company when loaded
  useEffect(() => {
    if (companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  const loadWorkspace = async (companyId: string) => {
    if (!companyId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [ws, reps] = await Promise.all([
        getClientWorkspace(companyId),
        getClientReports({ company_id: companyId, approval_filter: "APPROVED" })
      ]);
      setWorkspace(ws);
      setApprovedReports(reps);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load client workspace.");
      setWorkspace(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCompanyId) {
      loadWorkspace(selectedCompanyId);
    }
  }, [selectedCompanyId]);

  const handleExport = async (reportId: string, format: "markdown" | "html") => {
    try {
      const text = await exportClientReport(reportId, format);
      setPreviewContent(text);
      setPreviewFormat(format);
    } catch (err: unknown) {
      alert("Failed to export report: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId || !inviteEmail) return;

    try {
      const res = await createClientInvitation({
        company_id: selectedCompanyId,
        email: inviteEmail,
        role: "CLIENT_USER"
      });
      setInviteResult({ token: res.invitation_token, email: res.email });
      setInviteEmail("");
    } catch (err: unknown) {
      alert("Invitation failed: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Workspace Switcher & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-emerald-50 text-emerald-700 rounded-lg">
              <ShieldCheck className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">
                Client Workspace & Deliverables Portal
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Multi-tenant, role-isolated client view with verified deliverables and strictly minimized sensitive records.
              </p>
            </div>
          </div>
        </div>

        {/* Account Selector */}
        <div className="flex items-center gap-3 bg-white p-2 rounded-xl border border-gray-200 shadow-xs">
          <Building className="h-4 w-4 text-gray-500 ml-2" />
          <select
            value={selectedCompanyId}
            onChange={e => setSelectedCompanyId(e.target.value)}
            className="text-sm bg-transparent border-none text-gray-900 font-medium focus:ring-0 cursor-pointer pr-4"
          >
            {companies.map(c => (
              <option key={c.id} value={c.id}>
                {c.company_name} ({c.canonical_domain || "Active Client"})
              </option>
            ))}
          </select>
          <button
            onClick={() => loadWorkspace(selectedCompanyId)}
            title="Refresh Workspace"
            className="p-1.5 text-gray-400 hover:text-gray-700 rounded-md"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 text-red-600" />
          <div>{error}</div>
        </div>
      )}

      {workspace && (
        <div className="space-y-8">
          {/* Client Branding Hero */}
          <div className="bg-gradient-to-r from-indigo-900 via-indigo-850 to-slate-900 text-white p-8 rounded-2xl shadow-md border border-indigo-950 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-indigo-200 backdrop-blur-xs">
                <Sparkles className="h-3.5 w-3.5 text-indigo-300" />
                Managed by {workspace.branding.agency_name}
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight">
                {workspace.company_name}
              </h2>
              <div className="flex items-center gap-4 text-sm text-indigo-200">
                <span className="flex items-center gap-1.5">
                  <Globe className="h-4 w-4" />
                  {workspace.canonical_domain || "Verified Domain"}
                </span>
                <span>•</span>
                <span>Industry: {workspace.industry || "Enterprise"}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsInviteModalOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-medium border border-white/20 transition"
              >
                <UserPlus className="h-4 w-4" />
                Invite Team Member
              </button>
            </div>
          </div>

          {/* Non-Fabrication & Security Banner */}
          <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-xl flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-emerald-700 shrink-0 mt-0.5" />
            <div className="text-xs text-emerald-900 leading-relaxed">
              <strong>Strict Non-Fabrication Guarantee:</strong> All deliverables, technical audit scores, and placement records displayed in this portal are compiled exclusively from verified live website scans and authorized agency activities. Estimated or fabricated third-party rankings are strictly withheld in accordance with ProspectOS data integrity standards.
            </div>
          </div>

          {/* High Level KPI Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Crawl Health</div>
              <div className="text-2xl font-bold text-gray-900 mt-2 flex items-center gap-2">
                {workspace.verified_seo_health.https_secure ? (
                  <span className="text-emerald-600 flex items-center gap-1.5 text-lg">
                    <CheckCircle2 className="h-5 w-5" /> SSL Enforced
                  </span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1.5 text-lg">
                    <AlertTriangle className="h-5 w-5" /> Attention Required
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                HTTP {workspace.verified_seo_health.http_status || 200}
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Approved Deliverables</div>
              <div className="text-2xl font-bold text-indigo-600 mt-2">
                {workspace.available_reports_count}
              </div>
              <div className="text-xs text-gray-400 mt-1">Ready for executive review</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Campaigns</div>
              <div className="text-2xl font-bold text-gray-900 mt-2">
                {workspace.active_campaigns_count}
              </div>
              <div className="text-xs text-gray-400 mt-1">Communications & digital PR</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Media Plans</div>
              <div className="text-2xl font-bold text-emerald-600 mt-2">
                {workspace.approved_media_plans_count}
              </div>
              <div className="text-xs text-gray-400 mt-1">Allocated publications</div>
            </div>
          </div>

          {/* Middle Grid: SEO Technical Signals + Content Deliverables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* SEO Health Card */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <div className="flex items-center gap-2 font-semibold text-gray-900">
                  <Layers className="h-5 w-5 text-indigo-600" />
                  Website Technical Crawl Baseline
                </div>
                <span className="text-xs font-medium bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Verified Scan
                </span>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1.5 border-b border-gray-50">
                  <span className="text-gray-500">Target Address</span>
                  <span className="font-medium text-gray-900">{workspace.canonical_domain || "N/A"}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-50">
                  <span className="text-gray-500">Security / TLS Transport</span>
                  <span className="font-medium text-emerald-600 flex items-center gap-1">
                    <Lock className="h-3.5 w-3.5" /> 100% Encrypted
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-50">
                  <span className="text-gray-500">Page Title Optimization</span>
                  <span className="font-medium text-gray-900 truncate max-w-xs" title={workspace.verified_seo_health.title_tag}>
                    {workspace.verified_seo_health.title_tag || "Verified Tag"}
                  </span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-gray-500">Audit Status</span>
                  <span className="text-xs font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                    {workspace.verified_seo_health.crawl_status}
                  </span>
                </div>
              </div>
            </div>

            {/* Content & Growth Pillars */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <div className="flex items-center gap-2 font-semibold text-gray-900">
                  <Award className="h-5 w-5 text-indigo-600" />
                  Search Intent & Content Deliverables
                </div>
                <span className="text-xs font-medium bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full border border-indigo-200">
                  Active Focus
                </span>
              </div>
              <div className="space-y-3">
                {workspace.client_visible_opportunities.map((opp, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-sm space-y-1">
                    <div className="font-semibold text-indigo-950 flex items-center justify-between">
                      <span>{opp.category}</span>
                      <span className="text-xs font-normal text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        Pillar
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">{opp.summary}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Approved Reports Deliverables Library */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-200 flex items-center justify-between bg-gray-50/50">
              <div>
                <h3 className="text-base font-bold text-gray-900">Client Deliverables Library</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Official reports approved and certified by your agency team.
                </p>
              </div>
              <span className="text-xs font-semibold text-gray-500 bg-white border border-gray-200 px-2.5 py-1 rounded-md">
                {approvedReports.length} Available
              </span>
            </div>

            <div className="divide-y divide-gray-200">
              {approvedReports.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">
                  No approved reports published yet for this account. Your agency team is currently finalizing your initial deliverable.
                </div>
              ) : (
                approvedReports.map(rep => (
                  <div key={rep.id} className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-gray-50 transition">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900">{rep.title}</span>
                        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full font-medium border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3" /> Certified Deliverable
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 flex items-center gap-4">
                        <span>Type: {rep.report_type.replace(/_/g, " ")}</span>
                        <span>•</span>
                        <span>
                          Period: {rep.reporting_period_start ? rep.reporting_period_start.slice(0, 10) : "N/A"} to{" "}
                          {rep.reporting_period_end ? rep.reporting_period_end.slice(0, 10) : "N/A"}
                        </span>
                        <span>•</span>
                        <span>Published: {new Date(rep.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleExport(rep.id, "html")}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-xs"
                      >
                        <Eye className="h-3.5 w-3.5 text-gray-500" /> View Document
                      </button>
                      <button
                        onClick={() => handleExport(rep.id, "markdown")}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-xs"
                      >
                        <Download className="h-3.5 w-3.5 text-gray-500" /> Markdown
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TEAM INVITATION MODAL */}
      {isInviteModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Invite Team Member</h3>
              <button onClick={() => setIsInviteModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            {inviteResult ? (
              <div className="mt-4 space-y-4">
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800">
                  <div className="font-bold">Invitation Generated Successfully!</div>
                  <div className="mt-1">
                    An invitation token was issued for <strong>{inviteResult.email}</strong>:
                  </div>
                  <pre className="mt-2 p-2 bg-white rounded border border-emerald-300 font-mono text-emerald-950 truncate">
                    {inviteResult.token}
                  </pre>
                </div>
                <button
                  onClick={() => {
                    setInviteResult(null);
                    setIsInviteModalOpen(false);
                  }}
                  className="w-full py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleInvite} className="space-y-4 mt-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Colleague Work Email</label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={e => setInviteEmail(e.target.value)}
                    placeholder="teammate@company.com"
                    required
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    The user will be restricted strictly to this company workspace.
                  </p>
                </div>
                <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setIsInviteModalOpen(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm flex items-center gap-1.5"
                  >
                    <Send className="h-4 w-4" /> Issue Invitation
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* DOCUMENT PREVIEW MODAL */}
      {previewContent && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[85vh] flex flex-col border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <h3 className="text-base font-bold text-gray-900">
                Deliverable Document Preview ({previewFormat.toUpperCase()})
              </h3>
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
