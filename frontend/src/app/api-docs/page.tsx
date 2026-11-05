"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  KeyRound,
  Terminal,
  Code2,
  Copy,
  Check,
  Plus,
  Trash2,
  ExternalLink,
  Download,
  ShieldCheck,
  Zap,
  RefreshCw,
  Server
} from "lucide-react";
import { scraperApi } from "@/lib/scraperApi";

export default function ApiDocsPage() {
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(true);

  // New Key Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [rateLimit, setRateLimit] = useState(60);
  const [newKeyCreated, setNewKeyCreated] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Active Code Example Tab
  const [activeLang, setActiveLang] = useState<"curl" | "python" | "javascript">("curl");
  const [copiedKey, setCopiedKey] = useState(false);

  const fetchKeys = async () => {
    try {
      setLoadingKeys(true);
      const res = await scraperApi.getApiKeys();
      if (res && res.items) setApiKeys(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingKeys(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleGenerateKey = async () => {
    if (!keyName.trim()) {
      alert("Please provide a name for the API key.");
      return;
    }
    try {
      setIsGenerating(true);
      const res = await scraperApi.createApiKey({
        name: keyName,
        rate_limit_rpm: rateLimit
      });
      setNewKeyCreated(res.api_key);
      await fetchKeys();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevokeKey = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to revoke API key "${name}"? Existing integrations using it will immediately lose access.`)) {
      return;
    }
    try {
      await scraperApi.revokeApiKey(id);
      await fetchKeys();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const codeSnippets = {
    curl: {
      create_task: `curl -X POST "http://localhost:8000/api/scraper/tasks" \\
  -H "Authorization: Bearer pos_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "E-Commerce Leads Mexico",
    "target_url": "https://example-directory.com/browse",
    "execution_mode": "CLOUD",
    "workflow_config": {
      "container_selector": ".business-card",
      "fields": [
        {"name": "company_name", "selector": ".title", "type": "text"},
        {"name": "website", "selector": "a.website", "type": "link"}
      ]
    }
  }'`,
      run_task: `curl -X POST "http://localhost:8000/api/scraper/tasks/YOUR_TASK_ID/run" \\
  -H "Authorization: Bearer pos_live_YOUR_KEY"`,
      get_data: `curl -X GET "http://localhost:8000/api/scraper/data?validation_status=VALID&limit=50" \\
  -H "Authorization: Bearer pos_live_YOUR_KEY"`
    },
    python: {
      create_task: `import requests

API_KEY = "pos_live_YOUR_KEY"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

payload = {
    "name": "E-Commerce Leads Mexico",
    "target_url": "https://example-directory.com/browse",
    "execution_mode": "CLOUD",
    "workflow_config": {
        "container_selector": ".business-card",
        "fields": [
            {"name": "company_name", "selector": ".title", "type": "text"},
            {"name": "website", "selector": "a.website", "type": "link"}
        ]
    }
}

response = requests.post("http://localhost:8000/api/scraper/tasks", json=payload, headers=headers)
print("Created Task:", response.json())`,
      run_task: `import requests

task_id = "YOUR_TASK_ID"
response = requests.post(f"http://localhost:8000/api/scraper/tasks/{task_id}/run")
print("Run Status:", response.json())`,
      get_data: `import requests

response = requests.get("http://localhost:8000/api/scraper/data?limit=50")
records = response.json()["items"]
for r in records:
    print(r["company_name"], r["website"], r["quality_score"])`
    },
    javascript: {
      create_task: `const response = await fetch('http://localhost:8000/api/scraper/tasks', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer pos_live_YOUR_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'E-Commerce Leads Mexico',
    target_url: 'https://example-directory.com/browse',
    execution_mode: 'CLOUD',
    workflow_config: {
      container_selector: '.business-card',
      fields: [
        { name: 'company_name', selector: '.title', type: 'text' },
        { name: 'website', selector: 'a.website', type: 'link' }
      ]
    }
  })
});

const task = await response.json();
console.log('Created task:', task);`,
      run_task: `const res = await fetch('http://localhost:8000/api/scraper/tasks/YOUR_TASK_ID/run', {
  method: 'POST'
});
console.log(await res.json());`,
      get_data: `const res = await fetch('http://localhost:8000/api/scraper/data?validation_status=VALID&limit=50');
const data = await res.json();
console.log('Retrieved records:', data.items);`
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">
              Module K: REST API & Integration Suite
            </span>
            <span className="text-xs text-slate-400 font-mono">OpenAPI 3.1 Documented</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">API Access & Developer Integrations</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Integrate ProspectOS extraction into custom software, manage API keys, and download the local runner agent.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Interactive Swagger Docs
          </a>
          <button
            onClick={() => {
              setIsModalOpen(true);
              setNewKeyCreated(null);
              setKeyName("");
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            Generate New API Key
          </button>
        </div>
      </div>

      {/* API Keys Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Active API Keys</h2>
            <p className="text-xs text-slate-500">Keys for programmatic access to tasks and data endpoints</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{apiKeys.length} Keys Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Key Name</th>
                <th className="py-3 px-3">Prefix / Token</th>
                <th className="py-3 px-3">Rate Limit</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Created</th>
                <th className="py-3 px-4 text-right">Revoke</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loadingKeys ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Loading API keys...
                  </td>
                </tr>
              ) : apiKeys.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No API keys generated yet. Click &quot;Generate New API Key&quot; above to create one.
                  </td>
                </tr>
              ) : (
                apiKeys.map((k) => (
                  <tr key={k.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-bold text-slate-900">{k.name}</td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-600">{k.prefix}</td>
                    <td className="py-3 px-3 font-mono text-slate-600">{k.rate_limit_rpm} req/min</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        ACTIVE
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-500">
                      {k.created_at ? new Date(k.created_at).toLocaleDateString() : "--"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleRevokeKey(k.id, k.name)}
                        className="p-1 text-slate-400 hover:text-rose-600 bg-slate-50 hover:bg-rose-50 rounded transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Code Snippets Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Developer Code Examples</h3>
            <p className="text-xs text-slate-500">Standard API implementation patterns</p>
          </div>
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
            {(["curl", "python", "javascript"] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setActiveLang(lang)}
                className={`px-3 py-1 rounded font-semibold capitalize transition ${
                  activeLang === lang ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {lang === "javascript" ? "Node / JS" : lang}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
              1. Create Extraction Task (POST /api/scraper/tasks)
            </span>
            <pre className="p-4 bg-slate-900 text-slate-200 rounded-xl text-[11px] font-mono overflow-x-auto leading-relaxed">
              {codeSnippets[activeLang].create_task}
            </pre>
          </div>

          <div>
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
              2. Launch Extraction Run (POST /api/scraper/tasks/:id/run)
            </span>
            <pre className="p-4 bg-slate-900 text-slate-200 rounded-xl text-[11px] font-mono overflow-x-auto leading-relaxed">
              {codeSnippets[activeLang].run_task}
            </pre>
          </div>

          <div>
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
              3. Retrieve Extracted Data Records (GET /api/scraper/data)
            </span>
            <pre className="p-4 bg-slate-900 text-slate-200 rounded-xl text-[11px] font-mono overflow-x-auto leading-relaxed">
              {codeSnippets[activeLang].get_data}
            </pre>
          </div>
        </div>
      </div>

      {/* Generate API Key Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Generate New Scraper API Key</h3>

            {newKeyCreated ? (
              <div className="space-y-3">
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs space-y-1">
                  <strong>API Key Generated Successfully!</strong>
                  <p className="text-[11px] text-emerald-700">
                    Copy your secret key now. For security purposes, this secret key will not be shown again.
                  </p>
                </div>
                <div className="relative">
                  <input
                    type="text"
                    readOnly
                    value={newKeyCreated}
                    className="w-full bg-slate-900 text-emerald-400 font-mono text-xs rounded-lg p-2.5 pr-20"
                  />
                  <button
                    onClick={() => copyToClipboard(newKeyCreated)}
                    className="absolute right-2 top-2 px-2 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-[11px] font-medium"
                  >
                    {copiedKey ? "Copied!" : "Copy Key"}
                  </button>
                </div>
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Key Name / Identifier</label>
                  <input
                    type="text"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    placeholder="e.g. Production Data Pipeline"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Rate Limit (Requests per Minute)</label>
                  <input
                    type="number"
                    value={rateLimit}
                    onChange={(e) => setRateLimit(Number(e.target.value))}
                    min={10}
                    max={1000}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-mono"
                  />
                </div>
                <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleGenerateKey}
                    disabled={isGenerating}
                    className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm"
                  >
                    {isGenerating ? "Generating..." : "Generate Secret Key"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

