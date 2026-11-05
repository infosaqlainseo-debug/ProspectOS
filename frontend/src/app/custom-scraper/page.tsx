"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Code2,
  Globe2,
  Play,
  Save,
  Plus,
  Trash2,
  RefreshCw,
  Sparkles,
  Layers,
  ArrowRight,
  Eye,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Sliders,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  MousePointer,
  RotateCcw
} from "lucide-react";
import { scraperApi } from "@/lib/scraperApi";

interface ExtractionField {
  name: string;
  label?: string;
  selector: string;
  type: "text" | "link" | "image" | "attribute";
  attribute: string;
  sample_value?: string;
  confidence?: number;
}

interface WorkflowStep {
  id: string;
  type: string;
  name: string;
  params: Record<string, any>;
}

function CustomScraperContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateIdParam = searchParams.get("template_id");
  const targetUrlParam = searchParams.get("target_url");
  const taskIdParam = searchParams.get("task_id");

  // Task & URL State
  const [taskName, setTaskName] = useState("Custom Extraction Workflow");
  const [targetUrl, setTargetUrl] = useState(
    targetUrlParam || "https://www.yellowpages.com/search?search_terms=ecommerce&geo_location_terms=Mexico"
  );
  const [containerSelector, setContainerSelector] = useState(".result, .business-card, .listing-item");

  // Field List State
  const [fields, setFields] = useState<ExtractionField[]>([
    { name: "company_name", selector: "h2, h3, .title, .business-name", type: "text", attribute: "text", sample_value: "Example Company Ltd" },
    { name: "website", selector: "a[href*='http'], a.website", type: "link", attribute: "href", sample_value: "https://example.com" },
    { name: "phone", selector: ".phone, a[href^='tel:']", type: "text", attribute: "text", sample_value: "+52 55 5000 0000" },
    { name: "address", selector: ".address, .location, address", type: "text", attribute: "text", sample_value: "Mexico City, Mexico" },
    { name: "email", selector: "a[href^='mailto:'], .email", type: "text", attribute: "text", sample_value: "info@example.com" },
  ]);

  // Pagination State
  const [paginationType, setPaginationType] = useState<"NEXT_BUTTON" | "URL_PATTERN" | "NONE">("NEXT_BUTTON");
  const [paginationSelector, setPaginationSelector] = useState("a[rel='next'], .pagination .next");
  const [maxPages, setMaxPages] = useState<number>(3);
  const [maxRecords, setMaxRecords] = useState<number>(50);

  // Workflow Steps State
  const [steps, setSteps] = useState<WorkflowStep[]>([
    { id: "step_1", type: "open_url", name: "1. Navigate to Target URL", params: { url: targetUrl } },
    { id: "step_2", type: "loop_elements", name: "2. Loop Container Elements", params: { selector: containerSelector } },
    { id: "step_3", type: "extract_fields", name: "3. Extract Field Values", params: { count: fields.length } },
    { id: "step_4", type: "pagination", name: "4. Follow Next Page Loop", params: { max_pages: maxPages } },
    { id: "step_5", type: "clean_data", name: "5. Normalize & Clean Records", params: { trim: true, deduplicate: true } },
    { id: "step_6", type: "save_results", name: "6. Store to Data Center", params: {} },
  ]);

  // Interactive Browser Preview State
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [previewTitle, setPreviewTitle] = useState<string>("");
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [inspectorSelectedEl, setInspectorSelectedEl] = useState<{ tag: string; selector: string; text: string } | null>(null);

  // Execution & Testing State
  const [isDetecting, setIsDetecting] = useState(false);
  const [testResults, setTestResults] = useState<any[] | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  // New field input form
  const [newFieldName, setNewFieldName] = useState("");
  const [newFieldSelector, setNewFieldSelector] = useState("");
  const [newFieldType, setNewFieldType] = useState<"text" | "link" | "image" | "attribute">("text");

  // Load existing task or template if params present
  useEffect(() => {
    async function initFromParams() {
      if (templateIdParam) {
        try {
          const tpl = await scraperApi.getTemplate(templateIdParam);
          if (tpl) {
            setTaskName(`${tpl.name} Custom Workflow`);
            if (tpl.workflow_config?.container_selector) {
              setContainerSelector(tpl.workflow_config.container_selector);
            }
            if (tpl.workflow_config?.fields) {
              setFields(tpl.workflow_config.fields);
            }
            setStatusMessage({ type: "info", text: `Loaded configuration from template: ${tpl.name}` });
          }
        } catch (e) {
          console.error(e);
        }
      } else if (taskIdParam) {
        try {
          const task = await scraperApi.getTask(taskIdParam);
          if (task) {
            setTaskName(task.name);
            if (task.target_url) setTargetUrl(task.target_url);
            if (task.workflow_config?.container_selector) {
              setContainerSelector(task.workflow_config.container_selector);
            }
            if (task.workflow_config?.fields) {
              setFields(task.workflow_config.fields);
            }
            setStatusMessage({ type: "info", text: `Editing existing task: ${task.name}` });
          }
        } catch (e) {
          console.error(e);
        }
      }
    }
    initFromParams();
  }, [templateIdParam, taskIdParam]);

  // Load page preview
  const handleLoadPreview = async () => {
    if (!targetUrl) return;
    try {
      setIsLoadingPreview(true);
      setStatusMessage({ type: "info", text: "Loading page preview in controlled inspector sandbox..." });
      const res = await scraperApi.previewDom(targetUrl);
      setPreviewHtml(res.sanitized_html);
      setPreviewTitle(res.title);
      setStatusMessage({ type: "success", text: `Preview loaded successfully for ${targetUrl}` });
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Preview failed: ${e.message}` });
    } finally {
      setIsLoadingPreview(false);
    }
  };

  // Run Auto-Detection
  const handleAutoDetect = async () => {
    if (!targetUrl) return;
    try {
      setIsDetecting(true);
      setStatusMessage({ type: "info", text: "Auto-detecting DOM repeated structure and fields..." });
      const res = await scraperApi.autoDetect(targetUrl);
      if (res.detected_container) {
        setContainerSelector(res.detected_container);
      }
      if (res.detected_fields && res.detected_fields.length > 0) {
        setFields(res.detected_fields);
      }
      if (res.pagination) {
        setPaginationType(res.pagination.type === "NEXT_BUTTON" ? "NEXT_BUTTON" : "URL_PATTERN");
        if (res.pagination.selector) setPaginationSelector(res.pagination.selector);
      }
      if (res.sample_records) {
        setTestResults(res.sample_records);
      }
      setStatusMessage({
        type: "success",
        text: `Auto-detection completed! Identified container '${res.detected_container}' with ${res.detected_fields.length} fields.`
      });
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Auto-detection failed: ${e.message}` });
    } finally {
      setIsDetecting(false);
    }
  };

  // Add field from inspector or form
  const handleAddField = () => {
    if (!newFieldName.trim() || !newFieldSelector.trim()) {
      alert("Please enter field name and selector.");
      return;
    }
    const cleanName = newFieldName.toLowerCase().replace(/[^a-z0-9_]/g, "_");
    setFields([
      ...fields,
      {
        name: cleanName,
        selector: newFieldSelector.trim(),
        type: newFieldType,
        attribute: newFieldType === "link" ? "href" : newFieldType === "image" ? "src" : "text",
        sample_value: "Pending test"
      }
    ]);
    setNewFieldName("");
    setNewFieldSelector("");
  };

  const handleRemoveField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  // Test selectors
  const handleTestWorkflow = async () => {
    try {
      setStatusMessage({ type: "info", text: "Testing extraction selectors against page DOM..." });
      const res = await scraperApi.autoDetect(targetUrl);
      if (res.sample_records) {
        setTestResults(res.sample_records);
        setStatusMessage({ type: "success", text: `Extracted ${res.sample_records.length} sample preview records.` });
      }
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Test failed: ${e.message}` });
    }
  };

  // Save Task
  const handleSaveTask = async () => {
    try {
      setIsSaving(true);
      const workflowConfig = {
        start_url: targetUrl,
        container_selector: containerSelector,
        fields,
        pagination: paginationType !== "NONE" ? { type: paginationType, selector: paginationSelector, max_pages: maxPages } : null,
        max_records: maxRecords,
        max_pages: maxPages,
        steps
      };

      if (taskIdParam) {
        await scraperApi.updateTask(taskIdParam, {
          name: taskName,
          target_url: targetUrl,
          workflow_config: workflowConfig
        });
        setStatusMessage({ type: "success", text: "Task updated successfully!" });
      } else {
        const res = await scraperApi.createTask({
          name: taskName,
          task_type: "CUSTOM",
          target_url: targetUrl,
          workflow_config: workflowConfig,
          execution_mode: "CLOUD"
        });
        setStatusMessage({ type: "success", text: "Task saved successfully! Redirecting to tasks..." });
        setTimeout(() => router.push("/tasks"), 1000);
      }
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Save error: ${e.message}` });
    } finally {
      setIsSaving(false);
    }
  };

  // Save & Run Now
  const handleSaveAndRunNow = async () => {
    try {
      setIsSaving(true);
      const workflowConfig = {
        start_url: targetUrl,
        container_selector: containerSelector,
        fields,
        pagination: paginationType !== "NONE" ? { type: paginationType, selector: paginationSelector, max_pages: maxPages } : null,
        max_records: maxRecords,
        max_pages: maxPages
      };

      const res = await scraperApi.createTask({
        name: taskName,
        task_type: "CUSTOM",
        target_url: targetUrl,
        workflow_config: workflowConfig,
        execution_mode: "CLOUD"
      });

      await scraperApi.runTask(res.task.id, "CLOUD");
      setStatusMessage({ type: "success", text: "Task created and cloud execution started! Redirecting to task monitoring..." });
      setTimeout(() => router.push("/tasks"), 1000);
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Run error: ${e.message}` });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-slate-100 overflow-hidden select-none">
      {/* Top Workflow Builder Bar */}
      <div className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-sm z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-sm">
            <Code2 className="w-4 h-4" />
          </div>
          <div>
            <input
              type="text"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              className="text-sm font-bold text-slate-900 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-blue-500 focus:outline-none transition px-1"
            />
            <div className="text-[10px] text-slate-400 px-1 font-mono">Visual Scraper Workflow Builder</div>
          </div>
        </div>

        {/* URL Bar & Auto-Detect Actions */}
        <div className="flex-1 max-w-xl mx-6 flex items-center gap-2">
          <div className="relative flex-1">
            <Globe2 className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="url"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://target-website.com/directory"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>
          <button
            onClick={handleLoadPreview}
            disabled={isLoadingPreview}
            className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shrink-0"
          >
            {isLoadingPreview ? "Loading..." : "Load Preview"}
          </button>
          <button
            onClick={handleAutoDetect}
            disabled={isDetecting}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shrink-0 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {isDetecting ? "Detecting..." : "Auto-Detect"}
          </button>
        </div>

        {/* Header Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleTestWorkflow}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition"
          >
            <Eye className="w-3.5 h-3.5" />
            Test Preview
          </button>
          <button
            onClick={handleSaveTask}
            disabled={isSaving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            <Save className="w-3.5 h-3.5" />
            Save Task
          </button>
          <button
            onClick={handleSaveAndRunNow}
            disabled={isSaving}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm shadow-blue-500/20"
          >
            <Play className="w-3.5 h-3.5" />
            Run Cloud Task
          </button>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          className={`px-6 py-2 text-xs flex items-center justify-between border-b shrink-0 ${
            statusMessage.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : statusMessage.type === "error"
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-blue-50 text-blue-800 border-blue-200"
          }`}
        >
          <span>{statusMessage.text}</span>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-slate-600">
            ×
          </button>
        </div>
      )}

      {/* 3-Panel Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* PANEL 1: Left Panel — Workflow Actions Palette & Steps Editor */}
        <div className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Workflow Sequence</span>
            <span className="text-[10px] text-slate-400 font-mono">{steps.length} Steps</span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {steps.map((st, i) => (
              <div
                key={st.id}
                className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-blue-300 transition text-xs space-y-1"
              >
                <div className="flex items-center justify-between font-semibold text-slate-800">
                  <span>{st.name}</span>
                  <span className="w-4 h-4 rounded-full bg-slate-200 text-slate-600 text-[10px] flex items-center justify-center">
                    {i + 1}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono truncate">
                  Type: {st.type}
                </div>
              </div>
            ))}
          </div>

          {/* Palette Actions */}
          <div className="p-3 border-t border-slate-200 bg-slate-50/70 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Palette Actions</span>
            <div className="grid grid-cols-2 gap-1 text-[11px]">
              <button
                onClick={() => setSteps([...steps, { id: `step_${Date.now()}`, type: "extract_table", name: "Extract HTML Table", params: {} }])}
                className="p-1.5 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-left truncate"
              >
                + Table
              </button>
              <button
                onClick={() => setSteps([...steps, { id: `step_${Date.now()}`, type: "pagination", name: "Add Pagination", params: {} }])}
                className="p-1.5 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-left truncate"
              >
                + Pagination
              </button>
              <button
                onClick={() => setSteps([...steps, { id: `step_${Date.now()}`, type: "wait", name: "Wait Delay", params: { ms: 1000 } }])}
                className="p-1.5 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-left truncate"
              >
                + Wait Delay
              </button>
              <button
                onClick={() => setSteps([...steps, { id: `step_${Date.now()}`, type: "clean_data", name: "Clean Data", params: {} }])}
                className="p-1.5 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-left truncate"
              >
                + Clean Data
              </button>
            </div>
          </div>
        </div>

        {/* PANEL 2: Center Panel — Controlled Browser Preview & DOM Element Selector */}
        <div className="flex-1 bg-slate-100 flex flex-col overflow-hidden border-r border-slate-200">
          <div className="h-9 bg-slate-200/80 px-4 flex items-center justify-between text-xs text-slate-600 border-b border-slate-300/80 shrink-0">
            <div className="flex items-center gap-2">
              <MousePointer className="w-3.5 h-3.5 text-blue-600" />
              <span className="font-semibold text-slate-700">DOM Inspector Preview</span>
              {previewTitle && <span className="text-slate-500 truncate max-w-sm font-medium">({previewTitle})</span>}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">Click any element below to inspect & extract</span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto">
            {previewHtml ? (
              <div
                className="bg-white rounded-xl shadow-sm border border-slate-300 p-6 max-w-4xl mx-auto prose prose-sm prose-slate"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
                onClick={(e) => {
                  const target = e.target as HTMLElement;
                  if (!target) return;
                  const tag = target.tagName.toLowerCase();
                  const classes = target.className && typeof target.className === "string" ? target.className.split(" ")[0] : "";
                  const selector = classes ? `${tag}.${classes}` : tag;
                  const text = target.innerText || target.getAttribute("href") || target.getAttribute("src") || "";
                  setInspectorSelectedEl({ tag, selector, text: text.slice(0, 100) });
                  setNewFieldSelector(selector);
                  if (!newFieldName) setNewFieldName(tag);
                }}
              />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-3">
                <Globe2 className="w-12 h-12 text-slate-300" />
                <div className="max-w-md">
                  <h3 className="font-bold text-slate-700 text-sm">No Page Preview Loaded</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Click <strong>Load Preview</strong> above to render the webpage DOM, or click <strong>Auto-Detect</strong> to automatically identify cards and extractable fields!
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Inspector Selection Box */}
          {inspectorSelectedEl && (
            <div className="p-3 bg-white border-t border-slate-200 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 font-mono">
                  &lt;{inspectorSelectedEl.tag}&gt;
                </span>
                <span className="font-mono text-slate-700">Selector: {inspectorSelectedEl.selector}</span>
                <span className="text-slate-400 truncate max-w-md">Text: &quot;{inspectorSelectedEl.text}&quot;</span>
              </div>
              <button
                onClick={handleAddField}
                className="px-3 py-1 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded transition"
              >
                + Add As Field
              </button>
            </div>
          )}
        </div>

        {/* PANEL 3: Right Panel — Extraction Configuration & Field List */}
        <div className="w-96 bg-white flex flex-col shrink-0 overflow-hidden">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Extraction Fields</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 font-mono">
              {fields.length} Fields
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-5">
            {/* Container Selector Setting */}
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                Repeated Container Selector
              </label>
              <input
                type="text"
                value={containerSelector}
                onChange={(e) => setContainerSelector(e.target.value)}
                placeholder=".card, .business-item, tr"
                className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400 block">
                The CSS selector of the repeated item or card wrapping each lead.
              </span>
            </div>

            {/* Configured Fields List */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Field Mapping</span>
              {fields.map((f, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-white hover:border-slate-300 transition space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 font-mono text-xs">{f.name}</span>
                    <button
                      onClick={() => handleRemoveField(idx)}
                      className="p-1 text-slate-400 hover:text-rose-600 transition"
                      title="Remove field"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={f.selector}
                      onChange={(e) => {
                        const copy = [...fields];
                        copy[idx].selector = e.target.value;
                        setFields(copy);
                      }}
                      className="flex-1 bg-slate-50 border border-slate-200 rounded px-2 py-0.5 text-[11px] font-mono text-slate-700"
                    />
                    <select
                      value={f.type}
                      onChange={(e) => {
                        const copy = [...fields];
                        copy[idx].type = e.target.value as any;
                        setFields(copy);
                      }}
                      className="bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 text-[11px] text-slate-700 font-medium"
                    >
                      <option value="text">Text</option>
                      <option value="link">Link</option>
                      <option value="image">Image</option>
                      <option value="attribute">Attr</option>
                    </select>
                  </div>
                  {f.sample_value && (
                    <div className="text-[10px] text-slate-400 truncate font-mono">
                      Sample: {f.sample_value}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Add Custom Field Form */}
            <div className="p-3 rounded-xl border border-dashed border-slate-300 space-y-2">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">+ Add New Field</span>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="field_name"
                  value={newFieldName}
                  onChange={(e) => setNewFieldName(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs font-mono"
                />
                <select
                  value={newFieldType}
                  onChange={(e) => setNewFieldType(e.target.value as any)}
                  className="bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs"
                >
                  <option value="text">Text</option>
                  <option value="link">Link URL</option>
                  <option value="image">Image URL</option>
                  <option value="attribute">Attribute</option>
                </select>
              </div>
              <input
                type="text"
                placeholder="CSS Selector (e.g. .company-title)"
                value={newFieldSelector}
                onChange={(e) => setNewFieldSelector(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs font-mono"
              />
              <button
                onClick={handleAddField}
                className="w-full py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition"
              >
                Add Field
              </button>
            </div>

            {/* Pagination Settings */}
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">Pagination Settings</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-500 font-medium">Type</label>
                  <select
                    value={paginationType}
                    onChange={(e) => setPaginationType(e.target.value as any)}
                    className="w-full bg-white border border-slate-200 rounded p-1 text-xs"
                  >
                    <option value="NEXT_BUTTON">Next Button</option>
                    <option value="URL_PATTERN">URL Pattern</option>
                    <option value="NONE">Single Page</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium">Max Pages</label>
                  <input
                    type="number"
                    value={maxPages}
                    onChange={(e) => setMaxPages(Number(e.target.value))}
                    min={1}
                    max={20}
                    className="w-full bg-white border border-slate-200 rounded p-1 text-xs"
                  />
                </div>
              </div>
              {paginationType === "NEXT_BUTTON" && (
                <div>
                  <label className="text-[10px] text-slate-500 font-medium">Next Button Selector</label>
                  <input
                    type="text"
                    value={paginationSelector}
                    onChange={(e) => setPaginationSelector(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded p-1 text-xs font-mono"
                  />
                </div>
              )}
            </div>

            {/* Live Sample Test Preview Output */}
            {testResults && (
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                  Sample Extracted Data ({testResults.length} records)
                </span>
                <div className="max-h-56 overflow-y-auto space-y-2">
                  {testResults.map((rec, i) => (
                    <div key={i} className="p-2.5 rounded bg-slate-50 border border-slate-200 text-[11px] font-mono space-y-1">
                      <div className="font-bold text-slate-900">{rec.company_name || rec.title || "Record #" + (i + 1)}</div>
                      {rec.website && <div className="text-blue-600 truncate">{rec.website}</div>}
                      {rec.phone && <div className="text-slate-600">{rec.phone}</div>}
                      {rec.email && <div className="text-slate-600">{rec.email}</div>}
                      {rec.quality_score && (
                        <div className="text-[10px] text-emerald-600 font-semibold">Quality: {rec.quality_score} pts</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CustomScraperPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-400 text-xs">Loading Visual Scraper Builder...</div>}>
      <CustomScraperContent />
    </Suspense>
  );
}
