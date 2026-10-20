"use client";

import { useEffect, useState } from "react";
import {
  api,
  OutreachDraft,
  OutreachCampaign,
  CompanyContact,
  OutreachMessage,
  OutreachSuppression,
  EmailProviderStatus,
  Company,
  MultiChannelDrafts,
  SocialConnectionStatus,
  SocialMessageLog
} from "@/lib/api";
import {
  Mail,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  UserCheck,
  Building2,
  FileText,
  RefreshCw,
  Plus,
  Edit3,
  Ban,
  ExternalLink,
  ChevronRight,
  Eye,
  Info,
  Share2,
  PhoneCall,
  MessageSquare,
  Lock,
  Check,
  RotateCcw,
  Sparkles
} from "lucide-react";

function FacebookIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
    </svg>
  );
}

function InstagramIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
    </svg>
  );
}

export default function OutreachPage() {
  const [activeTab, setActiveTab] = useState<"composer" | "drafts" | "campaigns" | "contacts" | "history">("composer");
  const [providerStatus, setProviderStatus] = useState<EmailProviderStatus | null>(null);
  
  // Data lists
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [campaigns, setCampaigns] = useState<OutreachCampaign[]>([]);
  const [contacts, setContacts] = useState<CompanyContact[]>([]);
  const [messages, setMessages] = useState<OutreachMessage[]>([]);
  const [suppressions, setSuppressions] = useState<OutreachSuppression[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Multi-Channel Outreach Composer States (Module E5)
  const [multiDrafts, setMultiDrafts] = useState<MultiChannelDrafts | null>(null);
  const [loadingMultiDrafts, setLoadingMultiDrafts] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<"facebook" | "instagram" | "whatsapp" | "email">("whatsapp");
  const [composerText, setComposerText] = useState("");
  const [composerSubject, setComposerSubject] = useState("");
  const [composerCta, setComposerCta] = useState("");
  const [composerRecipient, setComposerRecipient] = useState("");
  const [explicitUserConfirmed, setExplicitUserConfirmed] = useState(false);
  const [sendingSocial, setSendingSocial] = useState(false);
  const [socialLogs, setSocialLogs] = useState<SocialMessageLog[]>([]);
  const [socialConns, setSocialConns] = useState<SocialConnectionStatus[]>([]);

  // Modals & Drawers
  const [selectedDraft, setSelectedDraft] = useState<OutreachDraft | null>(null);
  const [editDraftModal, setEditDraftModal] = useState<OutreachDraft | null>(null);
  const [evidenceDrawer, setEvidenceDrawer] = useState<OutreachDraft | null>(null);
  const [sendConfirmModal, setSendConfirmModal] = useState<OutreachDraft | null>(null);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [newCampaignModalOpen, setNewCampaignModalOpen] = useState(false);
  const [newSuppressionModalOpen, setNewSuppressionModalOpen] = useState(false);

  // Form states
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [generateIncludeMediaPlan, setGenerateIncludeMediaPlan] = useState(true);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");
  const [editCta, setEditCta] = useState("");
  const [editSummary, setEditSummary] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [campaignDailyLimit, setCampaignDailyLimit] = useState(20);
  const [campaignFollowUpDays, setCampaignFollowUpDays] = useState(3);
  const [suppressEmail, setSuppressEmail] = useState("");
  const [suppressReason, setSuppressReason] = useState("MANUAL_OPTOUT");

  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const showNotice = (type: "success" | "error" | "info", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 6000);
  };

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [pStatus, dList, cList, contList, mList, sList, compList, sConns] = await Promise.all([
        api.getEmailProviderStatus().catch(() => null),
        api.getDrafts().catch(() => []),
        api.getCampaigns().catch(() => []),
        api.getContacts().catch(() => []),
        api.getOutreachMessages().catch(() => []),
        api.getSuppressions().catch(() => []),
        api.getCompanies().catch(() => []),
        api.getSocialConnections().catch(() => [])
      ]);

      if (pStatus) setProviderStatus(pStatus);
      setDrafts(dList);
      setCampaigns(cList);
      setContacts(contList);
      setMessages(mList);
      setSuppressions(sList);
      setCompanies(compList);
      setSocialConns(sConns);
      if (compList.length > 0 && !selectedCompanyId) {
        setSelectedCompanyId(compList[0].id);
        loadMultiDrafts(compList[0].id);
      }
    } catch (err: any) {
      showNotice("error", err.message || "Failed to load outreach data");
    } finally {
      setLoading(false);
    }
  };

  const loadMultiDrafts = async (companyId: string) => {
    if (!companyId) return;
    setLoadingMultiDrafts(true);
    try {
      const [draftsRes, logsRes] = await Promise.all([
        api.getMultiChannelDrafts(companyId).catch(() => null),
        api.getSocialMessages(companyId).catch(() => [])
      ]);
      if (draftsRes) {
        setMultiDrafts(draftsRes);
        syncChannelDraft(draftsRes, selectedChannel);
      }
      setSocialLogs(logsRes);
    } catch (err: any) {
      console.error("Failed to load multi-channel drafts", err);
    } finally {
      setLoadingMultiDrafts(false);
    }
  };

  const syncChannelDraft = (data: MultiChannelDrafts, channel: "facebook" | "instagram" | "whatsapp" | "email") => {
    const ch = data.drafts[channel];
    if (ch) {
      setComposerText(ch.message_text || "");
      setComposerCta(ch.cta || "");
      setComposerRecipient(ch.recipient || "");
      setComposerSubject((ch as any).subject || "");
      setExplicitUserConfirmed(false);
    }
  };

  const handleChannelChange = (channel: "facebook" | "instagram" | "whatsapp" | "email") => {
    setSelectedChannel(channel);
    if (multiDrafts) {
      syncChannelDraft(multiDrafts, channel);
    }
  };

  const handleCompanySelect = (companyId: string) => {
    setSelectedCompanyId(companyId);
    loadMultiDrafts(companyId);
  };

  const handleSendSocial = async () => {
    if (!selectedCompanyId || !composerText.trim() || !composerRecipient.trim()) {
      showNotice("error", "Company, recipient, and message text are required.");
      return;
    }
    if (!explicitUserConfirmed) {
      showNotice("error", "Explicit user authorization confirmation is required before sending.");
      return;
    }

    setSendingSocial(true);
    try {
      const res = await api.sendSocialMessage({
        company_id: selectedCompanyId,
        channel: selectedChannel.toUpperCase(),
        message_text: composerText.trim(),
        recipient_identifier: composerRecipient.trim(),
        explicit_user_confirmed: true
      });
      showNotice("success", `Message logged to CRM (${res.channel}) for ${res.recipient}. Status: ${res.delivery_status}`);
      const updatedLogs = await api.getSocialMessages(selectedCompanyId).catch(() => []);
      setSocialLogs(updatedLogs);
      setExplicitUserConfirmed(false);
    } catch (err: any) {
      showNotice("error", err.message || "Failed to dispatch message");
    } finally {
      setSendingSocial(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleGenerateDraft = async () => {
    if (!selectedCompanyId) return;
    setActionLoading(true);
    try {
      const draft = await api.generateDraft({
        company_id: selectedCompanyId,
        include_media_plan: generateIncludeMediaPlan,
        save_draft: true
      });
      showNotice("success", `Generated draft for ${draft.recipient_email}`);
      setGenerateModalOpen(false);
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to generate draft");
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async (draftId: string) => {
    setActionLoading(true);
    try {
      await api.approveDraft(draftId, "growth_reviewer", "Human reviewed and verified against evidence.");
      showNotice("success", "Draft approved for sending.");
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to approve draft");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (draftId: string) => {
    const reason = prompt("Enter rejection reason:");
    if (!reason) return;
    setActionLoading(true);
    try {
      await api.rejectDraft(draftId, reason, "growth_reviewer");
      showNotice("info", "Draft rejected.");
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to reject draft");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendConfirm = async () => {
    if (!sendConfirmModal) return;
    setActionLoading(true);
    try {
      const res = await api.sendDraft(sendConfirmModal.id, "authorized_lead");
      if (res.success) {
        showNotice("success", `Email sent successfully to ${res.recipient_email} via ${res.provider}!`);
      } else {
        showNotice("error", `Send aborted: ${res.error}`);
      }
      setSendConfirmModal(null);
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Send failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editDraftModal) return;
    setActionLoading(true);
    try {
      await api.updateDraft(editDraftModal.id, {
        subject_line: editSubject,
        body_text: editBody,
        call_to_action: editCta,
        prospect_summary: editSummary
      });
      showNotice("success", "Draft updated (reverted to unapproved for review).");
      setEditDraftModal(null);
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to update draft");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateCampaign = async () => {
    if (!campaignName) return;
    setActionLoading(true);
    try {
      await api.createCampaign({
        name: campaignName,
        daily_send_limit: campaignDailyLimit,
        follow_up_delay_days: campaignFollowUpDays,
        status: "ACTIVE"
      });
      showNotice("success", `Campaign '${campaignName}' created.`);
      setNewCampaignModalOpen(false);
      setCampaignName("");
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to create campaign");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddSuppression = async () => {
    if (!suppressEmail) return;
    setActionLoading(true);
    try {
      await api.addSuppression({
        email: suppressEmail,
        reason: suppressReason
      });
      showNotice("success", `Suppressed ${suppressEmail}. Any scheduled drafts cancelled.`);
      setNewSuppressionModalOpen(false);
      setSuppressEmail("");
      loadAllData();
    } catch (err: any) {
      showNotice("error", err.message || "Failed to add suppression");
    } finally {
      setActionLoading(false);
    }
  };

  const filteredDrafts = drafts.filter((d) => {
    if (statusFilter === "ALL") return true;
    if (statusFilter === "UNAPPROVED") return d.approval_status === "UNAPPROVED";
    if (statusFilter === "APPROVED") return d.approval_status === "APPROVED" && d.status !== "SENT";
    if (statusFilter === "SENT") return d.status === "SENT";
    return d.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Mail className="h-7 w-7 text-indigo-600" />
            AI Outreach Automation
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Evidence-grounded personalized outreach with mandatory human approval controls and non-fabrication guarantees.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setGenerateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Generate Outreach Draft
          </button>
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between text-sm ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : notification.type === "error"
              ? "bg-red-50 text-red-800 border border-red-200"
              : "bg-blue-50 text-blue-800 border border-blue-200"
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} className="text-gray-400 hover:text-gray-600 font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* Provider Status Banner */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-lg ${
              providerStatus?.is_ready_to_send
                ? "bg-emerald-100 text-emerald-700"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 text-sm">Active Email Provider:</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {providerStatus?.configured_provider || "Checking..."}
              </span>
              {providerStatus?.is_ready_to_send ? (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Ready
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" /> Unconfigured
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {providerStatus?.is_ready_to_send
                ? `Authorized sender: ${providerStatus.sender_email || "System Default"}. Live transmission permitted with human approval.`
                : "No live provider configured. Drafts can be safely created, edited, and approved. External network sends remain blocked until credentials are set in .env."}
            </p>
          </div>
        </div>
        <div className="text-xs text-gray-500 bg-gray-50 px-3 py-2 rounded-lg border border-gray-100">
          <span className="font-medium text-gray-700">Supported:</span> Gmail (OAuth2), SMTP (TLS), Mock
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-6 overflow-x-auto">
          {[
            { id: "composer", label: "Unified Outreach Composer", icon: Share2 },
            { id: "drafts", label: `Drafts & Approvals (${drafts.length})`, icon: FileText },
            { id: "campaigns", label: `Campaigns (${campaigns.length})`, icon: Building2 },
            { id: "contacts", label: `Contacts & Provenance (${contacts.length})`, icon: UserCheck },
            { id: "history", label: `Message History (${messages.length})`, icon: Clock }
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 whitespace-nowrap ${
                  active
                    ? "border-indigo-600 text-indigo-600 font-semibold"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* TAB 0: UNIFIED OUTREACH COMPOSER (Module E5) */}
      {activeTab === "composer" && (
        <div className="space-y-6">
          {/* Prospect Selector & Status Bar */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-600">
                  <Share2 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900">Multi-Channel Outreach Composer</h2>
                  <p className="text-xs text-gray-500">
                    Evidence-grounded personalized messaging for Facebook, Instagram, WhatsApp, and Email.
                  </p>
                </div>
              </div>

              {/* Company Picker */}
              <div className="w-full md:w-80">
                <label className="block text-[11px] font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Select Target Lead:
                </label>
                <select
                  value={selectedCompanyId}
                  onChange={(e) => handleCompanySelect(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg text-xs font-semibold text-gray-900 focus:ring-2 focus:ring-indigo-500"
                >
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.company_name || c.canonical_domain} ({c.country || "Target Market"})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Evidence & Findings Card */}
            {loadingMultiDrafts ? (
              <div className="py-8 text-center text-xs text-gray-500 flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                Loading grounded SEO evidence and drafting multi-channel outreach...
              </div>
            ) : multiDrafts ? (
              <div className="bg-gradient-to-r from-slate-50 to-indigo-50/40 p-4 rounded-xl border border-indigo-100/60 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-gray-900">{multiDrafts.company_name}</span>
                    <span className="text-xs text-gray-500 font-mono">({multiDrafts.domain})</span>
                    {multiDrafts.opportunity_score !== undefined && (
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-100 text-indigo-800">
                        SEO Opp Score: {multiDrafts.opportunity_score}/100
                      </span>
                    )}
                    {multiDrafts.dr_score !== undefined && (
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800">
                        DR: {multiDrafts.dr_score}
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-indigo-700 font-medium">
                    Recommended: <strong>{multiDrafts.recommended_services?.join(", ")}</strong>
                  </div>
                </div>

                <p className="text-xs text-gray-700 leading-relaxed font-medium">
                  {multiDrafts.summary}
                </p>

                {/* Evidence Points */}
                {multiDrafts.evidence_points && multiDrafts.evidence_points.length > 0 && (
                  <div className="pt-2 border-t border-indigo-100/60">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-gray-600 mb-1">
                      Verified Audit Evidence:
                    </div>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-1.5 text-xs text-gray-600">
                      {multiDrafts.evidence_points.map((pt, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                          <span>{pt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Channel Selector & Active Composer */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Channel Tabs */}
            <div className="flex border-b border-gray-200 bg-gray-50/50">
              {[
                { id: "whatsapp", label: "WhatsApp Business", icon: PhoneCall, color: "text-emerald-600" },
                { id: "facebook", label: "Facebook Page", icon: FacebookIcon, color: "text-blue-600" },
                { id: "instagram", label: "Instagram Direct", icon: InstagramIcon, color: "text-pink-600" },
                { id: "email", label: "Cold Email", icon: Mail, color: "text-indigo-600" }
              ].map((ch) => {
                const Icon = ch.icon;
                const isSelected = selectedChannel === ch.id;
                return (
                  <button
                    key={ch.id}
                    onClick={() => handleChannelChange(ch.id as any)}
                    className={`flex-1 py-3 px-4 text-xs font-bold flex items-center justify-center gap-2 border-b-2 transition ${
                      isSelected
                        ? "border-indigo-600 bg-white text-gray-900 shadow-sm"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/60"
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${ch.color}`} />
                    {ch.label}
                  </button>
                );
              })}
            </div>

            {/* Composer Form Body */}
            <div className="p-6 space-y-5">
              {/* Channel Policy Notice */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-indigo-600 shrink-0" />
                  <span>
                    {selectedChannel === "whatsapp" && "WhatsApp Click-to-Chat (https://wa.me/...) enables direct verified outreach. Cloud API messaging requires approved templates and opt-in."}
                    {selectedChannel === "facebook" && "Direct Facebook Messenger requires an authorized Page and eligible conversation window. Public profile can be opened directly."}
                    {selectedChannel === "instagram" && "Instagram Graph API requires business accounts and messaging permissions. Direct profile link supported for manual outreach."}
                    {selectedChannel === "email" && "Email drafts are evidence-grounded. Outbound sending respects system email safety configuration."}
                  </span>
                </div>

                {/* External Link if available */}
                {selectedChannel === "whatsapp" && multiDrafts?.drafts.whatsapp.click_to_chat_url && (
                  <a
                    href={multiDrafts.drafts.whatsapp.click_to_chat_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded shadow-sm whitespace-nowrap ml-3"
                  >
                    <PhoneCall className="w-3.5 h-3.5 mr-1.5" /> Launch WhatsApp Web <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                )}
                {selectedChannel === "facebook" && multiDrafts?.drafts.facebook.recipient && (
                  <a
                    href={multiDrafts.drafts.facebook.recipient}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded shadow-sm whitespace-nowrap ml-3"
                  >
                    Open Page <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                )}
                {selectedChannel === "instagram" && multiDrafts?.drafts.instagram.recipient && (
                  <a
                    href={multiDrafts.drafts.instagram.recipient.startsWith("http") ? multiDrafts.drafts.instagram.recipient : `https://instagram.com/${multiDrafts.drafts.instagram.recipient.replace('@', '')}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center px-3 py-1 bg-pink-600 hover:bg-pink-700 text-white font-bold text-xs rounded shadow-sm whitespace-nowrap ml-3"
                  >
                    Open Profile <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                )}
              </div>

              {/* Recipient Input */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Recipient Identifier *
                  </label>
                  <input
                    type="text"
                    value={composerRecipient}
                    onChange={(e) => setComposerRecipient(e.target.value)}
                    placeholder={
                      selectedChannel === "whatsapp"
                        ? "Phone Number (e.g. +52 55 1234 5678)"
                        : selectedChannel === "email"
                        ? "Recipient Email"
                        : "Profile URL or Username"
                    }
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Call To Action (CTA)
                  </label>
                  <input
                    type="text"
                    value={composerCta}
                    onChange={(e) => setComposerCta(e.target.value)}
                    placeholder="e.g. Can we share a free technical SEO audit report?"
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Subject if Email */}
              {selectedChannel === "email" && (
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Email Subject Line *
                  </label>
                  <input
                    type="text"
                    value={composerSubject}
                    onChange={(e) => setComposerSubject(e.target.value)}
                    placeholder="e.g. Technical SEO observations for example.com"
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-xs font-semibold focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              )}

              {/* Message Body */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Message Body (Evidence-Grounded AI Draft) *
                  </label>
                  <span className="text-[11px] text-gray-400 font-mono">
                    {composerText.length} characters
                  </span>
                </div>
                <textarea
                  rows={6}
                  value={composerText}
                  onChange={(e) => setComposerText(e.target.value)}
                  placeholder="Enter message text..."
                  className="w-full p-3 border border-gray-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-indigo-500 leading-relaxed"
                />
              </div>

              {/* Explicit Authorization & Send Action */}
              <div className="pt-4 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <label className="flex items-start gap-2.5 text-xs text-gray-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={explicitUserConfirmed}
                    onChange={(e) => setExplicitUserConfirmed(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 mt-0.5"
                  />
                  <div>
                    <span className="font-bold text-gray-900">Mandatory Human Send Authorization:</span>
                    <p className="text-gray-500 text-[11px]">
                      I confirm that this outreach message is verified against actual findings and compliant with platform policies.
                    </p>
                  </div>
                </label>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <button
                    onClick={handleSendSocial}
                    disabled={sendingSocial || !explicitUserConfirmed || !composerText.trim()}
                    className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition disabled:opacity-50"
                  >
                    {sendingSocial ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Logging & Dispatching...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Send & Log to CRM
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Social Message Log Table */}
          {socialLogs.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-800">
                Recent Social Outreach Logs for {multiDrafts?.company_name || "Lead"}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 text-gray-600 font-bold text-[10px] uppercase">
                    <tr>
                      <th className="py-2 px-3">Channel</th>
                      <th className="py-2 px-3">Recipient</th>
                      <th className="py-2 px-3">Message Excerpt</th>
                      <th className="py-2 px-3">Status</th>
                      <th className="py-2 px-3">Sent At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {socialLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50">
                        <td className="py-2 px-3 font-semibold text-gray-900">{log.channel}</td>
                        <td className="py-2 px-3 font-mono text-gray-600">{log.recipient_identifier}</td>
                        <td className="py-2 px-3 text-gray-700 max-w-xs truncate">{log.message_text}</td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            {log.delivery_status}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-gray-500 font-mono">
                          {log.sent_at ? new Date(log.sent_at).toLocaleTimeString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 1: DRAFTS & APPROVALS */}
      {activeTab === "drafts" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-lg border border-gray-200">
            <div className="flex gap-2">
              {["ALL", "UNAPPROVED", "APPROVED", "SENT"].map((filterKey) => (
                <button
                  key={filterKey}
                  onClick={() => setStatusFilter(filterKey)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${
                    statusFilter === filterKey
                      ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
                      : "text-gray-600 hover:bg-gray-100 border border-transparent"
                  }`}
                >
                  {filterKey}
                </button>
              ))}
            </div>
            <div className="text-xs text-gray-500">
              Showing {filteredDrafts.length} of {drafts.length} total drafts
            </div>
          </div>

          {/* Drafts List */}
          {filteredDrafts.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <FileText className="h-10 w-10 text-gray-400 mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-gray-900">No outreach drafts found</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                Generate an evidence-backed outreach draft from existing prospect intelligence.
              </p>
              <button
                onClick={() => setGenerateModalOpen(true)}
                className="mt-4 px-3.5 py-2 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
              >
                Generate Draft
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredDrafts.map((draft) => {
                const comp = companies.find((c) => c.id === draft.company_id);
                return (
                  <div
                    key={draft.id}
                    className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:border-gray-300 transition-all space-y-4"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-gray-100 pb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900 text-base">{comp?.name || comp?.company_name || "Prospect"}</span>
                          <span className="text-xs text-gray-400">({comp?.normalized_domain || comp?.canonical_domain || "domain"})</span>
                          <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-medium">
                            Step {draft.sequence_step} {draft.is_follow_up ? "(Follow-Up)" : "(Initial)"}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">
                          Recipient: <span className="font-medium text-gray-700">{draft.recipient_email}</span>
                          {draft.recipient_name && ` (${draft.recipient_name})`}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Approval Status Badge */}
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                            draft.approval_status === "APPROVED"
                              ? "bg-emerald-100 text-emerald-800"
                              : draft.approval_status === "REJECTED"
                              ? "bg-red-100 text-red-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {draft.approval_status}
                        </span>

                        {/* Send Status Badge */}
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                            draft.status === "SENT"
                              ? "bg-blue-100 text-blue-800"
                              : draft.status === "CANCELLED"
                              ? "bg-gray-100 text-gray-600"
                              : draft.status === "FAILED"
                              ? "bg-red-100 text-red-800"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {draft.status}
                        </span>
                      </div>
                    </div>

                    {/* Subject & Summary */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-800">
                        Subject: <span className="font-normal text-gray-900">{draft.subject_line}</span>
                      </h4>
                      {draft.prospect_summary && (
                        <p className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg border border-gray-100 mt-2">
                          <span className="font-semibold text-gray-700">Audit Summary:</span> {draft.prospect_summary}
                        </p>
                      )}
                    </div>

                    {/* Body snippet */}
                    <div className="text-xs text-gray-700 bg-gray-50/60 p-3 rounded-lg border border-gray-100 whitespace-pre-line font-mono max-h-36 overflow-y-auto">
                      {draft.body_text}
                    </div>

                    {/* Actions and Evidence Citations */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEvidenceDrawer(draft)}
                          className="px-3 py-1.5 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg font-medium hover:bg-indigo-100 flex items-center gap-1.5"
                        >
                          <Info className="h-3.5 w-3.5" />
                          View Evidence Citations ({draft.evidence_citations?.length || 0})
                        </button>

                        <button
                          onClick={() => {
                            setEditDraftModal(draft);
                            setEditSubject(draft.subject_line);
                            setEditBody(draft.body_text);
                            setEditCta(draft.call_to_action || "");
                            setEditSummary(draft.prospect_summary || "");
                          }}
                          disabled={draft.status === "SENT"}
                          className="px-3 py-1.5 text-xs bg-white text-gray-700 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1"
                        >
                          <Edit3 className="h-3.5 w-3.5" />
                          Edit Copy
                        </button>
                      </div>

                      {/* Human Review Controls */}
                      <div className="flex items-center gap-2">
                        {draft.approval_status !== "APPROVED" && draft.status !== "SENT" && (
                          <>
                            <button
                              onClick={() => handleReject(draft.id)}
                              disabled={actionLoading}
                              className="px-3 py-1.5 text-xs bg-white text-red-700 border border-red-200 rounded-lg font-medium hover:bg-red-50 disabled:opacity-50"
                            >
                              Reject
                            </button>
                            <button
                              onClick={() => handleApprove(draft.id)}
                              disabled={actionLoading}
                              className="px-3 py-1.5 text-xs bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              Approve Draft
                            </button>
                          </>
                        )}

                        {draft.approval_status === "APPROVED" && draft.status !== "SENT" && (
                          <button
                            onClick={() => setSendConfirmModal(draft)}
                            disabled={actionLoading}
                            className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                          >
                            <Send className="h-3.5 w-3.5" />
                            Send Email
                          </button>
                        )}

                        {draft.status === "SENT" && (
                          <span className="text-xs text-emerald-700 font-medium flex items-center gap-1">
                            <CheckCircle2 className="h-4 w-4" /> Sent at {new Date(draft.sent_at!).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CAMPAIGNS */}
      {activeTab === "campaigns" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-gray-200">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Outreach Campaigns</h3>
              <p className="text-xs text-gray-500">
                Organize prospects, configure rate limits, follow-up intervals, and automatic reply suppression.
              </p>
            </div>
            <button
              onClick={() => setNewCampaignModalOpen(true)}
              className="px-3 py-2 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              New Campaign
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {campaigns.map((camp) => (
              <div key={camp.id} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-gray-900 text-base">{camp.name}</h4>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
                      {camp.status}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 pt-2 border-t border-gray-100">
                  <div>Daily Send Limit: <span className="font-bold text-gray-900">{camp.daily_send_limit}</span></div>
                  <div>Follow-Up Delay: <span className="font-bold text-gray-900">{camp.follow_up_delay_days} days</span></div>
                  <div>Max Follow-Ups: <span className="font-bold text-gray-900">{camp.max_follow_ups}</span></div>
                  <div>Stop on Reply: <span className="font-bold text-gray-900">{camp.stop_on_reply ? "Yes" : "No"}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: CONTACTS & PROVENANCE */}
      {activeTab === "contacts" && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Discovered Business Contacts</h3>
              <p className="text-xs text-gray-500">
                Legitimate public contacts collected from official website pages, security standards, and public records.
              </p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-600">
              <thead className="bg-gray-50 text-gray-700 font-semibold uppercase tracking-wider text-[11px] border-b border-gray-200">
                <tr>
                  <th className="p-3.5">Contact Email</th>
                  <th className="p-3.5">Company</th>
                  <th className="p-3.5">Provenance Source</th>
                  <th className="p-3.5">Verification</th>
                  <th className="p-3.5">Confidence</th>
                  <th className="p-3.5">Opt-Out</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {contacts.map((c) => {
                  const comp = companies.find((co) => co.id === c.company_id);
                  return (
                    <tr key={c.id} className="hover:bg-gray-50/70">
                      <td className="p-3.5 font-medium text-gray-900">{c.email}</td>
                      <td className="p-3.5">{comp?.name || comp?.company_name || c.company_id}</td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 font-mono text-[10px]">
                          {c.source_type}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded-full font-medium ${
                            c.verification_status === "VERIFIED"
                              ? "bg-emerald-100 text-emerald-800"
                              : c.verification_status === "INFERRED"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {c.verification_status}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono">{((c.confidence || 0) * 100).toFixed(0)}%</td>
                      <td className="p-3.5">
                        {c.opt_out ? (
                          <span className="text-red-600 font-bold">YES</span>
                        ) : (
                          <span className="text-emerald-600">No</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: MESSAGE HISTORY & SUPPRESSION */}
      {activeTab === "history" && (
        <div className="space-y-6">
          {/* Suppressions */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-bold text-gray-900">Opt-Out & Suppression List</h3>
                <p className="text-xs text-gray-500">
                  Any emails or domains on this list are permanently blocked from receiving outreach messages.
                </p>
              </div>
              <button
                onClick={() => setNewSuppressionModalOpen(true)}
                className="px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center gap-1"
              >
                <Ban className="h-3.5 w-3.5" />
                Add Opt-Out
              </button>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              {suppressions.map((s) => (
                <div
                  key={s.id}
                  className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs font-medium flex items-center gap-1.5"
                >
                  <Ban className="h-3 w-3" />
                  {s.email} ({s.reason})
                </div>
              ))}
              {suppressions.length === 0 && <span className="text-xs text-gray-400">No suppressions logged.</span>}
            </div>
          </div>

          {/* Audit Log */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-bold text-gray-900">Sent Outreach Audit Trail</h3>
              <p className="text-xs text-gray-500">Immutable record of all sent outreach messages.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-gray-600">
                <thead className="bg-gray-50 text-gray-700 font-semibold uppercase tracking-wider text-[11px] border-b border-gray-200">
                  <tr>
                    <th className="p-3.5">Sent At</th>
                    <th className="p-3.5">Recipient</th>
                    <th className="p-3.5">Subject</th>
                    <th className="p-3.5">Provider</th>
                    <th className="p-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {messages.map((m) => (
                    <tr key={m.id}>
                      <td className="p-3.5 whitespace-nowrap font-mono">{new Date(m.sent_at).toLocaleString()}</td>
                      <td className="p-3.5 font-medium text-gray-900">{m.recipient_email}</td>
                      <td className="p-3.5">{m.subject_line}</td>
                      <td className="p-3.5 font-mono">{m.provider}</td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          {m.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {messages.length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-gray-400">
                        No sent messages in audit history.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Generate New Draft */}
      {generateModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-gray-900 text-lg">Generate Outreach Draft</h3>
            <p className="text-xs text-gray-500">
              Select an existing prospect to assemble evidence from their website scan, opportunity profile, and media plan.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Target Prospect Company</label>
                <select
                  value={selectedCompanyId}
                  onChange={(e) => setSelectedCompanyId(e.target.value)}
                  className="w-full text-xs border border-gray-300 rounded-lg p-2.5 bg-white text-gray-900"
                >
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name || c.company_name} ({c.normalized_domain || c.canonical_domain || "domain"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="incMp"
                  checked={generateIncludeMediaPlan}
                  onChange={(e) => setGenerateIncludeMediaPlan(e.target.checked)}
                  className="rounded border-gray-300 text-indigo-600"
                />
                <label htmlFor="incMp" className="text-xs text-gray-700">
                  Include publisher media plan matches in draft copy
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-gray-100">
              <button
                onClick={() => setGenerateModalOpen(false)}
                className="px-3.5 py-2 text-xs border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateDraft}
                disabled={actionLoading}
                className="px-4 py-2 text-xs bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {actionLoading ? "Generating..." : "Generate & Save Draft"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Evidence Drawer */}
      {evidenceDrawer && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-xl w-full p-6 space-y-4 shadow-xl max-h-[85vh] flex flex-col">
            <div className="flex justify-between items-start border-b border-gray-100 pb-3">
              <div>
                <h3 className="font-bold text-gray-900 text-base">Evidence Provenance Ledger</h3>
                <p className="text-xs text-gray-500">Every claim in the outreach draft is strictly grounded in these audited facts.</p>
              </div>
              <button onClick={() => setEvidenceDrawer(null)} className="text-gray-400 hover:text-gray-600 font-bold">
                ×
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {evidenceDrawer.evidence_citations?.map((cit, idx) => (
                <div key={idx} className="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-indigo-700">{cit.source_type} ({cit.field_name})</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                      Confidence: {(cit.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="font-medium text-gray-900">{cit.claim}</p>
                  <p className="text-[11px] text-gray-500 font-mono truncate">
                    Source ID: {cit.source_id || "Direct Verified Signal"}
                  </p>
                </div>
              ))}
              {(!evidenceDrawer.evidence_citations || evidenceDrawer.evidence_citations.length === 0) && (
                <p className="text-xs text-gray-400 text-center py-6">No explicit citations found.</p>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-gray-100">
              <button
                onClick={() => setEvidenceDrawer(null)}
                className="px-4 py-2 text-xs bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
              >
                Close Ledger
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Edit Copy */}
      {editDraftModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-xl max-h-[90vh] flex flex-col">
            <h3 className="font-bold text-gray-900 text-lg">Edit Outreach Copy</h3>
            <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
              Note: Saving changes will reset approval status to UNAPPROVED to mandate re-verification before sending.
            </p>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Subject Line</label>
                <input
                  type="text"
                  value={editSubject}
                  onChange={(e) => setEditSubject(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 font-mono text-gray-900"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Prospect Summary</label>
                <textarea
                  rows={2}
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 text-gray-900"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Message Body</label>
                <textarea
                  rows={8}
                  value={editBody}
                  onChange={(e) => setEditBody(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 font-mono text-gray-900"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-700 mb-1">Call to Action (CTA)</label>
                <input
                  type="text"
                  value={editCta}
                  onChange={(e) => setEditCta(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 text-gray-900"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => setEditDraftModal(null)}
                className="px-3.5 py-2 text-xs border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={actionLoading}
                className="px-4 py-2 text-xs bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Send Confirmation Safety Gate */}
      {sendConfirmModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center gap-3 text-amber-600">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="font-bold text-gray-900 text-base">Confirm Email Transmission</h3>
            </div>
            
            <p className="text-xs text-gray-600">
              You are authorizing the dispatch of this message to:
            </p>

            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs space-y-1">
              <div><span className="font-semibold text-gray-700">Recipient:</span> {sendConfirmModal.recipient_email}</div>
              <div><span className="font-semibold text-gray-700">Subject:</span> {sendConfirmModal.subject_line}</div>
              <div><span className="font-semibold text-gray-700">Provider:</span> {providerStatus?.configured_provider}</div>
            </div>

            <p className="text-xs text-gray-500">
              Verification checks will run before sending: valid RFC format, opt-out suppression check, duplicate-send cooldown, and campaign rate limits.
            </p>

            <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => setSendConfirmModal(null)}
                className="px-3.5 py-2 text-xs border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSendConfirm}
                disabled={actionLoading}
                className="px-4 py-2 text-xs bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5"
              >
                <Send className="h-3.5 w-3.5" />
                {actionLoading ? "Sending..." : "Authorize & Send"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: New Campaign */}
      {newCampaignModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-gray-900 text-base">Create Outreach Campaign</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Campaign Name</label>
                <input
                  type="text"
                  placeholder="e.g. Q4 SEO Growth - Enterprise SaaS"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-gray-700 mb-1">Daily Send Limit</label>
                  <input
                    type="number"
                    value={campaignDailyLimit}
                    onChange={(e) => setCampaignDailyLimit(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 mb-1">Follow-Up Delay (Days)</label>
                  <input
                    type="number"
                    value={campaignFollowUpDays}
                    onChange={(e) => setCampaignFollowUpDays(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => setNewCampaignModalOpen(false)}
                className="px-3.5 py-2 text-xs border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCampaign}
                disabled={actionLoading || !campaignName}
                className="px-4 py-2 text-xs bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                Create Campaign
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: New Suppression */}
      {newSuppressionModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-gray-900 text-base">Add Opt-Out Suppression</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Email Address to Suppress</label>
                <input
                  type="email"
                  placeholder="contact@company.com"
                  value={suppressEmail}
                  onChange={(e) => setSuppressEmail(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900"
                />
              </div>
              <div>
                <label className="block font-medium text-gray-700 mb-1">Reason</label>
                <select
                  value={suppressReason}
                  onChange={(e) => setSuppressReason(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 bg-white text-gray-900"
                >
                  <option value="MANUAL_OPTOUT">Manual Opt-Out</option>
                  <option value="UNSUBSCRIBED">Unsubscribed</option>
                  <option value="BOUNCED">Hard Bounce</option>
                  <option value="COMPLAINT">Complaint</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => setNewSuppressionModalOpen(false)}
                className="px-3.5 py-2 text-xs border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddSuppression}
                disabled={actionLoading || !suppressEmail}
                className="px-4 py-2 text-xs bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50"
              >
                Add Suppression
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
