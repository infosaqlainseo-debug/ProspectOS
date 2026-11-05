"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Plus,
  Trash2,
  Users,
  Search,
  Filter,
  Layers,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  X
} from "lucide-react";
import { crmApi, CRMLeadSegment } from "@/lib/crmApi";

export default function ListsPage() {
  const [segments, setSegments] = useState<CRMLeadSegment[]>([]);
  const [loading, setLoading] = useState(true);

  // Selected segment inspection
  const [selectedSegment, setSelectedSegment] = useState<CRMLeadSegment | null>(null);
  const [segmentLeads, setSegmentLeads] = useState<any[]>([]);
  const [loadingLeads, setLoadingLeads] = useState(false);

  // Create Segment Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [country, setCountry] = useState("");
  const [industry, setIndustry] = useState("");
  const [minScore, setMinScore] = useState<number | "">("");
  const [creating, setCreating] = useState(false);

  const fetchSegments = async () => {
    try {
      setLoading(true);
      const res = await crmApi.listSegments();
      setSegments(res);
      if (res.length > 0 && !selectedSegment) {
        handleInspectSegment(res[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSegments();
  }, []);

  const handleInspectSegment = async (seg: CRMLeadSegment) => {
    setSelectedSegment(seg);
    try {
      setLoadingLeads(true);
      const res = await crmApi.getSegmentLeads(seg.id);
      setSegmentLeads(res.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingLeads(false);
    }
  };

  const handleCreateSegment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const filterCriteria: Record<string, any> = {};
    if (country.trim()) filterCriteria.country = country.trim();
    if (industry.trim()) filterCriteria.industry = industry.trim();
    if (minScore !== "") filterCriteria.min_score = Number(minScore);

    try {
      setCreating(true);
      const created = await crmApi.createSegment({
        name: name.trim(),
        description: description.trim() || undefined,
        is_dynamic: true,
        filter_criteria: filterCriteria,
        color: "indigo"
      });
      setCreateModalOpen(false);
      setName("");
      setDescription("");
      setCountry("");
      setIndustry("");
      setMinScore("");
      await fetchSegments();
      handleInspectSegment(created);
    } catch (e: any) {
      alert(e.message || "Failed to create segment");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSegment = async (id: string) => {
    if (!confirm("Are you sure you want to delete this segment?")) return;
    try {
      await crmApi.deleteSegment(id);
      if (selectedSegment?.id === id) {
        setSelectedSegment(null);
        setSegmentLeads([]);
      }
      await fetchSegments();
    } catch (e: any) {
      alert(e.message || "Failed to delete segment");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Lists & Dynamic Segmentation
            </span>
            <span className="text-xs text-slate-400 font-mono">{segments.length} Saved Segments</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Lead Lists & Target Segments</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Create rule-based dynamic segments and static outreach cohorts automatically populated by the scoring engine.
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm shadow-indigo-500/20"
        >
          <Plus className="w-3.5 h-3.5" />
          Create Segment
        </button>
      </div>

      {/* Main Grid: Segments List (Left) & Qualifying Leads Preview (Right) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        {/* Left: Saved Segments */}
        <div className="space-y-3">
          <div className="text-xs font-bold uppercase text-slate-400 tracking-wider px-1">
            Saved Segments
          </div>

          {loading ? (
            <div className="p-6 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
              Loading segments...
            </div>
          ) : segments.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400 bg-white rounded-xl border border-dashed border-slate-300 space-y-2">
              <p>No custom segments created yet.</p>
              <button
                onClick={() => setCreateModalOpen(true)}
                className="text-indigo-600 font-semibold hover:underline"
              >
                Create your first segment
              </button>
            </div>
          ) : (
            segments.map((seg) => {
              const isSelected = selectedSegment?.id === seg.id;
              return (
                <div
                  key={seg.id}
                  onClick={() => handleInspectSegment(seg)}
                  className={`p-4 rounded-xl border transition cursor-pointer space-y-2 ${
                    isSelected
                      ? "bg-indigo-50/50 border-indigo-300 shadow-sm ring-1 ring-indigo-200"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-xs text-slate-900">{seg.name}</h3>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {seg.description || "Dynamic segment based on criteria"}
                      </p>
                    </div>
                    <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full">
                      {seg.member_count} leads
                    </span>
                  </div>

                  {seg.filter_criteria && Object.keys(seg.filter_criteria).length > 0 && (
                    <div className="flex flex-wrap gap-1 text-[10px]">
                      {Object.entries(seg.filter_criteria).map(([k, v]) => (
                        <span key={k} className="bg-white border border-slate-200 text-slate-600 px-1.5 py-0.2 rounded font-mono">
                          {k}: {String(v)}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                    <span>{seg.is_dynamic ? "Auto-updating" : "Static list"}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSegment(seg.id);
                      }}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Qualifying Leads in Selected Segment */}
        <div className="md:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                {selectedSegment ? selectedSegment.name : "Select a Segment"}
              </h2>
              <p className="text-xs text-slate-500">
                {selectedSegment ? `Showing qualifying leads (${segmentLeads.length})` : "Click on a segment on the left to preview leads"}
              </p>
            </div>
            {selectedSegment && (
              <span className="text-xs font-mono font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                Dynamic Filter Active
              </span>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Company Name</th>
                  <th className="py-2.5 px-3">Industry</th>
                  <th className="py-2.5 px-3">Country</th>
                  <th className="py-2.5 px-3">Score</th>
                  <th className="py-2.5 px-3">Stage</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loadingLeads ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      Loading qualifying segment leads...
                    </td>
                  </tr>
                ) : !selectedSegment ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No segment selected.
                    </td>
                  </tr>
                ) : segmentLeads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No leads currently match this segment's filter criteria.
                    </td>
                  </tr>
                ) : (
                  segmentLeads.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50/70 transition">
                      <td className="py-2.5 px-4 font-bold text-slate-900">
                        <Link href={`/crm/leads/${l.id}`} className="hover:text-indigo-600">
                          {l.company_name}
                        </Link>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">{l.industry || "--"}</td>
                      <td className="py-2.5 px-3 text-slate-600">{l.country || "--"}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">
                        {l.lead_score ? Math.round(l.lead_score) : "--"}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                          {l.sales_stage}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <Link
                          href={`/crm/leads/${l.id}`}
                          className="text-xs font-semibold text-indigo-600 hover:underline"
                        >
                          View Lead
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create Segment Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Create Dynamic Lead Segment</h3>
              <button onClick={() => setCreateModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateSegment} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Segment Name *</label>
                <input
                  required
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Mexico E-Commerce High Priority"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Qualified e-commerce retailers in Mexico with score >= 60"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Country Filter</label>
                  <input
                    type="text"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    placeholder="e.g. Mexico"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Industry Filter</label>
                  <input
                    type="text"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    placeholder="e.g. E-Commerce"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Minimum Lead Score</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minScore}
                  onChange={(e) => setMinScore(e.target.value === "" ? "" : Number(e.target.value))}
                  placeholder="e.g. 60"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-sm"
                >
                  {creating ? "Saving..." : "Create Segment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

