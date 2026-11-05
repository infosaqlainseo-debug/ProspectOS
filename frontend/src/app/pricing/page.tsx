"use client";

import React from "react";
import Link from "next/link";
import { Check, ArrowRight, ShieldCheck, Zap, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PricingPage() {
  const tiers = [
    {
      name: "Starter",
      badge: "Standard",
      price: "$99",
      billing: "/month",
      desc: "For solo growth consultants and boutique agencies starting structured lead extraction.",
      features: [
        "Up to 5,000 extracted records / month",
        "2 concurrent cloud worker nodes",
        "Access to all 10 prebuilt scrapers",
        "Visual workflow builder",
        "Canonical domain deduplication",
        "Standard CRM (up to 2,500 active leads)",
        "CSV & JSON export formats"
      ],
      cta: "Start Free Trial",
      href: "/custom-scraper",
      featured: false
    },
    {
      name: "Professional",
      badge: "Most Popular",
      price: "$249",
      billing: "/month",
      desc: "For scaling revenue teams requiring automated recurring discovery and AI intelligence.",
      features: [
        "Up to 25,000 extracted records / month",
        "5 concurrent cloud worker nodes",
        "Task scheduler (cron automations)",
        "Deep AI Company Research (Gemini/OpenAI)",
        "Interactive 8-stage Kanban Pipeline",
        "4-Pillar Transparent Lead Scoring",
        "Dynamic lists & audience segmentation",
        "Google Drive cloud synchronization"
      ],
      cta: "Launch Professional",
      href: "/custom-scraper",
      featured: true
    },
    {
      name: "Enterprise",
      badge: "Dedicated Cluster",
      price: "Custom",
      billing: "contract",
      desc: "For enterprise data teams requiring dedicated worker clusters, RBAC, and Super Admin control.",
      features: [
        "Unlimited extraction records",
        "Dedicated isolated cloud worker cluster",
        "Super Admin & RBAC Governance Center",
        "SEO Control Center & dynamic sitemaps",
        "Custom LLM inference & air-gapped Ollama",
        "Real-time outbound webhook streaming",
        "Dedicated account architect & SLA",
        "Custom extraction template engineering"
      ],
      cta: "Contact Architecture Team",
      href: "/admin",
      featured: false
    }
  ];

  return (
    <div className="space-y-10 animate-in fade-in duration-200">
      <div className="text-center max-w-3xl mx-auto py-8">
        <Badge variant="default" size="sm" className="mb-3">TRANSPARENT PLANS</Badge>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 leading-tight">
          Cloud Extraction &amp; CRM Intelligence at Predictable Scale
        </h1>
        <p className="text-sm sm:text-base text-slate-600 mt-3 leading-relaxed">
          Choose the extraction capacity and intelligence capabilities that match your growth velocity.
          All plans include verified data provenance and zero synthetic records.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {tiers.map((t, i) => (
          <Card
            key={i}
            className={`p-6 flex flex-col justify-between transition relative ${
              t.featured ? "border-blue-500 shadow-md ring-1 ring-blue-500/20" : "hover:border-slate-300"
            }`}
          >
            {t.featured && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider">
                Recommended Choice
              </div>
            )}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-slate-900">{t.name}</h3>
                <Badge variant={t.featured ? "default" : "neutral"} size="sm">{t.badge}</Badge>
              </div>
              <p className="text-xs text-slate-500 mb-4">{t.desc}</p>

              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-3xl font-extrabold text-slate-900">{t.price}</span>
                <span className="text-xs text-slate-400 font-medium">{t.billing}</span>
              </div>

              <div className="space-y-2.5 pt-4 border-t border-slate-100 mb-6">
                {t.features.map((feat, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            <Link
              href={t.href}
              className={`w-full py-2.5 text-xs font-semibold rounded-lg transition text-center block ${
                t.featured
                  ? "bg-blue-600 text-white hover:bg-blue-700 shadow-xs shadow-blue-500/20"
                  : "bg-slate-100 text-slate-800 hover:bg-slate-200"
              }`}
            >
              {t.cta}
            </Link>
          </Card>
        ))}
      </div>
    </div>
  );
}

