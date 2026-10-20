"use client";

import { useEffect, useState } from "react";
import {
  api,
  NLQueryParseResponse,
  ScrapingTemplate,
  SourceAdapterInfo,
  DiscoveryJobDetail
} from "@/lib/api";
import {
  Search,
  Loader2,
  Globe,
  Building2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Filter,
  Layers,
  Activity,
  Play,
  RotateCcw,
  Ban,
  ExternalLink,
  ChevronRight,
  HardDrive,
  Database,
  Sliders,
  Check,
  Zap
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function DiscoveryPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"nl_search" | "templates" | "jobs" | "sources" | "intake">("nl_search");

  // NL Search States
  const [nlQuery, setNlQuery] = useState(
    "Find 50 new companies in Mexico that have weak SEO, operate in the e-commerce industry, have an accessible website, and could benefit from technical SEO, link building, and Digital PR."
  );
  const [isInterpreting, setIsInterpreting] = useState(false);
  const [parsedCriteria, setParsedCriteria] = useState<NLQueryParseResponse | null>(null);

  // Editable Search Configuration
  const [targetCount, setTargetCount] = useState(50);
  const [country, setCountry] = useState("Mexico");
  const [city, setCity] = useState("");
  const [industry, setIndustry] = useState("E-commerce");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [minOppScore, setMinOppScore] = useState(40);
  const [maxOppScore, setMaxOppScore] = useState(100);
  const [desiredService, setDesiredService] = useState("Technical SEO & Backlinks");
  const [minDataQuality, setMinDataQuality] = useState("MEDIUM");
  const [includePrevious, setIncludePrevious] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>(["curated_directory", "duckduckgo_search"]);

  // Job Submission States
  const [isLaunchingJob, setIsLaunchingJob] = useState(false);
  const [launchResult, setLaunchResult] = useState<{ job_id: string; job_name: string; status: string } | null>(null);
  const [launchError, setLaunchError] = useState<string | null>(null);

  // Templates
  const [templates, setTemplates] = useState<ScrapingTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // Sources
  const [sources, setSources] = useState<SourceAdapterInfo[]>([]);
  const [loadingSources, setLoadingSources] = useState(false);

  // Jobs Dashboard
  const [jobs, setJobs] = useState<DiscoveryJobDetail[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [actionLoadingJobId, setActionLoadingJobId] = useState<string | null>(null);

  // Direct Intake Form States
  const [intakeDomain, setIntakeDomain] = useState("");
  const [intakeName, setIntakeName] = useState("");
  const [intakeIndustry, setIntakeIndustry] = useState("");
  const [triggerAnalysis, setTriggerAnalysis] = useState(true);
  const [isIntakeSubmitting, setIsIntakeSubmitting] = useState(false);
  const [intakeResult, setIntakeResult] = useState<any>(null);
  const [intakeError, setIntakeError] = useState<string | null>(null);

  // Initial Load
  useEffect(() => {
    loadTemplates();
    loadSources();
    loadJobs();
  }, []);

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const data = await api.getDiscoveryTemplates();
      setTemplates(data);
    } catch (err) {
      console.error("Failed to load templates", err);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadSources = async () => {
    setLoadingSources(true);
    try {
      const data = await api.getDiscoverySources();
      setSources(data);
    } catch (err) {
      console.error("Failed to load sources", err);
    } finally {
      setLoadingSources(false);
    }
  };

  const loadJobs = async () => {
    setLoadingJobs(true);
    try {
      const data = await api.getDiscoveryJobs(undefined, 30);
      setJobs(data);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleInterpretQuery = async () => {
    if (!nlQuery.trim()) return;
    setIsInterpreting(true);
    setLaunchError(null);
    try {
      const res = await api.parseDiscoveryQuery(nlQuery.trim());
      setParsedCriteria(res);
      // Sync into editable parameters
      const c = res.interpreted_criteria;
      setTargetCount(c.target_count || 50);
      if (c.country) setCountry(c.country);
      if (c.city) setCity(c.city);
      if (c.industry) setIndustry(c.industry);
      if (c.website_url) setWebsiteUrl(c.website_url);
      if (c.min_opportunity_score !== undefined) setMinOppScore(c.min_opportunity_score);
      if (c.max_opportunity_score !== undefined) setMaxOppScore(c.max_opportunity_score);
      if (c.desired_services && c.desired_services.length > 0) setDesiredService(c.desired_services.join(", "));
      if (c.min_data_quality) setMinDataQuality(c.min_data_quality);
      if (c.include_previously_discovered !== undefined) setIncludePrevious(c.include_previously_discovered);
      if (res.source_strategy && res.source_strategy.length > 0) {
        setSelectedSources(res.source_strategy);
      }
    } catch (err: any) {
      setLaunchError(err.message || "Failed to interpret query with AI");
    } finally {
      setIsInterpreting(false);
    }
  };

  const handleLaunchDiscovery = async (templateId?: string) => {
    setIsLaunchingJob(true);
    setLaunchError(null);
    setLaunchResult(null);

    try {
      const payload = {
        query: nlQuery.trim() || undefined,
        target_count: Number(targetCount) || 50,
        country: country.trim() || undefined,
        city: city.trim() || undefined,
        industry: industry.trim() || undefined,
        website_url: websiteUrl.trim() || undefined,
        min_opportunity_score: Number(minOppScore),
        max_opportunity_score: Number(maxOppScore),
        desired_service: desiredService.trim() || undefined,
        template_id: templateId,
        source_preferences: selectedSources,
        include_previously_discovered: includePrevious,
        min_data_quality: minDataQuality
      };

      const res = await api.createDiscoveryJob(payload);
      setLaunchResult(res);
      setActiveTab("jobs");
      loadJobs();
    } catch (err: any) {
      setLaunchError(err.message || "Failed to launch discovery job");
    } finally {
      setIsLaunchingJob(false);
    }
  };

  const handleUseTemplate = (tmpl: ScrapingTemplate) => {
    setNlQuery(`Run ${tmpl.name} targeting ${tmpl.default_target_count} companies in ${tmpl.target_market} for ${tmpl.industry}`);
    setTargetCount(tmpl.default_target_count);
    setCountry(tmpl.target_market);
    setIndustry(tmpl.industry);
    setDesiredService(tmpl.recommended_services.join(", "));
    setSelectedSources(tmpl.sources);
    handleLaunchDiscovery(tmpl.id);
  };

  const handleCancelJob = async (jobId: string) => {
    setActionLoadingJobId(jobId);
    try {
      await api.cancelDiscoveryJob(jobId);
      await loadJobs();
    } catch (err: any) {
      alert(err.message || "Failed to cancel job");
    } finally {
      setActionLoadingJobId(null);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    setActionLoadingJobId(jobId);
    try {
      await api.retryDiscoveryJob(jobId);
      await loadJobs();
    } catch (err: any) {
      alert(err.message || "Failed to retry job");
    } finally {
      setActionLoadingJobId(null);
    }
  };

  const handleDirectIntake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intakeDomain.trim()) return;

    setIsIntakeSubmitting(true);
    setIntakeError(null);
    setIntakeResult(null);

    try {
      const res = await api.importCompany({
        domain: intakeDomain.trim(),
        company_name: intakeName.trim() || undefined,
        industry: intakeIndustry.trim() || undefined,
        trigger_analysis: triggerAnalysis
      });
      setIntakeResult(res);
    } catch (err: any) {
      setIntakeError(err.message || "Failed to intake prospect");
    } finally {
      setIsIntakeSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16 px-4 sm:px-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-bold bg-blue-100 text-blue-800 rounded">Module A</span>
            <span className="px-2 py-0.5 text-xs font-bold bg-purple-100 text-purple-800 rounded">AI Scraping Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 flex items-center mt-1">
            <Search className="w-7 h-7 mr-3 text-blue-600" /> Lead Discovery & Scraping Suite
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Autonomous multi-source lead scraping, live SEO analysis, CRM persistence, and Google Drive synchronization for GrokxSEO.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex flex-wrap rounded-lg bg-slate-100 p-1 border border-slate-200">
          <button
            onClick={() => setActiveTab("nl_search")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition flex items-center gap-1.5 ${
              activeTab === "nl_search"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" /> AI Search
          </button>
          <button
            onClick={() => setActiveTab("templates")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition flex items-center gap-1.5 ${
              activeTab === "templates"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Layers className="w-3.5 h-3.5" /> Templates ({templates.length})
          </button>
          <button
            onClick={() => {
              setActiveTab("jobs");
              loadJobs();
            }}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition flex items-center gap-1.5 ${
              activeTab === "jobs"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> Jobs Dashboard ({jobs.length})
          </button>
          <button
            onClick={() => setActiveTab("sources")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition flex items-center gap-1.5 ${
              activeTab === "sources"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Database className="w-3.5 h-3.5" /> Sources ({sources.length})
          </button>
          <button
            onClick={() => setActiveTab("intake")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition flex items-center gap-1.5 ${
              activeTab === "intake"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Globe className="w-3.5 h-3.5" /> Direct Intake
          </button>
        </div>
      </div>

      {/* TAB 1: Natural Language Lead Discovery */}
      {activeTab === "nl_search" && (
        <div className="space-y-6">
          {/* Natural Language Prompt Input */}
          <div className="bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-900 text-white p-6 sm:p-8 rounded-2xl shadow-xl border border-blue-800/40 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-400/30">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                  </div>
                  <h2 className="text-lg font-bold text-white tracking-wide">
                    Natural-Language Prospecting Prompt
                  </h2>
                </div>
                <span className="text-xs text-blue-200/80 font-mono">Octoparse-Style AI Query Extraction</span>
              </div>

              <p className="text-xs text-blue-100/90 leading-relaxed max-w-3xl">
                Enter your prospect criteria in plain English. ProspectOS will parse the geographic target, vertical, SEO thresholds, and source strategy, allowing you to fine-tune the execution criteria before launching.
              </p>

              <div className="relative">
                <textarea
                  rows={3}
                  value={nlQuery}
                  onChange={(e) => setNlQuery(e.target.value)}
                  placeholder="e.g. Find 50 new companies in Mexico with weak SEO and demand for backlinks..."
                  className="w-full bg-white/10 text-white placeholder-blue-200/50 border border-blue-400/30 rounded-xl p-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition resize-none font-medium"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2 text-xs text-blue-200">
                  <span className="font-semibold text-blue-300">Quick Samples:</span>
                  <button
                    onClick={() => setNlQuery("Find 50 new companies in Mexico that have weak SEO, operate in the e-commerce industry, have an accessible website, and could benefit from technical SEO, link building, and Digital PR.")}
                    className="underline hover:text-white transition"
                  >
                    Mexico E-commerce (50)
                  </button>
                  <span>•</span>
                  <button
                    onClick={() => setNlQuery("Discover 25 high-potential B2B SaaS companies in the United States with DR under 35 and missing schema metadata.")}
                    className="underline hover:text-white transition"
                  >
                    USA SaaS (25)
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleInterpretQuery}
                    disabled={isInterpreting || !nlQuery.trim()}
                    className="inline-flex items-center px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-400 text-white font-semibold text-xs transition shadow-lg disabled:opacity-50"
                  >
                    {isInterpreting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing with AI...
                      </>
                    ) : (
                      <>
                        <Sliders className="w-4 h-4 mr-2" />
                        Interpret & Structure Criteria
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* AI Explanation Banner */}
          {parsedCriteria && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-900 flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <div className="font-bold text-sm text-emerald-950">
                  Interpreted: {parsedCriteria.suggested_job_name} (Confidence: {Math.round(parsedCriteria.confidence * 100)}%)
                </div>
                <p className="text-emerald-800">{parsedCriteria.explanation}</p>
                <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px]">
                  <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                    Sources: {parsedCriteria.source_strategy.join(", ")}
                  </span>
                  <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                    Target Fields: {parsedCriteria.extraction_targets.slice(0, 5).join(", ")}...
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Structured & Editable Search Configuration */}
          <div className="bg-white shadow-sm rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Sliders className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">Configurable Discovery Parameters</h3>
              </div>
              <span className="text-xs text-slate-500">Edit values before job execution</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Target Qualified Leads *
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={targetCount}
                  onChange={(e) => setTargetCount(Number(e.target.value))}
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-semibold"
                />
                <p className="mt-1 text-[11px] text-slate-500">Target unique qualifying leads, not fabricated duplicates.</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Target Country / Market
                </label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g. Mexico, United States, UK"
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  City / Region (Optional)
                </label>
                <input
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="e.g. Mexico City, Guadalajara, Monterrey"
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Industry / Business Vertical
                </label>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. E-commerce, Retail, SaaS"
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Min Opportunity Score (0–100)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minOppScore}
                  onChange={(e) => setMinOppScore(Number(e.target.value))}
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  GrokxSEO Service Opportunity
                </label>
                <input
                  type="text"
                  value={desiredService}
                  onChange={(e) => setDesiredService(e.target.value)}
                  placeholder="e.g. Technical SEO, Backlinks, Digital PR"
                  className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Source Adapters & Quality */}
            <div className="pt-2 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Active Data Source Adapters
                </label>
                <div className="space-y-2">
                  {[
                    { id: "curated_directory", name: "Curated Business Listings (Mexico Verified Directory)" },
                    { id: "duckduckgo_search", name: "DuckDuckGo Organic Search Engine API" },
                    { id: "public_business_registry", name: "Public Organizational Registries & Sitemaps" }
                  ].map((src) => {
                    const isChecked = selectedSources.includes(src.id);
                    return (
                      <label
                        key={src.id}
                        className={`flex items-center p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                          isChecked ? "bg-blue-50 border-blue-300 text-blue-900" : "bg-slate-50 border-slate-200 text-slate-700"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSources([...selectedSources, src.id]);
                            } else {
                              setSelectedSources(selectedSources.filter((s) => s !== src.id));
                            }
                          }}
                          className="h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mr-2.5"
                        />
                        <span className="font-medium">{src.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Minimum Data Quality Threshold
                  </label>
                  <select
                    value={minDataQuality}
                    onChange={(e) => setMinDataQuality(e.target.value)}
                    className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="LOW">LOW (Accept company with valid canonical domain)</option>
                    <option value="MEDIUM">MEDIUM (Requires valid domain + website crawl evidence)</option>
                    <option value="HIGH">HIGH (Requires domain + SEO audit + contact channels)</option>
                  </select>
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <input
                    type="checkbox"
                    id="includePrevious"
                    checked={includePrevious}
                    onChange={(e) => setIncludePrevious(e.target.checked)}
                    className="h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                  />
                  <label htmlFor="includePrevious" className="text-xs text-slate-700 font-medium">
                    Include previously discovered leads (otherwise skip CRM duplicates)
                  </label>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1">
                  <div className="font-bold text-slate-800 flex items-center gap-1.5">
                    <HardDrive className="w-3.5 h-3.5 text-blue-600" /> Auto-Sync Destination
                  </div>
                  <p>
                    All verified prospects will be automatically synchronized with your connected <strong>Google Drive</strong> Master Sheet.
                  </p>
                </div>
              </div>
            </div>

            {/* Launch Error Notice */}
            {launchError && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{launchError}</span>
              </div>
            )}

            {/* Launch Action */}
            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => handleLaunchDiscovery()}
                disabled={isLaunchingJob || selectedSources.length === 0}
                className="inline-flex items-center px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md transition disabled:opacity-50"
              >
                {isLaunchingJob ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Enqueuing Discovery Job...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Execute Lead Discovery ({targetCount} Leads in {country})
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Reusable Scraping Templates */}
      {activeTab === "templates" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-900">Pre-Configured Scraping Templates (Module A3)</h2>
            <p className="text-xs text-slate-500 mt-1">
              Production-tested prospecting configurations tuned for specific GrokxSEO service opportunities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((tmpl) => (
              <div
                key={tmpl.id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 text-[11px] font-bold bg-blue-50 text-blue-700 rounded-md">
                      {tmpl.target_market}
                    </span>
                    <span className="text-xs font-semibold text-slate-600">
                      Target: {tmpl.default_target_count} Leads
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base">{tmpl.name}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{tmpl.description}</p>

                  <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
                    <div className="text-slate-500">
                      Industry: <strong className="text-slate-800">{tmpl.industry}</strong>
                    </div>
                    <div className="text-slate-500">
                      Recommended: <strong className="text-slate-800">{tmpl.recommended_services.join(", ")}</strong>
                    </div>
                    <div className="text-slate-500">
                      Sources: <span className="font-mono text-[11px] text-slate-700">{tmpl.sources.join(", ")}</span>
                    </div>
                    <div className="text-slate-500">
                      Focus: <span className="text-indigo-700 font-medium">{tmpl.scoring_focus}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-5 mt-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Ready to Run
                  </span>
                  <button
                    onClick={() => handleUseTemplate(tmpl)}
                    disabled={isLaunchingJob}
                    className="inline-flex items-center px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
                  >
                    Use & Execute <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Extraction Job Dashboard */}
      {activeTab === "jobs" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div>
              <h2 className="text-base font-bold text-slate-900">Lead Extraction Jobs Dashboard (Module A5)</h2>
              <p className="text-xs text-slate-500 mt-1">
                Persistent background pipeline execution status, counts, and verification records.
              </p>
            </div>
            <button
              onClick={loadJobs}
              disabled={loadingJobs}
              className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
            >
              <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${loadingJobs ? "animate-spin" : ""}`} /> Refresh Jobs
            </button>
          </div>

          {jobs.length === 0 ? (
            <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-3">
              <Activity className="w-10 h-10 text-slate-400 mx-auto" />
              <div className="text-sm font-bold text-slate-800">No Lead Discovery Jobs Yet</div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Launch a discovery run using the AI Prompt or select a template to discover real prospects.
              </p>
              <button
                onClick={() => setActiveTab("nl_search")}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition shadow-sm"
              >
                Start New Discovery Job
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => {
                const statusColor =
                  job.status === "COMPLETED"
                    ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                    : job.status === "RUNNING"
                    ? "bg-blue-100 text-blue-800 border-blue-300 animate-pulse"
                    : job.status === "QUEUED"
                    ? "bg-amber-100 text-amber-800 border-amber-300"
                    : job.status === "CANCELLED"
                    ? "bg-slate-100 text-slate-700 border-slate-300"
                    : "bg-red-100 text-red-800 border-red-300";

                return (
                  <div
                    key={job.id}
                    className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 hover:border-blue-200 transition"
                  >
                    {/* Top Row */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${statusColor}`}>
                            {job.status}
                          </span>
                          <span className="text-xs font-mono text-slate-400">ID: {job.id.slice(0, 8)}...</span>
                          {job.current_stage && (
                            <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                              Stage: {job.current_stage}
                            </span>
                          )}
                        </div>
                        <h3 className="font-bold text-slate-900 text-base mt-1">
                          {job.job_name || `Discovery Job (${job.requested_count} leads)`}
                        </h3>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-2">
                        {job.status === "RUNNING" && (
                          <button
                            onClick={() => handleCancelJob(job.id)}
                            disabled={actionLoadingJobId === job.id}
                            className="inline-flex items-center px-2.5 py-1 text-xs font-semibold text-red-600 hover:bg-red-50 rounded border border-red-200 transition"
                          >
                            <Ban className="w-3.5 h-3.5 mr-1" /> Cancel
                          </button>
                        )}
                        {(job.status === "FAILED" || job.status === "CANCELLED") && (
                          <button
                            onClick={() => handleRetryJob(job.id)}
                            disabled={actionLoadingJobId === job.id}
                            className="inline-flex items-center px-2.5 py-1 text-xs font-semibold text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition"
                          >
                            <RotateCcw className="w-3.5 h-3.5 mr-1" /> Retry
                          </button>
                        )}
                        <Link
                          href="/crm"
                          className="inline-flex items-center px-3 py-1 text-xs font-bold bg-slate-900 text-white rounded hover:bg-slate-800 transition"
                        >
                          View CRM <ChevronRight className="w-3.5 h-3.5 ml-1" />
                        </Link>
                      </div>
                    </div>

                    {/* Stats Metrics Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-2 text-xs">
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Target Leads</div>
                        <div className="font-bold text-slate-900 text-sm mt-0.5">{job.requested_count}</div>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Discovered</div>
                        <div className="font-bold text-slate-900 text-sm mt-0.5">{job.leads_discovered}</div>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Validated</div>
                        <div className="font-bold text-emerald-700 text-sm mt-0.5">{job.leads_validated}</div>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Deduplicated</div>
                        <div className="font-bold text-amber-700 text-sm mt-0.5">{job.duplicates_skipped}</div>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Saved in CRM</div>
                        <div className="font-bold text-blue-700 text-sm mt-0.5">{job.leads_saved}</div>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="text-slate-500 text-[10px] uppercase font-bold">Drive Synced</div>
                        <div className="font-bold text-indigo-700 text-sm mt-0.5">{job.gdrive_synced_count}</div>
                      </div>
                    </div>

                    {/* Error / Notes if any */}
                    {job.error_summary && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800">
                        <strong>Error Summary:</strong> {job.error_summary}
                      </div>
                    )}

                    <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                      <div>Sources Used: {job.sources_used?.join(", ") || "Multi-adapter"}</div>
                      <div>
                        {job.started_at && `Started: ${new Date(job.started_at).toLocaleTimeString()}`}
                        {job.duration_seconds !== undefined && ` (${job.duration_seconds}s)`}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Data Sources & Permissions */}
      {activeTab === "sources" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-900">Supported Source Adapters (Module A2)</h2>
            <p className="text-xs text-slate-500 mt-1">
              Documented source adapters, rate limits, access permissions, and configuration requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sources.map((src) => (
              <div key={src.name} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-slate-900 text-base">{src.name}</div>
                  <span
                    className={`px-2 py-0.5 text-xs font-bold rounded ${
                      src.is_available ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {src.config_status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{src.description}</p>

                <div className="space-y-1 text-xs border-t border-slate-100 pt-3">
                  <div className="text-slate-500">
                    Source Type: <strong className="text-slate-800">{src.source_type}</strong>
                  </div>
                  <div className="text-slate-500">
                    Rate Limit: <span className="font-mono text-slate-700">{src.rate_limit}</span>
                  </div>
                  <div className="text-slate-500">
                    Supported Fields: <span className="text-slate-700">{src.supported_fields.join(", ")}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: Direct Commercial Intake (Preserved) */}
      {activeTab === "intake" && (
        <div className="bg-white shadow-sm rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
          <div className="flex items-center space-x-2 pb-4 border-b border-slate-100">
            <Globe className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-base font-bold text-slate-900">Direct Commercial Prospect Intake</h2>
              <p className="text-xs text-slate-500">
                Normalizes URL, extracts canonical domain, prevents duplicates, and links to CRM sales pipeline.
              </p>
            </div>
          </div>

          <form onSubmit={handleDirectIntake} className="space-y-5">
            <div>
              <label htmlFor="intakeDomain" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Target Website Domain or URL *
              </label>
              <div className="mt-1.5 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Globe className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="text"
                  id="intakeDomain"
                  required
                  className="block w-full pl-10 pr-4 py-2.5 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. 'thedefiant.io' or 'https://www.analyticsinsight.net/'"
                  value={intakeDomain}
                  onChange={(e) => setIntakeDomain(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="intakeName" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Company / Organization Name (Optional)
                </label>
                <div className="mt-1.5 relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Building2 className="h-4 w-4 text-slate-400" />
                  </div>
                  <input
                    type="text"
                    id="intakeName"
                    className="block w-full pl-10 pr-4 py-2 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 'The Defiant'"
                    value={intakeName}
                    onChange={(e) => setIntakeName(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="intakeIndustry" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Target Vertical / Industry (Optional)
                </label>
                <div className="mt-1.5 relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Filter className="h-4 w-4 text-slate-400" />
                  </div>
                  <input
                    type="text"
                    id="intakeIndustry"
                    className="block w-full pl-10 pr-4 py-2 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 'Fintech & Web3 Media'"
                    value={intakeIndustry}
                    onChange={(e) => setIntakeIndustry(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <input
                type="checkbox"
                id="triggerAnalysis"
                checked={triggerAnalysis}
                onChange={(e) => setTriggerAnalysis(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded"
              />
              <label htmlFor="triggerAnalysis" className="text-xs text-slate-700 font-medium">
                Immediately enqueue initial website analysis crawl after intake
              </label>
            </div>

            <button
              type="submit"
              disabled={isIntakeSubmitting || !intakeDomain.trim()}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
            >
              {isIntakeSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Normalizing Domain & Checking Catalog...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Ingest & Normalize Prospect
                </>
              )}
            </button>
          </form>

          {/* Success / Duplicate Result Card */}
          {intakeResult && (
            <div
              className={`mt-6 p-5 rounded-xl border ${
                intakeResult.is_duplicate
                  ? "bg-amber-50 border-amber-200 text-amber-900"
                  : "bg-emerald-50 border-emerald-200 text-emerald-900"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="font-bold flex items-center gap-2">
                    {intakeResult.is_duplicate ? (
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    )}
                    {intakeResult.is_duplicate
                      ? "Prospect Already Exists in Catalog (Deduplicated)"
                      : "Prospect Successfully Ingested"}
                  </div>
                  <p className="text-xs leading-relaxed">{intakeResult.message}</p>
                  <div className="text-xs font-mono text-slate-600 mt-2 bg-white/80 p-2.5 rounded-lg border border-slate-200 space-y-0.5">
                    <div>Canonical Domain: <strong>{intakeResult.company?.canonical_domain}</strong></div>
                    <div>Company Name: <strong>{intakeResult.company?.name || intakeResult.company?.company_name}</strong></div>
                    <div>Catalog ID: <span className="text-slate-500">{intakeResult.company?.id}</span></div>
                    {intakeResult.analysis_job_id && (
                      <div className="text-blue-700">Analysis Job Queued: {intakeResult.analysis_job_id}</div>
                    )}
                  </div>
                </div>

                <Link
                  href={`/companies/${intakeResult.company?.id}`}
                  className="inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition whitespace-nowrap ml-4"
                >
                  View Intelligence <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </Link>
              </div>
            </div>
          )}

          {intakeError && (
            <div className="mt-6 bg-red-50 p-4 rounded-xl border border-red-200 text-xs text-red-700 space-y-1">
              <div className="font-bold text-red-900 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-red-600" /> Intake Failed
              </div>
              <p>{intakeError}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
