"use client";

import { useEffect, useState, useMemo } from "react";
import {
  getCompanyCompetitors,
  discoverCompetitors,
  addCompanyCompetitor,
  updateCompanyCompetitor,
  runCompetitiveAnalysis,
  getCompanyCompetitiveRuns,
  getCompanyCompetitiveOverview,
  CompetitorResponse,
  CompetitorCandidate,
  CompetitiveAnalysisRunResponse,
  CompetitiveOverviewResponse,
  ContentGapItem,
  TechnicalGapItem,
  InternalLinkingGapItem,
  PublisherPROpportunityItem,
  CompetitiveRecommendation
} from "@/lib/api";
import {
  Swords,
  Search,
  Plus,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Layers,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  FileText,
  Code,
  Link as LinkIcon,
  Newspaper,
  Target,
  Sparkles,
  Info,
  Calendar,
  Building2,
  ChevronRight,
  Eye,
  AlertCircle
} from "lucide-react";

export default function CompetitiveIntelligencePage() {
  const [companies, setCompanies] = useState<Array<{ id: string; name: string; domain: string; industry?: string }>>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [isLoadingCompanies, setIsLoadingCompanies] = useState<boolean>(true);

  // Overview and Competitors State
  const [overview, setOverview] = useState<CompetitiveOverviewResponse | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorResponse[]>([]);
  const [selectedCompetitorId, setSelectedCompetitorId] = useState<string>("");
  const [activeRun, setActiveRun] = useState<CompetitiveAnalysisRunResponse | null>(null);
  const [historicalRuns, setHistoricalRuns] = useState<CompetitiveAnalysisRunResponse[]>([]);

  // Discovery State
  const [candidates, setCandidates] = useState<CompetitorCandidate[]>([]);
  const [isDiscovering, setIsDiscovering] = useState<boolean>(false);
  const [showDiscoveryModal, setShowDiscoveryModal] = useState<boolean>(false);

  // Add Competitor State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newCompName, setNewCompName] = useState<string>("");
  const [newCompDomain, setNewCompDomain] = useState<string>("");
  const [newCompTier, setNewCompTier] = useState<string>("DIRECT");
  const [newCompNotes, setNewCompNotes] = useState<string>("");

  // Loading & Execution States
  const [isLoadingOverview, setIsLoadingOverview] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

  // Active Tab
  const [activeTab, setActiveTab] = useState<"overview" | "content_gaps" | "technical_gaps" | "internal_linking" | "backlinks" | "digital_pr" | "recommendations" | "history">("overview");

  // Load Companies on mount
  useEffect(() => {
    async function fetchCompaniesList() {
      setIsLoadingCompanies(true);
      try {
        const res = await fetch("http://localhost:8000/companies?limit=100");
        if (res.ok) {
          const data = await res.json();
          const mapped = (data.items || data || []).map((c: any) => ({
            id: c.id,
            name: c.company_name || c.name || "Unnamed Prospect",
            domain: c.canonical_domain || c.website_url || "",
            industry: c.industry || "General"
          }));
          setCompanies(mapped);
          if (mapped.length > 0 && !selectedCompanyId) {
            setSelectedCompanyId(mapped[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to fetch companies:", err);
      } finally {
        setIsLoadingCompanies(false);
      }
    }
    fetchCompaniesList();
  }, []);

  // Fetch competitive data when selected company changes
  useEffect(() => {
    if (!selectedCompanyId) return;

    async function loadCompanyCompetitiveData() {
      setIsLoadingOverview(true);
      setActionErrorMessage(null);
      try {
        const [overviewData, compsData, runsData] = await Promise.all([
          getCompanyCompetitiveOverview(selectedCompanyId).catch(() => null),
          getCompanyCompetitors(selectedCompanyId).catch(() => []),
          getCompanyCompetitiveRuns(selectedCompanyId, 15).catch(() => [])
        ]);

        setOverview(overviewData);
        setCompetitors(compsData);
        setHistoricalRuns(runsData);

        if (compsData.length > 0 && !selectedCompetitorId) {
          setSelectedCompetitorId(compsData[0].id);
        } else if (compsData.length === 0) {
          setSelectedCompetitorId("");
        }

        if (overviewData?.latest_run) {
          setActiveRun(overviewData.latest_run);
        } else if (runsData.length > 0) {
          setActiveRun(runsData[0]);
        } else {
          setActiveRun(null);
        }
      } catch (err: any) {
        setActionErrorMessage(err.message || "Failed to load competitive intelligence data");
      } finally {
        setIsLoadingOverview(false);
      }
    }

    loadCompanyCompetitiveData();
  }, [selectedCompanyId]);

  // Handle Discover Competitors
  const handleDiscover = async () => {
    if (!selectedCompanyId) return;
    setIsDiscovering(true);
    setActionErrorMessage(null);
    try {
      const results = await discoverCompetitors(selectedCompanyId, 8, false);
      setCandidates(results);
      setShowDiscoveryModal(true);
      if (results.length === 0) {
        setActionSuccessMessage("No new peer companies matched topical/industry criteria in database.");
      }
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to discover competitors");
    } finally {
      setIsDiscovering(false);
    }
  };

  // Handle Add Candidate to Tracked Competitors
  const handleTrackCandidate = async (cand: CompetitorCandidate) => {
    try {
      await addCompanyCompetitor(selectedCompanyId, {
        competitor_name: cand.company_name,
        competitor_domain: cand.canonical_domain,
        competitor_company_id: cand.company_id || undefined,
        relevance_tier: cand.relevance_tier,
        relevance_score: cand.relevance_score,
        discovery_method: "INDUSTRY_TOPICAL_OVERLAP",
        notes: `Auto-discovered via ${cand.overlap_evidence.reasons?.join("; ") || "topical overlap"}`
      });
      // Refresh competitors
      const updated = await getCompanyCompetitors(selectedCompanyId);
      setCompetitors(updated);
      setSelectedCompetitorId(updated[updated.length - 1]?.id || "");
      setActionSuccessMessage(`Added ${cand.company_name} to tracked competitors.`);
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to track competitor");
    }
  };

  // Handle Add Competitor Manually
  const handleManualAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompDomain) return;
    try {
      const added = await addCompanyCompetitor(selectedCompanyId, {
        competitor_name: newCompName || newCompDomain.split(".")[0],
        competitor_domain: newCompDomain,
        relevance_tier: newCompTier,
        relevance_score: newCompTier === "DIRECT" ? 0.90 : 0.70,
        discovery_method: "MANUAL",
        notes: newCompNotes
      });
      setShowAddModal(false);
      setNewCompName("");
      setNewCompDomain("");
      setNewCompNotes("");
      const updated = await getCompanyCompetitors(selectedCompanyId);
      setCompetitors(updated);
      setSelectedCompetitorId(added.id);
      setActionSuccessMessage(`Successfully tracked competitor ${added.competitor_domain}`);
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to add competitor");
    }
  };

  // Handle Run Comparative Analysis
  const handleRunAnalysis = async () => {
    if (!selectedCompanyId || !selectedCompetitorId) {
      setActionErrorMessage("Please select a tracked competitor to compare against.");
      return;
    }
    setIsAnalyzing(true);
    setActionErrorMessage(null);
    setActionSuccessMessage(null);
    try {
      const run = await runCompetitiveAnalysis(selectedCompanyId, {
        competitor_id: selectedCompetitorId,
        sync_to_sales_opportunities: true
      });
      setActiveRun(run);
      // Refresh runs list and overview
      const [overviewData, runsData] = await Promise.all([
        getCompanyCompetitiveOverview(selectedCompanyId),
        getCompanyCompetitiveRuns(selectedCompanyId, 15)
      ]);
      setOverview(overviewData);
      setHistoricalRuns(runsData);
      setActionSuccessMessage(`Analysis completed against ${run.competitor_domain}. Discovered ${run.content_gaps.length} content gaps and ${run.technical_gaps.length} technical disparities.`);
    } catch (err: any) {
      setActionErrorMessage(err.message || "Analysis execution failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedProspect = useMemo(() => {
    return companies.find((c) => c.id === selectedCompanyId);
  }, [companies, selectedCompanyId]);

  const selectedCompetitor = useMemo(() => {
    return competitors.find((c) => c.id === selectedCompetitorId);
  }, [competitors, selectedCompetitorId]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-16">
      {/* Top Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="p-2 bg-indigo-600 rounded-lg text-white shadow-xs">
                  <Swords className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-xl font-bold tracking-tight text-slate-900">
                    Advanced Competitive SEO Intelligence
                  </h1>
                  <p className="text-xs text-slate-500">
                    Evidence-based competitor discovery, side-by-side crawl comparison, and GrokxSEO gap mapping
                  </p>
                </div>
              </div>
            </div>

            {/* Prospect Selector & Action Trigger */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg border border-slate-200">
                <Building2 className="w-4 h-4 text-slate-500 ml-2" />
                <select
                  className="bg-transparent text-sm font-medium text-slate-800 pr-8 py-1 focus:outline-hidden"
                  value={selectedCompanyId}
                  onChange={(e) => setSelectedCompanyId(e.target.value)}
                  disabled={isLoadingCompanies}
                >
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.domain || "no-domain"})
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleDiscover}
                disabled={isDiscovering || !selectedCompanyId}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                {isDiscovering ? "Discovering..." : "Discover Candidates"}
              </button>

              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Competitor
              </button>

              <button
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || !selectedCompetitorId}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-xs transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? "animate-spin" : ""}`} />
                {isAnalyzing ? "Running Analysis..." : "Run Side-by-Side Analysis"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Notifications */}
        {actionSuccessMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>{actionSuccessMessage}</span>
            </div>
            <button onClick={() => setActionSuccessMessage(null)} className="text-emerald-600 font-bold hover:underline">Dismiss</button>
          </div>
        )}

        {actionErrorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>{actionErrorMessage}</span>
            </div>
            <button onClick={() => setActionErrorMessage(null)} className="text-rose-600 font-bold hover:underline">Dismiss</button>
          </div>
        )}

        {/* Executive Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Tracked Peers</span>
              <Building2 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">{competitors.length}</span>
              <span className="text-xs text-slate-500">competitors</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {competitors.filter((c) => c.relevance_tier === "DIRECT").length} direct rivals
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Topical Gaps</span>
              <FileText className="w-4 h-4 text-blue-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-blue-700">{activeRun?.content_gaps?.length ?? 0}</span>
              <span className="text-xs text-slate-500">uncovered topics</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Intent-tagged search gaps
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Technical Gaps</span>
              <Code className="w-4 h-4 text-amber-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-700">{activeRun?.technical_gaps?.length ?? 0}</span>
              <span className="text-xs text-slate-500">audit deficits</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Crawl & structure disparities
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Digital PR Placements</span>
              <Newspaper className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-700">{activeRun?.publisher_opportunities?.length ?? 0}</span>
              <span className="text-xs text-slate-500">inventory matches</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Verified media outlets
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Action Items</span>
              <Target className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-indigo-700">{activeRun?.prioritized_recommendations?.length ?? 0}</span>
              <span className="text-xs text-slate-500">GrokxSEO actions</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Prioritized by potential ROI
            </p>
          </div>
        </div>

        {/* Competitor Selector & Comparison Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Active Competitor Target:</span>
              {competitors.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {competitors.map((c) => {
                    const isSelected = c.id === selectedCompetitorId;
                    return (
                      <button
                        key={c.id}
                        onClick={() => setSelectedCompetitorId(c.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border transition-colors ${
                          isSelected
                            ? "bg-indigo-600 text-white border-indigo-600 shadow-xs"
                            : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                        }`}
                      >
                        <span>{c.competitor_name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          isSelected ? "bg-indigo-700 text-indigo-100" : "bg-slate-200 text-slate-600"
                        }`}>
                          {c.relevance_tier}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <span className="text-xs text-slate-400 italic">No competitors tracked yet. Click &quot;Discover Candidates&quot; or &quot;Add Competitor&quot;.</span>
              )}
            </div>

            {selectedCompetitor && (
              <div className="text-xs text-slate-500 flex items-center gap-2">
                <span>Domain: <strong className="text-slate-800">{selectedCompetitor.competitor_domain}</strong></span>
                <span>•</span>
                <span>Relevance: <strong className="text-slate-800">{Math.round(selectedCompetitor.relevance_score * 100)}%</strong></span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="border-b border-slate-200">
          <nav className="flex space-x-6 overflow-x-auto" aria-label="Tabs">
            {[
              { id: "overview", label: "Executive Overview", icon: Layers },
              { id: "content_gaps", label: `Topical Gaps (${activeRun?.content_gaps?.length ?? 0})`, icon: FileText },
              { id: "technical_gaps", label: `Technical SEO (${activeRun?.technical_gaps?.length ?? 0})`, icon: Code },
              { id: "internal_linking", label: `Silos & Linking (${activeRun?.internal_linking_gaps?.length ?? 0})`, icon: LinkIcon },
              { id: "backlinks", label: "Authority & Backlinks", icon: TrendingUp },
              { id: "digital_pr", label: `Digital PR (${activeRun?.publisher_opportunities?.length ?? 0})`, icon: Newspaper },
              { id: "recommendations", label: `Recommendations (${activeRun?.prioritized_recommendations?.length ?? 0})`, icon: Target },
              { id: "history", label: `Runs History (${historicalRuns.length})`, icon: Calendar },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
                    isActive
                      ? "border-indigo-600 text-indigo-600 font-bold"
                      : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* TAB 1: EXECUTIVE OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {activeRun ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Side-by-Side Comparison Card */}
                <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
                  <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                    <div>
                      <h2 className="text-base font-bold text-slate-900">Side-by-Side Competitive Assessment</h2>
                      <p className="text-xs text-slate-500">
                        Observed crawl signals between <span className="font-semibold text-slate-700">{activeRun.company_name}</span> and <span className="font-semibold text-slate-700">{activeRun.competitor_name}</span>
                      </p>
                    </div>
                    <span className="text-[11px] px-2.5 py-1 bg-slate-100 text-slate-600 rounded-full font-medium">
                      Analyzed {new Date(activeRun.analyzed_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Side-by-side Columns */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Prospect Column */}
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Prospect (Client)</span>
                        <span className="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-semibold">TARGET</span>
                      </div>
                      <div className="text-sm font-bold text-slate-900">{activeRun.company_name}</div>
                      <div className="text-xs text-slate-500 font-mono">{activeRun.summary_findings?.prospect_domain || selectedProspect?.domain || "N/A"}</div>
                      
                      <div className="pt-2 border-t border-slate-200 space-y-2 text-xs">
                        <div className="flex justify-between text-slate-600">
                          <span>Word Count:</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.prospect_word_count ?? "Unknown"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>H1 Tags:</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.prospect_h1_count ?? "0"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>Subheadings (H2):</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.prospect_h2_count ?? "0"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>Schema Rich Snippets:</span>
                          <span className={`font-semibold ${activeRun.summary_findings?.prospect_has_schema ? "text-emerald-700" : "text-rose-700"}`}>
                            {activeRun.summary_findings?.prospect_has_schema ? "Detected" : "Missing"}
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>SSL Protocol:</span>
                          <span className={`font-semibold ${activeRun.summary_findings?.prospect_https ? "text-emerald-700" : "text-rose-700"}`}>
                            {activeRun.summary_findings?.prospect_https ? "HTTPS Secure" : "HTTP Insecure"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Competitor Column */}
                    <div className="p-4 bg-indigo-50/50 rounded-lg border border-indigo-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider">Tracked Rival</span>
                        <span className="text-[10px] px-2 py-0.5 bg-indigo-200 text-indigo-900 rounded font-semibold">BENCHMARK</span>
                      </div>
                      <div className="text-sm font-bold text-slate-900">{activeRun.competitor_name}</div>
                      <div className="text-xs text-indigo-700 font-mono">{activeRun.competitor_domain}</div>
                      
                      <div className="pt-2 border-t border-indigo-200 space-y-2 text-xs">
                        <div className="flex justify-between text-slate-600">
                          <span>Word Count:</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.competitor_word_count ?? "Unknown"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>H1 Tags:</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.competitor_h1_count ?? "0"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>Subheadings (H2):</span>
                          <span className="font-semibold text-slate-800">{activeRun.summary_findings?.competitor_h2_count ?? "0"}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>Schema Rich Snippets:</span>
                          <span className={`font-semibold ${activeRun.summary_findings?.competitor_has_schema ? "text-emerald-700" : "text-slate-600"}`}>
                            {activeRun.summary_findings?.competitor_has_schema ? "Present" : "None"}
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>SSL Protocol:</span>
                          <span className="font-semibold text-emerald-700">HTTPS Secure</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Key Disparity Summary */}
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <h3 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-amber-600" />
                      Strategic SEO Diagnosis
                    </h3>
                    <p className="mt-1 text-xs text-amber-800 leading-relaxed">
                      {activeRun.summary_findings?.differential_verdict || 
                        `Identified ${activeRun.content_gaps.length} critical topical gaps and ${activeRun.technical_gaps.length} structural deficits where ${activeRun.competitor_name} maintains clear search crawler advantages.`}
                    </p>
                  </div>
                </div>

                {/* Right Column: Top Recommendations Preview */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <h3 className="text-sm font-bold text-slate-900">Highest-Impact Actions</h3>
                    <button onClick={() => setActiveTab("recommendations")} className="text-xs text-indigo-600 font-semibold hover:underline">
                      View All ({activeRun.prioritized_recommendations.length})
                    </button>
                  </div>

                  <div className="space-y-3">
                    {activeRun.prioritized_recommendations.slice(0, 4).map((rec) => (
                      <div key={rec.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 uppercase">
                            {rec.service}
                          </span>
                          <span className="text-xs font-bold text-indigo-700">
                            Score: {Math.round(rec.priority_score)}
                          </span>
                        </div>
                        <div className="text-xs font-bold text-slate-900">{rec.title}</div>
                        <p className="text-[11px] text-slate-600 line-clamp-2">{rec.rationale}</p>
                      </div>
                    ))}
                  </div>

                  {activeRun.data_limitations && activeRun.data_limitations.length > 0 && (
                    <div className="pt-3 border-t border-slate-100">
                      <div className="flex items-start gap-1.5 text-[11px] text-slate-500">
                        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span>Data Limitations: {activeRun.data_limitations[0]}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-4">
                <Swords className="w-12 h-12 text-slate-300 mx-auto" />
                <h3 className="text-base font-bold text-slate-900">No Comparative Analysis Run Yet</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Select a tracked competitor above and click &quot;Run Side-by-Side Analysis&quot; to execute multi-dimensional crawl, content gap, and technical SEO comparisons.
                </p>
                {competitors.length > 0 ? (
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing}
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-xs"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? "animate-spin" : ""}`} />
                    Run Initial Analysis
                  </button>
                ) : (
                  <button
                    onClick={handleDiscover}
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100"
                  >
                    <Search className="w-3.5 h-3.5" />
                    Discover Competitor Candidates
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: TOPICAL CONTENT GAPS */}
        {activeTab === "content_gaps" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Keyword & Topical Content Gaps</h2>
                <p className="text-xs text-slate-500">
                  Search intent coverage differences between prospect and rival. Uncovered topics represent high-intent organic ranking opportunities.
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
                {activeRun?.content_gaps?.length ?? 0} Opportunities Detected
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <th className="py-3 px-4">Topic / Keyword Cluster</th>
                    <th className="py-3 px-3">Search Intent</th>
                    <th className="py-3 px-4">Competitor Coverage</th>
                    <th className="py-3 px-4">Prospect Coverage</th>
                    <th className="py-3 px-3">Recommended Service</th>
                    <th className="py-3 px-4">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeRun?.content_gaps && activeRun.content_gaps.length > 0 ? (
                    activeRun.content_gaps.map((gap, idx) => {
                      const intentColors: Record<string, string> = {
                        INFORMATIONAL: "bg-blue-100 text-blue-800 border-blue-200",
                        COMMERCIAL: "bg-amber-100 text-amber-800 border-amber-200",
                        TRANSACTIONAL: "bg-emerald-100 text-emerald-800 border-emerald-200",
                        NAVIGATIONAL: "bg-purple-100 text-purple-800 border-purple-200"
                      };
                      return (
                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-4 font-bold text-slate-900">{gap.topic}</td>
                          <td className="py-3 px-3">
                            <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${intentColors[gap.search_intent] || "bg-slate-100 text-slate-700"}`}>
                              {gap.search_intent}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-700 font-medium">{gap.competitor_coverage}</td>
                          <td className="py-3 px-4 text-rose-600 font-medium">{gap.prospect_coverage}</td>
                          <td className="py-3 px-3 font-semibold text-indigo-700">{gap.recommended_service}</td>
                          <td className="py-3 px-4 text-slate-600">{gap.recommended_action}</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400">
                        No content gaps identified for this analysis run.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: TECHNICAL SEO GAPS */}
        {activeTab === "technical_gaps" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeRun?.technical_gaps && activeRun.technical_gaps.length > 0 ? (
                activeRun.technical_gaps.map((tech, idx) => {
                  const severityBadge: Record<string, string> = {
                    HIGH: "bg-rose-100 text-rose-800 border-rose-200",
                    MEDIUM: "bg-amber-100 text-amber-800 border-amber-200",
                    LOW: "bg-blue-100 text-blue-800 border-blue-200"
                  };
                  return (
                    <div key={idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900">{tech.metric_or_feature}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${severityBadge[tech.severity] || "bg-slate-100 text-slate-700"}`}>
                          {tech.severity} SEVERITY
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold uppercase">Prospect State</span>
                          <p className="font-semibold text-rose-700 mt-0.5">{tech.prospect_state}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold uppercase">Competitor State</span>
                          <p className="font-semibold text-emerald-700 mt-0.5">{tech.competitor_state}</p>
                        </div>
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed">{tech.gap_description}</p>

                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                        <span className="font-semibold text-indigo-700">{tech.recommended_service}</span>
                        <span className="text-slate-500 font-medium">{tech.recommended_action}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="col-span-2 bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400">
                  No technical SEO disparities identified for this run.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: INTERNAL LINKING & TOPICAL SILOS */}
        {activeTab === "internal_linking" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-6">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Internal Linking & Silo Architecture Analysis</h2>
              <p className="text-xs text-slate-500">
                Evaluating topical cluster depth, orphan risk, and internal link equity distribution against the competitor benchmark.
              </p>
            </div>

            <div className="space-y-4">
              {activeRun?.internal_linking_gaps && activeRun.internal_linking_gaps.length > 0 ? (
                activeRun.internal_linking_gaps.map((silo, idx) => (
                  <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-slate-900">{silo.silo_topic}</h3>
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded">
                        {silo.recommended_service}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-white rounded border border-rose-200">
                        <span className="text-[10px] font-bold text-rose-600 uppercase">Prospect Architecture Issue</span>
                        <p className="text-slate-800 mt-1">{silo.prospect_issue}</p>
                      </div>
                      <div className="p-3 bg-white rounded border border-emerald-200">
                        <span className="text-[10px] font-bold text-emerald-600 uppercase">Competitor Structural Advantage</span>
                        <p className="text-slate-800 mt-1">{silo.competitor_advantage}</p>
                      </div>
                    </div>

                    <div className="p-3 bg-indigo-50 border border-indigo-100 rounded text-xs text-indigo-900">
                      <strong>Remediation Strategy: </strong>{silo.recommended_action}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No internal linking deficits identified.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: BACKLINK & AUTHORITY GAP */}
        {activeTab === "backlinks" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-6">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Backlink & Referring Domain Gap Analysis</h2>
              <p className="text-xs text-slate-500">
                Comparing domain authority and backlink metrics using authorized third-party SEO providers (Moz, Ahrefs, Semrush).
              </p>
            </div>

            {/* Provider Configuration / Non-Fabrication Notice */}
            {!activeRun?.backlink_gaps?.is_provider_configured && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900 space-y-1">
                  <strong>Strict Non-Fabrication Safeguard Enforced:</strong>
                  <p>
                    Third-party backlink provider APIs (Moz / Ahrefs) are not configured or returned no authorized live metrics for this competitor domain. 
                    Authority values are displayed as <em>Unknown (None)</em> rather than fabricated figures or assumed zeros.
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center">
                <span className="text-xs font-medium text-slate-500 uppercase">Prospect Domain Authority (DA)</span>
                <div className="mt-2 text-2xl font-bold text-slate-800">
                  {activeRun?.backlink_gaps?.prospect_da !== null && activeRun?.backlink_gaps?.prospect_da !== undefined
                    ? activeRun.backlink_gaps.prospect_da
                    : "Unknown"}
                </div>
                <span className="text-[11px] text-slate-400 font-mono">{activeRun?.backlink_gaps?.prospect_domain || "N/A"}</span>
              </div>

              <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-200 text-center">
                <span className="text-xs font-medium text-indigo-700 uppercase">Competitor Domain Authority (DA)</span>
                <div className="mt-2 text-2xl font-bold text-indigo-900">
                  {activeRun?.backlink_gaps?.competitor_da !== null && activeRun?.backlink_gaps?.competitor_da !== undefined
                    ? activeRun.backlink_gaps.competitor_da
                    : "Unknown"}
                </div>
                <span className="text-[11px] text-indigo-700 font-mono">{activeRun?.backlink_gaps?.competitor_domain || "N/A"}</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center">
                <span className="text-xs font-medium text-slate-500 uppercase">Authority Differential</span>
                <div className="mt-2 text-2xl font-bold text-slate-800">
                  {activeRun?.backlink_gaps?.da_differential !== null && activeRun?.backlink_gaps?.da_differential !== undefined
                    ? `${activeRun.backlink_gaps.da_differential > 0 ? "+" : ""}${activeRun.backlink_gaps.da_differential}`
                    : "Unknown"}
                </div>
                <span className="text-[11px] text-slate-400">Verified difference</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: DIGITAL PR & PUBLISHER OPPORTUNITIES */}
        {activeTab === "digital_pr" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Digital PR & Placement Opportunities</h2>
                <p className="text-xs text-slate-500">
                  Pre-vetted publishers and media outlets from ProspectOS inventory matching prospect industry and audience focus.
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-200">
                {activeRun?.publisher_opportunities?.length ?? 0} Inventory Matches
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <th className="py-3 px-4">Publisher Outlet</th>
                    <th className="py-3 px-3">Domain</th>
                    <th className="py-3 px-3">Audience Focus</th>
                    <th className="py-3 px-3">Observed Metrics</th>
                    <th className="py-3 px-3">Placement Cost</th>
                    <th className="py-3 px-3">Strategy</th>
                    <th className="py-3 px-4">Relevance Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeRun?.publisher_opportunities && activeRun.publisher_opportunities.length > 0 ? (
                    activeRun.publisher_opportunities.map((pub) => (
                      <tr key={pub.publisher_id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900">{pub.publisher_name}</td>
                        <td className="py-3 px-3 font-mono text-slate-600">{pub.canonical_domain}</td>
                        <td className="py-3 px-3 font-medium text-slate-700">{pub.audience_focus}</td>
                        <td className="py-3 px-3">
                          <span className="font-semibold text-slate-800">
                            DA {pub.da ?? "—"} • DR {pub.dr ?? "—"}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-semibold text-slate-900">
                          {pub.price ? `${pub.currency || "$"} ${pub.price.toLocaleString()}` : "Contact for Rate"}
                        </td>
                        <td className="py-3 px-3 font-bold text-indigo-700">{pub.recommended_service}</td>
                        <td className="py-3 px-4 text-slate-600">{pub.relevance_rationale}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400">
                        No publisher opportunities matched for this industry.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 7: PRIORITIZED RECOMMENDATIONS */}
        {activeTab === "recommendations" && (
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Prioritized GrokxSEO Action Plan</h2>
                <p className="text-xs text-slate-500">
                  Synthesized recommendations mapped to existing GrokxSEO service offerings. Scored transparently by impact, effort, and confidence.
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-md border border-indigo-200">
                {activeRun?.prioritized_recommendations?.length ?? 0} Recommendations
              </span>
            </div>

            <div className="space-y-3">
              {activeRun?.prioritized_recommendations && activeRun.prioritized_recommendations.length > 0 ? (
                activeRun.prioritized_recommendations.map((rec) => (
                  <div key={rec.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800 uppercase">
                          {rec.service}
                        </span>
                        <h3 className="text-sm font-bold text-slate-900">{rec.title}</h3>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          Effort: {rec.effort}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          Impact: {rec.impact}
                        </span>
                        <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-600 text-white">
                          Priority {Math.round(rec.priority_score)}/100
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div>
                        <strong className="text-slate-700">Strategic Rationale:</strong>
                        <p className="text-slate-600 mt-0.5 leading-relaxed">{rec.rationale}</p>
                      </div>
                      <div>
                        <strong className="text-slate-700">Recommended Execution Action:</strong>
                        <p className="text-indigo-950 font-medium mt-0.5 leading-relaxed">{rec.action}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400 text-xs">
                  No prioritized recommendations available.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 8: HISTORICAL RUNS */}
        {activeTab === "history" && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <h2 className="text-sm font-bold text-slate-900">Historical Competitive Analysis Runs</h2>
              <p className="text-xs text-slate-500">
                Audited timeline of past competitive intelligence evaluations for this prospect.
              </p>
            </div>

            <div className="divide-y divide-slate-100">
              {historicalRuns.map((r) => (
                <div key={r.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">vs {r.competitor_name}</span>
                      <span className="text-xs font-mono text-slate-500">({r.competitor_domain})</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold uppercase">
                        {r.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {r.content_gaps.length} content gaps • {r.technical_gaps.length} technical gaps • {r.publisher_opportunities.length} PR opportunities
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-slate-400">{new Date(r.analyzed_at).toLocaleString()}</span>
                    <button
                      onClick={() => {
                        setActiveRun(r);
                        setActiveTab("overview");
                      }}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors flex items-center gap-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* DISCOVERY MODAL */}
      {showDiscoveryModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-xl overflow-hidden max-h-[85vh] flex flex-col">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Discovered Competitor Candidates</h3>
                <p className="text-xs text-slate-500">
                  Peers identified via verified database industry categorization and keyword overlap
                </p>
              </div>
              <button
                onClick={() => setShowDiscoveryModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {candidates.length > 0 ? (
                candidates.map((cand, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-slate-900">{cand.company_name}</h4>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold uppercase">
                          {cand.relevance_tier} ({Math.round(cand.relevance_score * 100)}%)
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">{cand.canonical_domain}</p>
                      <p className="text-[11px] text-slate-600 mt-1">
                        {cand.overlap_evidence.reasons?.join("; ") || "Verified topical match"}
                      </p>
                    </div>

                    <button
                      onClick={() => handleTrackCandidate(cand)}
                      className="px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 whitespace-nowrap"
                    >
                      Track Rival
                    </button>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No new candidates discovered for this prospect.
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setShowDiscoveryModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD COMPETITOR MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-xl overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">Add Competitor Relationship</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-sm">✕</button>
            </div>

            <form onSubmit={handleManualAdd} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Competitor Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Media Corp"
                  value={newCompName}
                  onChange={(e) => setNewCompName(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Canonical Domain</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. acmemedia.com"
                  value={newCompDomain}
                  onChange={(e) => setNewCompDomain(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Relevance Tier</label>
                <select
                  value={newCompTier}
                  onChange={(e) => setNewCompTier(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-indigo-500"
                >
                  <option value="DIRECT">DIRECT (Primary Market Competitor)</option>
                  <option value="INDIRECT">INDIRECT (Adjacent Niche / Solution)</option>
                  <option value="TOPICAL_PEER">TOPICAL_PEER (Shared Content Audience)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Notes / Rationale</label>
                <textarea
                  rows={3}
                  placeholder="Optional context about this competitor relationship..."
                  value={newCompNotes}
                  onChange={(e) => setNewCompNotes(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-indigo-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-200 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-xs"
                >
                  Add Competitor
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
