"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  Bot,
  Sparkles,
  Send,
  Building2,
  ExternalLink,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Layers,
  ArrowRight
} from "lucide-react";
import { crmApi, AIAssistantResponse } from "@/lib/crmApi";

interface Message {
  role: "user" | "assistant";
  content: string;
  responsePayload?: AIAssistantResponse;
  timestamp: string;
}

function AssistantContent() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I am ProspectOS Intelligence. Ask me anything about your central CRM leads, query specific industries or regions, uncover SEO opportunities, or analyze pipeline gaps.",
      timestamp: "Just now"
    }
  ]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // Adaptive Learning Insights
  const [learningInsights, setLearningInsights] = useState<any>(null);
  const [refreshingInsights, setRefreshingInsights] = useState(false);

  const fetchInsights = async () => {
    try {
      setRefreshingInsights(true);
      const res = await crmApi.getLearningInsights();
      setLearningInsights(res);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshingInsights(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const handleSend = async (customText?: string) => {
    const textToSend = customText || query;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      role: "user",
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await crmApi.queryAssistant(textToSend.trim());
      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        responsePayload: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      const errorMsg: Message = {
        role: "assistant",
        content: `Sorry, I encountered an error while querying your CRM database: ${e.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetLearning = async () => {
    if (!confirm("Reset all adaptive scoring weights back to default balanced settings?")) return;
    try {
      await crmApi.resetLearning();
      await fetchInsights();
      alert("Adaptive learning weights have been reset to factory defaults.");
    } catch (e: any) {
      alert(e.message || "Reset failed");
    }
  };

  const suggestionPrompts = [
    "Find Mexican companies with weak SEO",
    "Show high-priority leads with missing emails",
    "What are our top qualified prospects?",
    "Which leads need immediate follow-up?"
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60 flex items-center gap-1">
              <Bot className="w-3 h-3 text-indigo-600" />
              ProspectOS Intelligence
            </span>
            <span className="text-xs text-slate-400 font-mono">Grounded Database AI</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Lead Intelligence Assistant & Adaptive Learning</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Query your central leads database using natural language and inspect continuous adaptive feedback loops.
          </p>
        </div>

        <Link
          href="/crm"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition shadow-sm"
        >
          View All Leads
        </Link>
      </div>

      {/* Main Grid: Interactive Chat (Left) & Adaptive Learning Engine Status (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Natural Language Chat Interface (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-[650px] overflow-hidden">
          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 max-w-2xl ${m.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                    m.role === "user"
                      ? "bg-slate-800 text-white"
                      : "bg-indigo-600 text-white shadow-sm shadow-indigo-500/20"
                  }`}
                >
                  {m.role === "user" ? "U" : <Sparkles className="w-3.5 h-3.5" />}
                </div>

                <div className="space-y-2">
                  <div
                    className={`p-3.5 rounded-xl text-xs leading-relaxed ${
                      m.role === "user"
                        ? "bg-slate-900 text-white rounded-tr-none"
                        : "bg-slate-50 border border-slate-100 text-slate-800 rounded-tl-none shadow-sm"
                    }`}
                  >
                    <p>{m.content}</p>

                    {/* Matched Lead Cards Preview */}
                    {m.responsePayload?.matched_leads && m.responsePayload.matched_leads.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200/80 space-y-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          Cited Database Leads ({m.responsePayload.matched_leads.length})
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {m.responsePayload.matched_leads.map((lead) => (
                            <Link
                              key={lead.id}
                              href={`/crm/leads/${lead.id}`}
                              className="p-2.5 bg-white rounded-lg border border-slate-200 hover:border-indigo-400 transition block text-left group"
                            >
                              <div className="font-bold text-slate-900 group-hover:text-indigo-600 text-xs truncate">
                                {lead.company_name}
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {lead.canonical_domain || "No domain"}
                              </div>
                              <div className="flex items-center justify-between pt-1.5 mt-1 border-t border-slate-50 text-[10px]">
                                <span className="font-mono font-bold text-indigo-700">
                                  Score: {lead.lead_score ? Math.round(lead.lead_score) : "--"}
                                </span>
                                <span className="text-slate-500">{lead.sales_stage}</span>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <span className={`text-[10px] text-slate-400 block px-1 ${m.role === "user" ? "text-right" : ""}`}>
                    {m.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 max-w-lg">
                <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0">
                  <Sparkles className="w-3.5 h-3.5 animate-spin" />
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-500 animate-pulse">
                  Scanning database & synthesizing lead intelligence...
                </div>
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/50 flex flex-wrap gap-1.5">
            {suggestionPrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => handleSend(p)}
                className="text-[11px] font-medium bg-white border border-slate-200 hover:border-indigo-300 text-slate-600 hover:text-indigo-700 px-2.5 py-1 rounded-full transition shadow-sm"
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask ProspectOS Intelligence anything about your leads..."
              className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3.5 py-2 text-xs outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !query.trim()}
              className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 rounded-lg transition shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Column: Adaptive Learning Engine & Preference Weights */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Adaptive Learning System
                </h3>
              </div>
              <button
                onClick={fetchInsights}
                className="text-slate-400 hover:text-slate-600"
                title="Refresh Insights"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${refreshingInsights ? "animate-spin" : ""}`} />
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              ProspectOS monitors reviewer stage overrides, qualifications, and rejections to automatically tune lead scoring weights.
            </p>

            {/* Metrics */}
            {learningInsights && (
              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-base font-bold text-indigo-600">
                    {learningInsights.total_feedback_events}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Feedback Events</div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-base font-bold text-emerald-600">
                    {learningInsights.qualified_count}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Qualifications</div>
                </div>
              </div>
            )}

            {/* Learned Patterns */}
            {learningInsights?.learned_patterns && learningInsights.learned_patterns.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Active Learned Rules
                </span>
                <div className="space-y-2">
                  {learningInsights.learned_patterns.map((p: any, i: number) => (
                    <div key={i} className="p-2.5 bg-indigo-50/50 border border-indigo-100 rounded-lg text-xs space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-indigo-950 text-[11px]">{p.type}</span>
                        <span className="text-[9px] font-mono text-indigo-700 font-semibold">
                          {Math.round(p.confidence * 100)}% Conf
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px] leading-tight">{p.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reset Weights Action */}
            <div className="pt-3 border-t border-slate-100">
              <button
                onClick={handleResetLearning}
                className="w-full text-center text-xs font-semibold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100/70 p-2 rounded-lg transition"
              >
                Reset Adaptive Weights
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AssistantPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-slate-400">Loading Assistant...</div>}>
      <AssistantContent />
    </Suspense>
  );
}
