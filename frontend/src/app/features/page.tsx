"use client";

import React from "react";
import Link from "next/link";
import {
  Code2,
  Cloud,
  Database,
  Sparkles,
  Users,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Kanban,
  FileSpreadsheet,
  Globe,
  Layers,
  Activity
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function FeaturesPage() {
  const features = [
    {
      title: "Visual Scraping Workflow Builder",
      category: "Extraction Engine",
      icon: Code2,
      desc: "Intuitive element selector inspired by Octoparse. Define container targets, child field extractors, attribute mapping (href, text, src), and dynamic loops without writing custom scrapers."
    },
    {
      title: "Cloud Worker Cluster & Parallel Ingestion",
      category: "Infrastructure",
      icon: Cloud,
      desc: "Distributed execution powered by Arq over Redis. Parallel workers process thousands of records with configurable domain rate-limiting, proxy rotation, and robots.txt etiquette."
    },
    {
      title: "Dynamic Pagination & Infinite Scroll",
      category: "Extraction Engine",
      icon: Layers,
      desc: "Supports next-button clicking, query string parameter iteration (?page=N), and bounded scroll triggers with strict depth limits to prevent infinite crawl traps."
    },
    {
      title: "4-Pillar Transparent Lead Scoring (0–100)",
      category: "Lead Intelligence",
      icon: Sparkles,
      desc: "Mathematical lead evaluation assessing Contact Completeness (30%), Business Fit (30%), Website Health (20%), and Authority / SEO Opportunity (20%) with zero synthetic data."
    },
    {
      title: "Interactive Kanban Pipeline Board",
      category: "CRM Platform",
      icon: Kanban,
      desc: "Attio and Linear inspired deal progression. Drag and drop prospects across 8 default stages from 'NEW' and 'QUALIFIED' to 'WON', with complete timestamped audit logging."
    },
    {
      title: "Deep AI Company Research & Assistant",
      category: "AI Engine",
      icon: Users,
      desc: "Multimodal AI synthesis powered by Google Gemini and OpenAI. Generates comprehensive company dossiers, executive summaries, ICP fit analysis, and recommended outreach strategies."
    },
    {
      title: "Canonical Domain Anti-Duplication",
      category: "Data Hygiene",
      icon: FileSpreadsheet,
      desc: "Universal URL normalization (stripping www, http/https, subdomains, UTM params) ensures no duplicate company records exist across disparate scraping runs."
    },
    {
      title: "Super Admin & SEO Control Center",
      category: "Governance",
      icon: ShieldCheck,
      desc: "Restricted administrative control center with live system telemetry, RBAC permissions matrix, live Google SERP preview, XML sitemap generator, and robots.txt protection."
    }
  ];

  return (
    <div className="space-y-10 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="text-center max-w-3xl mx-auto py-8">
        <Badge variant="ai" size="sm" className="mb-3">ENTERPRISE SAAS CAPABILITIES</Badge>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 leading-tight">
          Engineered for Autonomous Web Data Extraction &amp; CRM Intelligence
        </h1>
        <p className="text-sm sm:text-base text-slate-600 mt-3 leading-relaxed">
          ProspectOS unites the robust extraction capabilities of Octoparse with the modern, disciplined
          CRM workflow of Attio and Linear.
        </p>
        <div className="flex items-center justify-center gap-3 mt-6">
          <Link
            href="/custom-scraper"
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-xs shadow-blue-500/20 transition flex items-center gap-1.5"
          >
            Launch Visual Builder <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            href="/crm"
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition"
          >
            Explore Lead CRM
          </Link>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {features.map((f, i) => {
          const Icon = f.icon;
          return (
            <Card key={i} className="p-5 flex flex-col justify-between hover:border-blue-200 transition">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </div>
                  <Badge variant="neutral" size="sm">{f.category}</Badge>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1.5">{f.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Architecture Highlights */}
      <Card className="p-8 bg-linear-to-br from-slate-900 via-slate-900 to-blue-950 text-white border-0">
        <div className="max-w-2xl">
          <Badge variant="ai" size="sm" className="mb-2 bg-blue-500/20 text-blue-300 border-blue-400/30">
            ZERO SYNTHETIC DATA GUARANTEE
          </Badge>
          <h2 className="text-xl font-bold tracking-tight">Verified Public Data Provenance</h2>
          <p className="text-xs text-slate-300 mt-2 leading-relaxed">
            Every company, phone number, public business email, and SEO metric captured in ProspectOS includes
            its exact source URL, retrieval timestamp, and verification hash. The platform never hallucinates
            or fabricates data to reach artificial targets.
          </p>
          <div className="flex items-center gap-6 mt-6 text-xs font-medium text-slate-300">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Source URL Traceability</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Canonical Domain Deduplication</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Ethical robots.txt Compliance</span>
          </div>
        </div>
      </Card>
    </div>
  );
}

