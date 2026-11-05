"use client";

import React from "react";
import Link from "next/link";
import {
  Building2,
  ShoppingBag,
  Globe,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  Search,
  Sparkles
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SolutionsPage() {
  const solutions = [
    {
      title: "E-Commerce & Digital Retail",
      icon: ShoppingBag,
      tag: "High Volume",
      desc: "Extract fresh online retail brands across regional markets (e.g. Mexico, LATAM, US) with verified shopping carts, technology stacks, contact details, and catalog offerings.",
      workflows: [
        "Store catalog & pricing extraction",
        "E-commerce platform detection (Shopify, WooCommerce, Magento)",
        "Direct verified contact email discovery"
      ],
      templateId: "business-directory-extractor"
    },
    {
      title: "B2B SaaS & Tech Startups",
      icon: Globe,
      tag: "High Yield",
      desc: "Discover high-growth software and tech enterprises. Gather Domain Rating, organic traffic trends, executive titles, and technology stack footprints.",
      workflows: [
        "Organic SERP discovery across specific vertical keywords",
        "Domain Authority and backlink profile enrichment",
        "Automated 4-pillar lead prioritization"
      ],
      templateId: "google-search-results-extractor"
    },
    {
      title: "Local Commercial Directories & Regional Leads",
      icon: Building2,
      tag: "Geographic",
      desc: "Scrape commercial directories, yellow page listings, and map cards with phone numbers, physical office addresses, and verified operating domains.",
      workflows: [
        "Regional address & phone parsing",
        "Deep multi-page pagination loops",
        "Canonical business deduplication"
      ],
      templateId: "google-maps-lead-extractor"
    },
    {
      title: "SEO Agencies & Growth Consultancies",
      icon: TrendingUp,
      tag: "Opportunity Scoring",
      desc: "Identify websites with high commercial intent but weak SEO indicators (poor Core Web Vitals, missing metadata, thin content) to position audit and consulting services.",
      workflows: [
        "Website health & speed diagnostic scanning",
        "Meta description & schema audit checks",
        "Integrated pipeline progression in CRM"
      ],
      templateId: "custom-website-url-extractor"
    }
  ];

  return (
    <div className="space-y-10 animate-in fade-in duration-200">
      <div className="text-center max-w-3xl mx-auto py-8">
        <Badge variant="default" size="sm" className="mb-3">TARGETED WORKFLOWS</Badge>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 leading-tight">
          Purpose-Built Solutions for Modern Revenue &amp; Research Teams
        </h1>
        <p className="text-sm sm:text-base text-slate-600 mt-3 leading-relaxed">
          From e-commerce catalog discovery to enterprise SEO opportunity auditing, ProspectOS provides
          ready-to-run workflows tailored to your operational goals.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {solutions.map((s, i) => {
          const Icon = s.icon;
          return (
            <Card key={i} className="p-6 flex flex-col justify-between hover:border-blue-200 transition">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <Badge variant="neutral" size="sm">{s.tag}</Badge>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-2">{s.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed mb-4">{s.desc}</p>

                <div className="space-y-2 mb-6">
                  {s.workflows.map((wf, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-slate-700">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span>{wf}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <Link
                  href={`/templates`}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1.5 transition"
                >
                  Use Template <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  href="/crm"
                  className="text-xs text-slate-500 hover:text-slate-800 transition"
                >
                  View CRM Leads
                </Link>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

