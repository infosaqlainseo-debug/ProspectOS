"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import {
  KanbanSquare,
  Search,
  Filter,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  Mail,
  Phone,
  Sparkles,
  Building2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Plus
} from "lucide-react";
import { crmApi, PipelineColumn, CRMLead } from "@/lib/crmApi";

const PIPELINE_STAGES = [
  { id: "NEW", label: "New Leads", color: "bg-slate-100 text-slate-700 border-slate-200" },
  { id: "QUALIFIED", label: "Qualified", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  { id: "RESEARCHED", label: "Researching", color: "bg-blue-50 text-blue-700 border-blue-200" },
  { id: "CONTACTED", label: "Contacted", color: "bg-amber-50 text-amber-700 border-amber-200" },
  { id: "INTERESTED", label: "Interested", color: "bg-purple-50 text-purple-700 border-purple-200" },
  { id: "NEGOTIATION", label: "Negotiation", color: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  { id: "WON", label: "Closed Won", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  { id: "LOST", label: "Lost / Pass", color: "bg-rose-50 text-rose-700 border-rose-200" },
];

function PipelineContent() {
  const [board, setBoard] = useState<Record<string, CRMLead[]>>({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [movingLeadId, setMovingLeadId] = useState<string | null>(null);

  const fetchBoard = async () => {
    try {
      setLoading(true);
      // Fetch leads across all stages
      const res = await crmApi.listLeads({ page_size: 100 });
      const grouped: Record<string, CRMLead[]> = {};
      PIPELINE_STAGES.forEach((s) => { grouped[s.id] = []; });

      (res.items || []).forEach((lead) => {
        const stage = lead.sales_stage.toUpperCase();
        if (grouped[stage]) {
          grouped[stage].push(lead);
        } else if (stage === "REPLIED" || stage === "MEETING_SCHEDULED") {
          // Map sub-stages to INTERESTED or QUALIFIED
          if (grouped["INTERESTED"]) grouped["INTERESTED"].push(lead);
          else grouped["NEW"].push(lead);
        } else {
          // Fallback
          grouped["NEW"].push(lead);
        }
      });

      setBoard(grouped);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoard();
  }, []);

  const handleMoveStage = async (leadId: string, currentStage: string, direction: "next" | "prev") => {
    const stageIds = PIPELINE_STAGES.map((s) => s.id);
    const curIdx = stageIds.indexOf(currentStage.toUpperCase());
    const targetIdx = direction === "next" ? curIdx + 1 : curIdx - 1;

    if (targetIdx < 0 || targetIdx >= stageIds.length) return;
    const newStage = stageIds[targetIdx];

    try {
      setMovingLeadId(leadId);
      await crmApi.updateLeadStage(leadId, newStage, `Moved via Pipeline Kanban to ${newStage}`);
      await fetchBoard();
    } catch (e: any) {
      alert(e.message || "Failed to move stage");
    } finally {
      setMovingLeadId(null);
    }
  };

  return (
    <div className="p-8 max-w-full mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              Interactive Kanban Board
            </span>
            <span className="text-xs text-slate-400 font-mono">8 Visual Stages</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Lead Pipeline & Opportunity Stages</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Visualize progression from fresh discovery through qualification, outreach, and closed engagement.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/crm"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
          >
            Table View
          </Link>
          <button
            onClick={fetchBoard}
            className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-100 rounded-lg transition"
            title="Refresh Board"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Kanban Horizontal Columns Scroll Container */}
      <div className="overflow-x-auto pb-6">
        <div className="flex gap-4 min-w-[1400px]">
          {PIPELINE_STAGES.map((col, idx) => {
            const leadsInCol = (board[col.id] || []).filter((l) =>
              searchQuery
                ? l.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  (l.canonical_domain && l.canonical_domain.toLowerCase().includes(searchQuery.toLowerCase()))
                : true
            );

            return (
              <div
                key={col.id}
                className="w-80 shrink-0 bg-slate-50/80 rounded-xl border border-slate-200 flex flex-col max-h-[78vh]"
              >
                {/* Column Header */}
                <div className="p-3.5 border-b border-slate-200 bg-white rounded-t-xl flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">{col.label}</span>
                    <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                      {leadsInCol.length}
                    </span>
                  </div>
                </div>

                {/* Column Cards Container */}
                <div className="p-3 overflow-y-auto flex-1 space-y-2.5">
                  {leadsInCol.length === 0 ? (
                    <div className="py-8 text-center text-[11px] text-slate-400 border border-dashed border-slate-200 rounded-lg">
                      No leads in {col.label}
                    </div>
                  ) : (
                    leadsInCol.map((lead) => {
                      const isMoving = movingLeadId === lead.id;
                      return (
                        <div
                          key={lead.id}
                          className={`bg-white p-3.5 rounded-lg border border-slate-200/90 shadow-sm hover:shadow transition space-y-2.5 ${
                            isMoving ? "opacity-50 pointer-events-none" : ""
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <Link
                                href={`/crm/leads/${lead.id}`}
                                className="font-bold text-xs text-slate-900 hover:text-indigo-600 transition block leading-snug"
                              >
                                {lead.company_name}
                              </Link>
                              {lead.canonical_domain && (
                                <span className="text-[10px] text-slate-400 font-mono truncate block max-w-[170px]">
                                  {lead.canonical_domain}
                                </span>
                              )}
                            </div>

                            {lead.lead_score !== undefined && lead.lead_score !== null && (
                              <div className="text-right shrink-0">
                                <span className="text-xs font-bold font-mono text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                                  {Math.round(lead.lead_score)}
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Industry / Location */}
                          {(lead.industry || lead.country) && (
                            <div className="text-[11px] text-slate-500 truncate flex items-center gap-1.5">
                              <Building2 className="w-3 h-3 text-slate-400 shrink-0" />
                              <span className="truncate">
                                {[lead.industry, lead.country].filter(Boolean).join(" • ")}
                              </span>
                            </div>
                          )}

                          {/* Quick Contact & Action Bar */}
                          <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[10px]">
                            <div className="flex items-center gap-1.5">
                              {lead.public_email && (
                                <span title={lead.public_email} className="text-emerald-600">
                                  <Mail className="w-3 h-3" />
                                </span>
                              )}
                              {lead.phone_number && (
                                <span title={lead.phone_number} className="text-blue-600">
                                  <Phone className="w-3 h-3" />
                                </span>
                              )}
                            </div>

                            {/* Move Stage Buttons */}
                            <div className="flex items-center gap-1">
                              {idx > 0 && (
                                <button
                                  onClick={() => handleMoveStage(lead.id, col.id, "prev")}
                                  title={`Move back to ${PIPELINE_STAGES[idx - 1].label}`}
                                  className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                                >
                                  <ArrowLeft className="w-3 h-3" />
                                </button>
                              )}
                              {idx < PIPELINE_STAGES.length - 1 && (
                                <button
                                  onClick={() => handleMoveStage(lead.id, col.id, "next")}
                                  title={`Move to ${PIPELINE_STAGES[idx + 1].label}`}
                                  className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition"
                                >
                                  <ArrowRight className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function PipelinePage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-slate-400">Loading Pipeline...</div>}>
      <PipelineContent />
    </Suspense>
  );
}

