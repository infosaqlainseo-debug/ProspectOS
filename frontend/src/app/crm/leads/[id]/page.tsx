"use client";

import { Suspense, useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  Globe2,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Sparkles,
  ArrowLeft,
  Tag,
  ExternalLink,
  CheckCircle2,
  Clock,
  FileText,
  Activity,
  Layers,
  Search,
  AlertTriangle,
  RefreshCw,
  Plus
} from "lucide-react";

function LinkedinIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.53 1.53 0 1 0-.01-3.05 1.53 1.53 0 0 0 .01 3.05m1.39 9.74v-8.37H5.07v8.37h2.78Z" />
    </svg>
  );
}
import { crmApi, CRMLeadDetail, CRMAIResearch } from "@/lib/crmApi";

const STAGES = [
  "NEW",
  "QUALIFIED",
  "RESEARCHED",
  "CONTACTED",
  "REPLIED",
  "INTERESTED",
  "MEETING_SCHEDULED",
  "NEGOTIATION",
  "WON",
  "LOST"
];

function LeadDetailContent({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const leadId = resolvedParams.id;
  const router = useRouter();

  const [detail, setDetail] = useState<CRMLeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "ai_research" | "timeline" | "notes">("overview");

  // AI Research state
  const [analyzingAi, setAnalyzingAi] = useState(false);

  // New Note state
  const [newNoteContent, setNewNoteContent] = useState("");
  const [submittingNote, setSubmittingNote] = useState(false);

  // Stage change state
  const [currentStage, setCurrentStage] = useState("NEW");

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const res = await crmApi.getLead(leadId);
      setDetail(res);
      setCurrentStage(res.company.sales_stage);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [leadId]);

  const handleStageChange = async (newStage: string) => {
    try {
      setCurrentStage(newStage);
      await crmApi.updateLeadStage(leadId, newStage, `Manual stage change to ${newStage}`);
      await fetchDetail();
    } catch (e: any) {
      alert(e.message || "Failed to update stage");
    }
  };

  const handleRunAiAnalysis = async () => {
    try {
      setAnalyzingAi(true);
      const research = await crmApi.analyzeLeadWithAI(leadId);
      if (detail) {
        setDetail({ ...detail, ai_research: research });
      }
      setActiveTab("ai_research");
      await fetchDetail();
    } catch (e: any) {
      alert(e.message || "AI Analysis failed");
    } finally {
      setAnalyzingAi(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;
    try {
      setSubmittingNote(true);
      const res = await fetch(`/crm/prospects/${leadId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newNoteContent.trim(), author: "human_reviewer" })
      });
      if (!res.ok) throw new Error("Failed to add note");
      setNewNoteContent("");
      await fetchDetail();
    } catch (e: any) {
      alert(e.message || "Failed to add note");
    } finally {
      setSubmittingNote(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 text-sm">
        Loading lead intelligence profile...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-12 text-center text-slate-500 text-sm space-y-3">
        <p>Lead not found or has been deleted.</p>
        <Link href="/crm" className="text-indigo-600 font-semibold hover:underline">
          Return to All Leads
        </Link>
      </div>
    );
  }

  const { company, ai_research, notes, activities } = detail;
  const components = company.lead_score_components || {};

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/crm"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Leads Directory
        </Link>
      </div>

      {/* Main Profile Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {company.company_name}
            </h1>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
              company.lead_priority === "CRITICAL"
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : company.lead_priority === "HIGH"
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-slate-100 text-slate-700 border-slate-200"
            }`}>
              {company.lead_priority} PRIORITY
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 font-medium">
            {company.canonical_domain && (
              <a
                href={company.website_url || `https://${company.canonical_domain}`}
                target="_blank"
                rel="noreferrer"
                className="text-indigo-600 hover:underline flex items-center gap-1 font-mono"
              >
                <Globe2 className="w-3.5 h-3.5" />
                <span>{company.canonical_domain}</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            )}
            {company.industry && (
              <span className="flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                {company.industry}
              </span>
            )}
            {(company.city || company.country) && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                {[company.city, company.country].filter(Boolean).join(", ")}
              </span>
            )}
          </div>
        </div>

        {/* Right Action / Stage Selector */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Pipeline Stage</span>
            <select
              value={currentStage}
              onChange={(e) => handleStageChange(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-800 shadow-sm focus:ring-2 focus:ring-indigo-500"
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>{s.replace("_", " ")}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRunAiAnalysis}
            disabled={analyzingAi}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition shadow-sm shadow-indigo-500/20"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {analyzingAi ? "Analyzing..." : "Analyze with AI"}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 text-xs font-semibold">
        {[
          { id: "overview", label: "Overview & Intelligence" },
          { id: "ai_research", label: "AI Research Dossier", badge: ai_research ? "Ready" : undefined },
          { id: "timeline", label: `Activity Timeline (${activities.length})` },
          { id: "notes", label: `Internal Notes (${notes.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === tab.id
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <span>{tab.label}</span>
            {tab.badge && (
              <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1 py-0.2 rounded font-mono">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview & Intelligence */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column (2 spans) */}
          <div className="md:col-span-2 space-y-6">
            {/* Transparent 4-Pillar Lead Score Breakdown */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Multi-Pillar Lead Quality Score</h3>
                  <p className="text-xs text-slate-500">Transparent scoring breakdown derived from verified parameters</p>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold font-mono text-indigo-700">
                    {company.lead_score ? Math.round(company.lead_score) : "--"}
                  </span>
                  <span className="text-xs text-slate-400">/ 100</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                {[
                  {
                    title: "Reachability",
                    score: components.contact_reachability?.score ?? "--",
                    max: 30,
                    status: company.public_email ? "Email Verified" : "Missing Direct Email"
                  },
                  {
                    title: "Completeness",
                    score: components.profile_completeness?.score ?? "--",
                    max: 25,
                    status: company.industry ? "Profile Structured" : "Partial Metadata"
                  },
                  {
                    title: "Viability",
                    score: components.website_viability?.score ?? "--",
                    max: 25,
                    status: company.website_url ? "Active Domain" : "Unverified Site"
                  },
                  {
                    title: "SEO Upside",
                    score: components.seo_opportunity?.score ?? "--",
                    max: 20,
                    status: "High Growth Fit"
                  },
                ].map((col, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-lg space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">{col.title}</span>
                    <div className="text-sm font-bold font-mono text-slate-800">
                      {col.score} <span className="text-[10px] text-slate-400 font-normal">/ {col.max}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 truncate block">{col.status}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Company Overview & Description */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-slate-900">About {company.company_name}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                {company.description || "No official description extracted yet. Run 'Analyze with AI' to synthesize full business profile."}
              </p>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100 text-xs">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Company Size</span>
                  <p className="font-medium text-slate-800 mt-0.5">{company.company_size || "Undisclosed / SMB"}</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Lead Source</span>
                  <p className="font-medium text-slate-800 mt-0.5">{company.lead_source || "Web Scraper"}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Contact Details & Tags */}
          <div className="space-y-6">
            {/* Contact Information */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Verified Contact Channels</h3>

              <div className="space-y-3 text-xs">
                <div className="flex items-start gap-2.5">
                  <Mail className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Public Business Email</span>
                    {company.public_email ? (
                      <a href={`mailto:${company.public_email}`} className="font-mono text-indigo-600 hover:underline">
                        {company.public_email}
                      </a>
                    ) : (
                      <span className="text-slate-400 font-mono">Not found</span>
                    )}
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Phone className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Business Phone</span>
                    {company.phone_number ? (
                      <a href={`tel:${company.phone_number}`} className="font-mono text-slate-800 hover:underline">
                        {company.phone_number}
                      </a>
                    ) : (
                      <span className="text-slate-400 font-mono">Not found</span>
                    )}
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <LinkedinIcon className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">LinkedIn Profile</span>
                    {company.linkedin_url ? (
                      <a href={company.linkedin_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline truncate block max-w-[200px]">
                        {company.linkedin_url}
                      </a>
                    ) : (
                      <span className="text-slate-400">Not connected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Tags & Taxonomy */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-slate-900">Tags & Categorization</h3>
              <div className="flex flex-wrap gap-1.5">
                {(company.tags || []).length === 0 ? (
                  <span className="text-xs text-slate-400">No tags assigned</span>
                ) : (
                  company.tags.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                    >
                      {t}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: AI Research Dossier */}
      {activeTab === "ai_research" && (
        <div className="space-y-6">
          {!ai_research ? (
            <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="max-w-md mx-auto">
                <h3 className="text-base font-bold text-slate-900">No AI Research Generated Yet</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Trigger automated deep company analysis to uncover market offering, SEO deficits, backlink targets, and strategic service recommendations.
                </p>
              </div>
              <button
                onClick={handleRunAiAnalysis}
                disabled={analyzingAi}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm"
              >
                <Sparkles className="w-4 h-4" />
                {analyzingAi ? "Analyzing Lead..." : "Generate AI Research Dossier"}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Executive Summary & Value Prop */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    <h3 className="text-sm font-bold text-slate-900">Executive Summary & Commercial Profile</h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    Model: {ai_research.model_used} • Confidence: {Math.round(ai_research.confidence_score * 100)}%
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {ai_research.executive_summary}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-100 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                    <span className="text-[10px] font-bold uppercase text-slate-400">Target Market</span>
                    <p className="text-slate-800 leading-normal">{ai_research.target_market}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                    <span className="text-[10px] font-bold uppercase text-slate-400">Value Proposition</span>
                    <p className="text-slate-800 leading-normal">{ai_research.value_proposition}</p>
                  </div>
                </div>
              </div>

              {/* Identified SEO Deficits & Opportunities */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    SEO Weaknesses & Technical Deficits
                  </h4>
                  <div className="space-y-2.5">
                    {(ai_research.seo_weaknesses || []).map((w, idx) => (
                      <div key={idx} className="p-3 bg-amber-50/40 border border-amber-100 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{w.issue}</span>
                          <span className="text-[9px] font-bold text-amber-700 bg-amber-100/80 px-1.5 py-0.2 rounded font-mono">
                            {w.severity}
                          </span>
                        </div>
                        <p className="text-slate-600 leading-normal">{w.details}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Backlink Opportunities */}
                <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <Layers className="w-4 h-4 text-indigo-500" />
                    Strategic Backlink Opportunities
                  </h4>
                  <div className="space-y-2.5">
                    {(ai_research.backlink_opportunities || []).map((b, idx) => (
                      <div key={idx} className="p-3 bg-indigo-50/40 border border-indigo-100 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{b.category}</span>
                          <span className="text-[9px] font-bold text-indigo-700 bg-indigo-100/80 px-1.5 py-0.2 rounded font-mono">
                            {b.relevance}
                          </span>
                        </div>
                        <p className="text-slate-600 leading-normal">{b.rationale}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommended Services */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Recommended Tailored Services
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(ai_research.recommended_services || []).map((s, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200/80 font-semibold rounded-lg text-xs flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Activity Timeline */}
      {activeTab === "timeline" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
          <h3 className="text-sm font-bold text-slate-900">Historical Activity Stream</h3>
          <div className="relative border-l-2 border-slate-200 pl-6 space-y-6 ml-2">
            {activities.length === 0 ? (
              <p className="text-xs text-slate-400">No activity recorded yet.</p>
            ) : (
              activities.map((a) => (
                <div key={a.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-white border-2 border-indigo-600" />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">{a.title}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono">
                      Actor: {a.actor} • Type: {a.activity_type}
                    </p>
                    {a.details && (
                      <pre className="bg-slate-50 p-2.5 rounded text-[10px] font-mono text-slate-600 overflow-x-auto max-w-xl">
                        {JSON.stringify(a.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Internal Notes */}
      {activeTab === "notes" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
          <h3 className="text-sm font-bold text-slate-900">Internal Reviewer Notes</h3>

          {/* Add Note Form */}
          <form onSubmit={handleAddNote} className="space-y-3">
            <textarea
              required
              rows={3}
              value={newNoteContent}
              onChange={(e) => setNewNoteContent(e.target.value)}
              placeholder="Add observation, qualification reasoning, or next steps..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submittingNote}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm"
              >
                {submittingNote ? "Saving..." : "Add Note"}
              </button>
            </div>
          </form>

          {/* Notes List */}
          <div className="space-y-3 pt-4 border-t border-slate-100">
            {notes.length === 0 ? (
              <p className="text-xs text-slate-400">No notes added yet.</p>
            ) : (
              notes.map((n) => (
                <div key={n.id} className="p-3 bg-slate-50 border border-slate-200/60 rounded-lg space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-slate-800">{n.author}</span>
                    <span className="text-slate-400 font-mono">{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-slate-700 whitespace-pre-wrap">{n.content}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-12 text-center text-slate-400 text-sm">Loading lead profile...</div>}>
      <LeadDetailContent params={params} />
    </Suspense>
  );
}
