"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Globe,
  ChevronLeft,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Shield,
  ExternalLink,
  Edit,
  Save,
  Sliders,
  Check,
  Eye
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  adminApi,
  SEOGlobalConfig,
  SEOPublicPageItem,
  SEOAuditReport
} from "@/lib/adminApi";

export default function SEOControlCenterPage() {
  const [globalConfig, setGlobalConfig] = useState<SEOGlobalConfig | null>(null);
  const [pages, setPages] = useState<SEOPublicPageItem[]>([]);
  const [auditReport, setAuditReport] = useState<SEOAuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [auditLoading, setAuditLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);

  // Active tab
  const [activeTab, setActiveTab] = useState<"pages" | "audit" | "global" | "sitemap">("pages");

  // Selected page for editing & preview
  const [selectedPage, setSelectedPage] = useState<SEOPublicPageItem | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editCanonical, setEditCanonical] = useState("");
  const [editSchema, setEditSchema] = useState("SoftwareApplication");

  const fetchData = async () => {
    try {
      setLoading(true);
      const [cfg, pageList] = await Promise.all([
        adminApi.getSEOGlobalConfig(),
        adminApi.listSEOPages(),
      ]);
      setGlobalConfig(cfg);
      setPages(pageList);
      if (pageList.length > 0 && !selectedPage) {
        setSelectedPage(pageList[0]);
        setEditTitle(pageList[0].meta_title);
        setEditDesc(pageList[0].meta_description);
        setEditCanonical(pageList[0].canonical_url);
        setEditSchema(pageList[0].schema_type);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSelectPage = (p: SEOPublicPageItem) => {
    setSelectedPage(p);
    setEditTitle(p.meta_title);
    setEditDesc(p.meta_description);
    setEditCanonical(p.canonical_url);
    setEditSchema(p.schema_type);
  };

  const handleRunAudit = async () => {
    try {
      setAuditLoading(true);
      const report = await adminApi.runSEOAudit();
      setAuditReport(report);
      setActiveTab("audit");
      await fetchData();
    } catch (e: any) {
      alert(`Audit error: ${e.message}`);
    } finally {
      setAuditLoading(false);
    }
  };

  const handleSavePage = async () => {
    if (!selectedPage) return;
    try {
      setSaveLoading(true);
      await adminApi.saveSEOPage({
        path: selectedPage.path,
        page_name: selectedPage.page_name,
        meta_title: editTitle,
        meta_description: editDesc,
        canonical_url: editCanonical,
        schema_type: editSchema,
        og_title: editTitle,
        og_description: editDesc,
        twitter_card: selectedPage.twitter_card,
        robots_directives: selectedPage.robots_directives,
        sitemap_priority: selectedPage.sitemap_priority,
        change_frequency: selectedPage.change_frequency,
        is_published: selectedPage.is_published,
      });
      alert(`Metadata for ${selectedPage.path} saved and re-audited!`);
      await fetchData();
    } catch (e: any) {
      alert(`Save error: ${e.message}`);
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Link href="/admin" className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-medium">
              <ChevronLeft className="w-3.5 h-3.5" /> Back to Admin
            </Link>
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60">
              SEO Engine
            </span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            SEO Control Center &amp; Metadata Engine
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage public website metadata, live Google SERP snippets, technical Schema.org entities, and automated audits.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAudit}
            disabled={auditLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-[0_1px_2px_rgba(15,23,42,0.06)] transition"
          >
            <Shield className={`w-3.5 h-3.5 ${auditLoading ? "animate-spin" : ""}`} />
            {auditLoading ? "Auditing Pages..." : "Run SEO Audit"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("pages")}
          className={`pb-3 transition border-b-2 ${
            activeTab === "pages"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Page-Level SEO &amp; SERP Preview
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-3 transition border-b-2 flex items-center gap-1.5 ${
            activeTab === "audit"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Technical SEO Audit
          {auditReport && (
            <Badge variant="success" size="sm">
              {auditReport.overall_health_score}%
            </Badge>
          )}
        </button>
        <button
          onClick={() => setActiveTab("global")}
          className={`pb-3 transition border-b-2 ${
            activeTab === "global"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Global Settings &amp; Verification
        </button>
        <button
          onClick={() => setActiveTab("sitemap")}
          className={`pb-3 transition border-b-2 ${
            activeTab === "sitemap"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          XML Sitemap &amp; Robots.txt
        </button>
      </div>

      {/* Tab 1: Page-Level Editor & Google Preview */}
      {activeTab === "pages" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pages List */}
          <Card className="lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle>Public Marketing Routes</CardTitle>
              <CardDescription>Select page to configure metadata</CardDescription>
            </CardHeader>
            <CardContent className="p-2 space-y-1">
              {pages.map((p) => {
                const isSelected = selectedPage?.id === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => handleSelectPage(p)}
                    className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left transition ${
                      isSelected ? "bg-blue-50 border border-blue-200" : "hover:bg-slate-50 border border-transparent"
                    }`}
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-900">{p.page_name}</div>
                      <div className="text-[11px] font-mono text-slate-400">{p.path}</div>
                    </div>
                    <Badge variant={p.audit_score >= 90 ? "success" : "warning"} size="sm">
                      {p.audit_score}/100
                    </Badge>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          {/* Editor & Preview */}
          <div className="lg:col-span-2 space-y-6">
            {selectedPage ? (
              <>
                {/* Google SERP Snippet Preview */}
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-blue-600" />
                      <CardTitle>Live Google SERP Snippet Preview</CardTitle>
                    </div>
                    <Badge variant="neutral" size="sm">Desktop SERP</Badge>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs font-sans">
                      <div className="text-[11px] text-slate-600 truncate mb-0.5 flex items-center gap-1.5">
                        <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-[9px]">P</span>
                        <span>{editCanonical || selectedPage.canonical_url}</span>
                      </div>
                      <h4 className="text-base text-blue-800 hover:underline cursor-pointer font-medium leading-snug line-clamp-1">
                        {editTitle || selectedPage.meta_title}
                      </h4>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                        {editDesc || selectedPage.meta_description}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Edit Form */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle>Edit Metadata for {selectedPage.path}</CardTitle>
                    <CardDescription>Tune titles, descriptions, and structured data schemas</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 text-xs">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="font-semibold text-slate-700">Meta Title</label>
                        <span className={`text-[10px] font-mono ${editTitle.length > 65 ? "text-amber-600 font-bold" : "text-slate-400"}`}>
                          {editTitle.length} / 65 recommended
                        </span>
                      </div>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 focus:bg-white"
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="font-semibold text-slate-700">Meta Description</label>
                        <span className={`text-[10px] font-mono ${editDesc.length > 160 ? "text-amber-600 font-bold" : "text-slate-400"}`}>
                          {editDesc.length} / 160 recommended
                        </span>
                      </div>
                      <textarea
                        rows={3}
                        value={editDesc}
                        onChange={(e) => setEditDesc(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 focus:bg-white"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Canonical URL</label>
                        <input
                          type="text"
                          value={editCanonical}
                          onChange={(e) => setEditCanonical(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 font-mono text-[11px]"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Schema.org Entity</label>
                        <select
                          value={editSchema}
                          onChange={(e) => setEditSchema(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500"
                        >
                          <option value="SoftwareApplication">SoftwareApplication</option>
                          <option value="Product">Product</option>
                          <option value="WebSite">WebSite</option>
                          <option value="Organization">Organization</option>
                          <option value="Article">Article</option>
                        </select>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
                      <button
                        onClick={handleSavePage}
                        disabled={saveLoading}
                        className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
                      >
                        <Save className="w-3.5 h-3.5" />
                        {saveLoading ? "Saving..." : "Save & Re-Audit Metadata"}
                      </button>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">Select a page from the left to configure.</div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Technical SEO Audit */}
      {activeTab === "audit" && (
        <div className="space-y-6">
          {auditReport ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="p-4">
                  <div className="text-xs text-slate-500 mb-1">Overall SEO Health</div>
                  <div className="text-3xl font-extrabold text-emerald-600">{auditReport.overall_health_score}%</div>
                  <div className="text-[11px] text-slate-400 mt-1">{auditReport.total_pages_checked} pages evaluated</div>
                </Card>

                <Card className="p-4">
                  <div className="text-xs text-slate-500 mb-1">Critical Issues</div>
                  <div className="text-3xl font-extrabold text-rose-600">{auditReport.critical_issues_count}</div>
                  <div className="text-[11px] text-slate-400 mt-1">Requires immediate fix</div>
                </Card>

                <Card className="p-4">
                  <div className="text-xs text-slate-500 mb-1">Warnings</div>
                  <div className="text-3xl font-extrabold text-amber-600">{auditReport.warning_issues_count}</div>
                  <div className="text-[11px] text-slate-400 mt-1">SERP truncation risks</div>
                </Card>

                <Card className="p-4">
                  <div className="text-xs text-slate-500 mb-1">Perfect Score Pages</div>
                  <div className="text-3xl font-extrabold text-blue-600">{auditReport.passed_checks_count}</div>
                  <div className="text-[11px] text-slate-400 mt-1">Zero audit issues</div>
                </Card>
              </div>

              {/* Audit Findings Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Page-by-Page Audit Telemetry</CardTitle>
                  <CardDescription>Issues identified with actionable resolution paths</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50/70 border-b border-slate-200/80 text-slate-500 font-semibold">
                        <tr>
                          <th className="py-3 px-4">Route</th>
                          <th className="py-3 px-4">Health</th>
                          <th className="py-3 px-4">Audit Findings</th>
                          <th className="py-3 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {auditReport.pages.map((p) => (
                          <tr key={p.id} className="hover:bg-slate-50/50 transition">
                            <td className="py-3 px-4">
                              <span className="font-semibold text-slate-900">{p.page_name}</span>
                              <span className="font-mono text-[11px] text-slate-400 block">{p.path}</span>
                            </td>
                            <td className="py-3 px-4">
                              <Badge variant={p.audit_score >= 90 ? "success" : "warning"} size="sm">
                                {p.audit_score}/100
                              </Badge>
                            </td>
                            <td className="py-3 px-4">
                              {p.audit_issues.length === 0 ? (
                                <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                                  <CheckCircle2 className="w-3.5 h-3.5" /> All checks passed
                                </span>
                              ) : (
                                <div className="space-y-1">
                                  {p.audit_issues.map((iss, i) => (
                                    <div key={i} className="text-[11px] flex items-center gap-1.5 text-slate-700">
                                      <span className={`w-1.5 h-1.5 rounded-full ${iss.severity === "CRITICAL" ? "bg-rose-500" : "bg-amber-500"}`} />
                                      <span>{iss.message}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => {
                                  setSelectedPage(p);
                                  setActiveTab("pages");
                                }}
                                className="text-blue-600 hover:underline font-semibold"
                              >
                                Edit
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="py-16 text-center text-xs text-slate-500 space-y-3">
              <Shield className="w-8 h-8 text-slate-300 mx-auto" />
              <p>No audit has been run in this session.</p>
              <button
                onClick={handleRunAudit}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition"
              >
                Run Technical SEO Audit Now
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Global Settings & Verification */}
      {activeTab === "global" && (
        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle>Global Search &amp; Social Properties</CardTitle>
            <CardDescription>Default brand metadata and verification codes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Site / Brand Name</label>
              <input
                type="text"
                value={globalConfig?.site_name || "ProspectOS"}
                onChange={(e) => setGlobalConfig(prev => prev ? { ...prev, site_name: e.target.value } : null)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Default Canonical Base Domain</label>
              <input
                type="text"
                value={globalConfig?.default_canonical_domain || "https://prospectos.com"}
                onChange={(e) => setGlobalConfig(prev => prev ? { ...prev, default_canonical_domain: e.target.value } : null)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Google Search Console Verification</label>
                <input
                  type="text"
                  value={globalConfig?.gsc_verification_code || ""}
                  onChange={(e) => setGlobalConfig(prev => prev ? { ...prev, gsc_verification_code: e.target.value } : null)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
                  placeholder="google-site-verification=..."
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">GA4 Measurement ID</label>
                <input
                  type="text"
                  value={globalConfig?.ga4_measurement_id || ""}
                  onChange={(e) => setGlobalConfig(prev => prev ? { ...prev, ga4_measurement_id: e.target.value } : null)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
                  placeholder="G-XXXXXX"
                />
              </div>
            </div>
            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={async () => {
                  if (globalConfig) {
                    await adminApi.updateSEOGlobalConfig(globalConfig);
                    alert("Global SEO configuration updated!");
                  }
                }}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
              >
                Save Global Config
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Live XML Sitemap & Robots.txt Viewer */}
      {activeTab === "sitemap" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Production XML Sitemap</CardTitle>
                <a
                  href="/sitemap.xml"
                  target="_blank"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                >
                  View live <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <CardDescription>Auto-generated from published public marketing routes</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <pre className="p-4 bg-slate-950 text-emerald-400 font-mono text-[11px] rounded-b-xl overflow-x-auto max-h-72">
{`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://prospectos.com/</loc>
    <lastmod>${new Date().toISOString().split("T")[0]}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://prospectos.com/features</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://prospectos.com/solutions</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://prospectos.com/pricing</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://prospectos.com/docs</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>`}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Production robots.txt</CardTitle>
                <a
                  href="/robots.txt"
                  target="_blank"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                >
                  View live <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <CardDescription>Protects private CRM and admin paths from search indexation</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <pre className="p-4 bg-slate-950 text-slate-200 font-mono text-[11px] rounded-b-xl overflow-x-auto max-h-72">
{`User-agent: *
Allow: /
Allow: /features
Allow: /solutions
Allow: /pricing
Allow: /docs
Disallow: /admin
Disallow: /crm
Disallow: /portal
Disallow: /system
Disallow: /api

Sitemap: https://prospectos.com/sitemap.xml`}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

