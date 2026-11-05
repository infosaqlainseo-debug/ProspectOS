"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Code2,
  Terminal,
  Cpu,
  ShieldCheck,
  Zap,
  Globe,
  Database,
  Layers,
  ArrowRight,
  ExternalLink,
  Copy,
  Check
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function DocsPage() {
  const [copiedSnippet, setCopiedSnippet] = useState<string | null>(null);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSnippet(id);
    setTimeout(() => setCopiedSnippet(null), 2000);
  };

  const curlExample = `curl -X POST https://api.prospectos.com/scraper/tasks \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Fintech SaaS in Mexico",
    "prompt": "Find 50 fresh fintech startups in Mexico with active websites and social presence",
    "target_records": 50,
    "max_depth": 2,
    "auto_import_crm": true
  }'`;

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-6">
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className="text-slate-600 bg-slate-50 font-mono text-[11px]">
            API v1.4.0 • Enterprise Reference
          </Badge>
          <Badge variant="success" dot={true}>
            Production Ready
          </Badge>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Platform Architecture &amp; Developer Docs
        </h1>
        <p className="text-sm text-slate-500 mt-1 max-w-3xl">
          Complete reference for ProspectOS Cloud Web Scraping, Intelligent Lead CRM, AI Enrichment pipelines, and granular Super Admin controls.
        </p>
      </div>

      {/* Quick Nav Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:border-slate-300 transition cursor-pointer">
          <CardContent className="p-5">
            <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200/60 flex items-center justify-center text-blue-600 mb-3">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Scraper Core Engine</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Autonomous discovery, DOM structure extraction, dynamic JS pagination, and validation pipelines.
            </p>
          </CardContent>
        </Card>

        <Card className="hover:border-slate-300 transition cursor-pointer">
          <CardContent className="p-5">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200/60 flex items-center justify-center text-emerald-600 mb-3">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Native CRM Intelligence</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Traceable lead records, multi-stage pipelines, automated scoring, and real-time deduplication.
            </p>
          </CardContent>
        </Card>

        <Card className="hover:border-slate-300 transition cursor-pointer">
          <CardContent className="p-5">
            <div className="w-9 h-9 rounded-lg bg-purple-50 border border-purple-200/60 flex items-center justify-center text-purple-600 mb-3">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Super Admin &amp; SEO Engine</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Granular RBAC, worker pool scaling, AI latency benchmarking, and automated technical SEO audits.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* REST API & Quickstart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Terminal className="w-4 h-4 text-slate-700" />
                Quickstart: Triggering an Autonomous Task
              </CardTitle>
              <CardDescription>
                Submit an autonomous natural language scraping query via our authenticated REST API.
              </CardDescription>
            </div>
            <button
              onClick={() => handleCopy("curl", curlExample)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-600 bg-slate-50 hover:bg-slate-100 rounded border border-slate-200 transition"
            >
              {copiedSnippet === "curl" ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  Copy cURL
                </>
              )}
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900 rounded-lg p-4 font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed border border-slate-800">
            <pre>{curlExample}</pre>
          </div>
        </CardContent>
      </Card>

      {/* Architecture Deep Dive */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              Extraction Pipeline Stages
            </CardTitle>
            <CardDescription>Zero fabrication, fully verifiable audit trail</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs text-slate-600">
            <div className="flex gap-3">
              <span className="font-mono text-blue-600 font-semibold">01.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">Discovery &amp; Intent Parsing</strong>
                Natural language query decomposed into search heuristics, target locations, industry taxonomies, and depth bounds.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-blue-600 font-semibold">02.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">DOM Extraction &amp; Pagination</strong>
                Cloud workers fetch dynamic pages, parse OpenGraph/JSON-LD, extract emails, phones, and LinkedIn endpoints.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-blue-600 font-semibold">03.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">Deduplication &amp; Cleaning</strong>
                Domain canonicalization (`https://www.site.com/` → `site.com`), contact validation, and duplicate hashing.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-blue-600 font-semibold">04.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">CRM Ingestion &amp; Verification</strong>
                Records imported with provenance metadata, HTTP response codes, and verified timestamp stamps.
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Super Admin &amp; Security Governance
            </CardTitle>
            <CardDescription>Multi-tenant safeguards and role isolation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs text-slate-600">
            <div className="flex gap-3">
              <span className="font-mono text-emerald-600 font-semibold">01.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">Dynamic Role-Based Access Control</strong>
                Fine-grained permissions matrix distinguishing Super Admin, Admin, Manager, Member, and Read-Only personas.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-emerald-600 font-semibold">02.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">AI Model Quotas &amp; Rate Limits</strong>
                Centralized gateway governing Gemini, OpenAI, and Anthropic API keys with RPM/TPM bounds and token cost telemetry.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-emerald-600 font-semibold">03.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">Automated Technical SEO Engine</strong>
                Dynamic XML sitemap (`/sitemap.xml`) generation, crawler directives (`/robots.txt`), and live Google SERP simulation.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-mono text-emerald-600 font-semibold">04.</span>
              <div>
                <strong className="text-slate-900 block mb-0.5">Immutable Audit Trail</strong>
                System actions, user invitations, and configuration mutations cryptographically logged in PostgreSQL.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Useful links */}
      <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-lg">
        <div className="text-xs text-slate-600">
          Looking for interactive Swagger documentation? Explore all API endpoints live.
        </div>
        <Link
          href="/api-docs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700"
        >
          Open API &amp; Integrations Hub
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}

