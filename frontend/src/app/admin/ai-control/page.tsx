"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  ChevronLeft,
  RefreshCw,
  Zap,
  Shield,
  Key,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Coins,
  Cpu,
  Layers
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi, AIProviderItem } from "@/lib/adminApi";

export default function AIControlCenterPage() {
  const [providers, setProviders] = useState<AIProviderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any | null>(null);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      const res = await adminApi.getAIProviders();
      setProviders(res);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  const handleTestConnection = async (providerName: string) => {
    try {
      setTestingProvider(providerName);
      setTestResult(null);
      const res = await adminApi.testAIConnection(providerName);
      setTestResult(res);
    } catch (e: any) {
      alert(`Test error: ${e.message}`);
    } finally {
      setTestingProvider(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Link href="/admin" className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-medium">
              <ChevronLeft className="w-3.5 h-3.5" /> Back to Admin
            </Link>
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              Intelligence
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            AI Control Center &amp; Model Governance
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure LLM inference providers, regulate token quotas, inspect consumption metrics, and verify provider connectivity.
          </p>
        </div>
        <button
          onClick={fetchProviders}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 transition shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {testResult && (
        <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 flex items-start justify-between gap-3 text-purple-950 text-xs">
          <div>
            <div className="flex items-center gap-2 font-bold">
              <CheckCircle2 className="w-4 h-4 text-purple-600" />
              <span>{testResult.provider_name.toUpperCase()} Connection Verified</span>
            </div>
            <p className="mt-1 text-slate-700">
              Latency: <span className="font-mono font-bold text-purple-700">{testResult.latency_ms} ms</span> | Model Tested: <span className="font-mono">{testResult.model_tested}</span>
            </p>
            <p className="mt-1 text-[11px] text-purple-800 italic bg-white/70 p-2 rounded border border-purple-100">
              &ldquo;{testResult.response_snippet}&rdquo;
            </p>
          </div>
          <button
            onClick={() => setTestResult(null)}
            className="text-purple-700 hover:text-purple-950 font-bold text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {providers.map((p) => (
          <Card key={p.id} className="relative overflow-hidden">
            {p.is_default && (
              <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg">
                DEFAULT SYSTEM PROVIDER
              </div>
            )}
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm border border-purple-100">
                  {p.provider_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <CardTitle>{p.display_name}</CardTitle>
                  <CardDescription className="font-mono text-[11px]">Default: {p.default_model}</CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4 pt-1">
              {/* Credentials & Status */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block mb-0.5">API Key (Masked)</span>
                  <span className="font-mono font-semibold text-slate-800">{p.api_key_masked || "Unconfigured"}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Status</span>
                  {p.is_enabled ? (
                    <Badge variant="success" size="sm" dot>Enabled</Badge>
                  ) : (
                    <Badge variant="neutral" size="sm">Disabled</Badge>
                  )}
                </div>
              </div>

              {/* Quotas & Usage */}
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 rounded-lg border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">RPM Limit</span>
                  <span className="font-bold text-slate-800">{p.rpm_limit}</span>
                </div>
                <div className="p-2 rounded-lg border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Tokens (Total)</span>
                  <span className="font-bold text-slate-800">{p.total_tokens_used.toLocaleString()}</span>
                </div>
                <div className="p-2 rounded-lg border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Est. Cost</span>
                  <span className="font-bold text-slate-800">${p.estimated_cost_usd.toFixed(3)}</span>
                </div>
              </div>

              {/* Feature Flags */}
              <div>
                <span className="text-[11px] font-semibold text-slate-700 block mb-1.5">Enabled Capabilities</span>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(p.feature_flags).map(([key, enabled]) => (
                    <span
                      key={key}
                      className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                        enabled
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-slate-50 text-slate-400 border-slate-200"
                      }`}
                    >
                      {key.replace(/_/g, " ")}: {enabled ? "ON" : "OFF"}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <span className="text-[11px] text-slate-400 font-mono">
                  {p.available_models.length} Models registered
                </span>
                <button
                  onClick={() => handleTestConnection(p.provider_name)}
                  disabled={testingProvider === p.provider_name}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 transition"
                >
                  <Zap className={`w-3.5 h-3.5 ${testingProvider === p.provider_name ? "animate-pulse" : ""}`} />
                  {testingProvider === p.provider_name ? "Pinging..." : "Test Latency"}
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

