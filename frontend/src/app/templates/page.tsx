"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutGrid,
  Search,
  ExternalLink,
  Code2,
  Play,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  Info,
  X,
  FileSpreadsheet,
  Globe2,
  ShieldAlert
} from "lucide-react";
import { scraperApi, ScraperTemplate } from "@/lib/scraperApi";

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<ScraperTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeTemplate, setActiveTemplate] = useState<ScraperTemplate | null>(null);

  // Modal execution state
  const [formInputs, setFormInputs] = useState<Record<string, any>>({});
  const [customTaskName, setCustomTaskName] = useState<string>("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await scraperApi.getTemplates();
        if (res && res.templates) {
          setTemplates(res.templates);
        }
      } catch (err) {
        console.error("Failed to load templates", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const categories = [
    "All",
    "Lead Generation",
    "Search & Maps",
    "E-commerce",
    "Company Intelligence",
    "Real Estate & Jobs",
    "Content & News"
  ];

  const filteredTemplates = templates.filter((tpl) => {
    const matchesCategory = selectedCategory === "All" || tpl.category === selectedCategory;
    const matchesSearch =
      tpl.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tpl.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tpl.data_source.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const openTemplateModal = (tpl: ScraperTemplate) => {
    setActiveTemplate(tpl);
    setCustomTaskName(`${tpl.name} Run`);
    const initialInputs: Record<string, any> = {};
    for (const p of tpl.input_parameters) {
      initialInputs[p.key] = p.default;
    }
    setFormInputs(initialInputs);
    setExecutionMessage(null);
  };

  const handleRunNow = async () => {
    if (!activeTemplate) return;
    try {
      setIsExecuting(true);
      setExecutionMessage("Creating extraction task from template...");

      // Extract target url from inputs if present
      const targetUrl = formInputs.directory_url || formInputs.target_url || formInputs.start_url || formInputs.catalog_url || formInputs.website_url;
      const res = await scraperApi.instantiateTemplate(activeTemplate.id, customTaskName, targetUrl);
      
      setExecutionMessage("Starting cloud extraction worker...");
      await scraperApi.runTask(res.task_id, "CLOUD");

      setExecutionMessage("Task queued and running successfully! Redirecting to tasks...");
      setTimeout(() => {
        router.push("/tasks");
      }, 1200);
    } catch (err: any) {
      setExecutionMessage(`Error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCustomizeInBuilder = () => {
    if (!activeTemplate) return;
    const targetUrl = formInputs.directory_url || formInputs.target_url || formInputs.start_url || formInputs.catalog_url || formInputs.website_url || "";
    router.push(`/custom-scraper?template_id=${activeTemplate.id}&target_url=${encodeURIComponent(targetUrl)}`);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
              Module F: Executable Templates
            </span>
            <span className="text-xs text-slate-400 font-mono">12 Pre-Built Tasks</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Scraping Template Library</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Ready-to-use extraction workflows inspired by Octoparse template tasks. Enter parameters and extract structured data instantly.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition ${
                selectedCategory === cat
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs">Loading template library...</div>
      ) : filteredTemplates.length === 0 ? (
        <div className="py-20 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
          No templates match your search filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTemplates.map((tpl) => (
            <div
              key={tpl.id}
              className="bg-white rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition flex flex-col justify-between p-5 space-y-4"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/50">
                    {tpl.category}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Executable</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{tpl.name}</h3>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">{tpl.description}</p>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-100 text-xs">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Data Source</span>
                  <div className="text-slate-700 font-medium truncate mt-0.5">{tpl.data_source}</div>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Output Fields</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {tpl.output_fields.slice(0, 4).map((f) => (
                      <span key={f} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-mono">
                        {f}
                      </span>
                    ))}
                    {tpl.output_fields.length > 4 && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-500 font-mono">
                        +{tpl.output_fields.length - 4} more
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between gap-2">
                  <button
                    onClick={() => openTemplateModal(tpl)}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Use Template
                  </button>
                  <button
                    onClick={() => {
                      router.push(`/custom-scraper?template_id=${tpl.id}`);
                    }}
                    title="Customize in Visual Scraper Builder"
                    className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition"
                  >
                    <Code2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Template Execution & Details */}
      {activeTemplate && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700">
                    {activeTemplate.category}
                  </span>
                  <span className="text-xs text-slate-400">Template ID: {activeTemplate.id}</span>
                </div>
                <h2 className="text-lg font-bold text-slate-900">{activeTemplate.name}</h2>
              </div>
              <button
                onClick={() => setActiveTemplate(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">{activeTemplate.description}</p>

            {/* Credential & Limitations Notice */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
              <div className="flex items-center gap-1.5 text-slate-700 font-semibold">
                <Info className="w-4 h-4 text-blue-600" />
                <span>Credentials & Compliance</span>
              </div>
              <div className="text-slate-500 pl-5">
                <strong>Access:</strong> {activeTemplate.required_credentials}
              </div>
              <div className="text-slate-500 pl-5">
                <strong>Limitations:</strong> {activeTemplate.limitations}
              </div>
            </div>

            {/* Task Name & Input Parameters */}
            <div className="space-y-3.5">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Configure Task Inputs</h4>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Task Name</label>
                <input
                  type="text"
                  value={customTaskName}
                  onChange={(e) => setCustomTaskName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {activeTemplate.input_parameters.map((p) => (
                <div key={p.key}>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {p.label} {p.required && <span className="text-rose-500">*</span>}
                  </label>
                  <input
                    type={p.type === "number" ? "number" : "text"}
                    value={formInputs[p.key] !== undefined ? formInputs[p.key] : p.default}
                    onChange={(e) =>
                      setFormInputs({
                        ...formInputs,
                        [p.key]: p.type === "number" ? Number(e.target.value) : e.target.value
                      })
                    }
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              ))}
            </div>

            {/* Sample Output Preview (Octoparse pattern) */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Sample Output Preview</h4>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200/60">
                  SAMPLE DATA ONLY
                </span>
              </div>
              <pre className="p-3 bg-slate-900 text-slate-200 rounded-xl text-[11px] font-mono overflow-x-auto max-h-36">
                {JSON.stringify(activeTemplate.example_output, null, 2)}
              </pre>
            </div>

            {/* Execution status message */}
            {executionMessage && (
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs font-medium text-blue-700 flex items-center gap-2">
                <Clock className="w-4 h-4 animate-spin text-blue-600" />
                <span>{executionMessage}</span>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100 gap-3">
              <button
                onClick={handleCustomizeInBuilder}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                <Code2 className="w-4 h-4" />
                Customize in Visual Builder
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTemplate(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRunNow}
                  disabled={isExecuting}
                  className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  {isExecuting ? "Launching Cloud Job..." : "Run Extraction Now"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

