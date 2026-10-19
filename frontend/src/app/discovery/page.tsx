"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Search, Loader2, Globe, Building2, CheckCircle2, AlertTriangle, ArrowRight, Sparkles, Filter } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface DiscoveryResult {
  error?: string;
  enqueued_jobs?: number;
}

export default function DiscoveryPage() {
  const [activeTab, setActiveTab] = useState<"intake" | "batch">("intake");

  // Direct Intake Form States
  const [intakeDomain, setIntakeDomain] = useState("");
  const [intakeName, setIntakeName] = useState("");
  const [intakeIndustry, setIntakeIndustry] = useState("");
  const [triggerAnalysis, setTriggerAnalysis] = useState(true);
  const [isIntakeSubmitting, setIsIntakeSubmitting] = useState(false);
  const [intakeResult, setIntakeResult] = useState<{
    status: string;
    is_duplicate: boolean;
    message: string;
    company: any;
    analysis_job_id?: string;
  } | null>(null);
  const [intakeError, setIntakeError] = useState<string | null>(null);

  // Batch Discovery Form States
  const [query, setQuery] = useState("");
  const [count, setCount] = useState(10);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const router = useRouter();

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

  const handleBatchDiscovery = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setResult(null);
    try {
      const res = await api.triggerDiscovery(query, count);
      setResult(res);
    } catch (e: unknown) {
      setResult({ error: e instanceof Error ? e.message : "Failed to trigger discovery" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 flex items-center">
            <Search className="w-7 h-7 mr-3 text-blue-600" /> Prospect Discovery & Direct Intake
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Import real commercial domains for GrokxSEO audit or run batch discovery across public organizational directories.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-lg bg-slate-100 p-1 border border-slate-200">
          <button
            onClick={() => setActiveTab("intake")}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition ${
              activeTab === "intake"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Direct Prospect Intake
          </button>
          <button
            onClick={() => setActiveTab("batch")}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition ${
              activeTab === "batch"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Batch Discovery Engine
          </button>
        </div>
      </div>

      {/* TAB 1: Direct Prospect Intake */}
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
              <p className="mt-1.5 text-xs text-slate-500">
                Protocol (https://) and subdomain prefixes (www.) are automatically normalized to the canonical domain.
              </p>
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

      {/* TAB 2: Batch Discovery Engine */}
      {activeTab === "batch" && (
        <div className="bg-white shadow-sm rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
          <div className="flex items-center space-x-2 pb-4 border-b border-slate-100">
            <Search className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-base font-bold text-slate-900">Batch Organizational Discovery Engine</h2>
              <p className="text-xs text-slate-500">
                Discovers companies and public domains from authorized sources (Phase 1.3).
              </p>
            </div>
          </div>

          <form onSubmit={handleBatchDiscovery} className="space-y-6">
            <div>
              <label htmlFor="query" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Search Query *
              </label>
              <div className="mt-1.5 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="text"
                  id="query"
                  required
                  className="block w-full pl-10 pr-4 py-2.5 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. 'Cybersecurity companies in London' or 'Fintech'"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label htmlFor="count" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Target Discovery Count
              </label>
              <input
                type="number"
                id="count"
                min="1"
                max="100"
                className="mt-1.5 block w-full py-2 px-3 sm:text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !query.trim()}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Start Batch Discovery Job"}
            </button>
          </form>

          {result && !result.error && (
            <div className="mt-6 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
              <h3 className="text-xs font-bold text-emerald-900 uppercase tracking-wider">Discovery Job Queued</h3>
              <p className="text-xs text-emerald-700 mt-1">
                Your batch discovery job has been enqueued to the ARQ worker queue.
              </p>
              <button
                onClick={() => router.push("/jobs")}
                className="mt-3 text-xs font-bold text-emerald-800 underline hover:text-emerald-950 inline-flex items-center"
              >
                View in Jobs Monitor <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
            </div>
          )}

          {result && result.error && (
            <div className="mt-6 bg-red-50 p-4 rounded-xl border border-red-200 text-xs text-red-700">
              <div className="font-bold text-red-900">Job Enqueue Error</div>
              <p className="mt-0.5">{result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
