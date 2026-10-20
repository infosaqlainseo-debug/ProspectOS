"use client";

import { useEffect, useState } from "react";
import {
  api,
  SocialConnectionStatus
} from "@/lib/api";
import {
  Share2,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  MessageSquare,
  PhoneCall,
  ExternalLink,
  Lock,
  Sliders,
  Send,
  Info
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

export default function SocialConnectionsPage() {
  const [connections, setConnections] = useState<SocialConnectionStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeModalChannel, setActiveModalChannel] = useState<string | null>(null);

  // Form states for connection modal
  const [accountName, setAccountName] = useState("");
  const [accountId, setAccountId] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [messagingEnabled, setMessagingEnabled] = useState(false);

  const [notice, setNotice] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const showNotice = (type: "success" | "error" | "info", message: string) => {
    setNotice({ type, message });
    setTimeout(() => setNotice(null), 7000);
  };

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    setLoading(true);
    try {
      const data = await api.getSocialConnections();
      setConnections(data);
    } catch (err: any) {
      showNotice("error", err.message || "Failed to load social connections");
    } finally {
      setLoading(false);
    }
  };

  const openConfigModal = (conn: SocialConnectionStatus) => {
    setActiveModalChannel(conn.channel);
    setAccountName(conn.account_name || "");
    setAccountId(conn.account_id || "");
    setPhoneNumber(conn.phone_number || "");
    setAccessToken("");
    setMessagingEnabled(conn.messaging_enabled);
  };

  const handleSaveConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeModalChannel || !accountName.trim()) return;

    setActionLoading(true);
    try {
      await api.connectSocialChannel(activeModalChannel, {
        account_name: accountName.trim(),
        account_id: accountId.trim() || undefined,
        phone_number: phoneNumber.trim() || undefined,
        access_token: accessToken.trim() || undefined,
        messaging_enabled: messagingEnabled
      });
      showNotice("success", `${activeModalChannel} account connection updated successfully.`);
      setActiveModalChannel(null);
      await loadConnections();
    } catch (err: any) {
      showNotice("error", err.message || `Failed to update ${activeModalChannel} connection`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisconnect = async (channel: string) => {
    if (!confirm(`Are you sure you want to disconnect ${channel}?`)) return;
    setActionLoading(true);
    try {
      await api.disconnectSocialChannel(channel);
      showNotice("info", `${channel} disconnected.`);
      await loadConnections();
    } catch (err: any) {
      showNotice("error", err.message || `Failed to disconnect ${channel}`);
    } finally {
      setActionLoading(false);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel.toUpperCase()) {
      case "FACEBOOK":
        return <FacebookIcon className="w-6 h-6 text-blue-600" />;
      case "INSTAGRAM":
        return <InstagramIcon className="w-6 h-6 text-pink-600" />;
      case "WHATSAPP":
        return <PhoneCall className="w-6 h-6 text-emerald-600" />;
      default:
        return <Share2 className="w-6 h-6 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16 px-4 sm:px-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-bold bg-purple-100 text-purple-800 rounded">Module E</span>
            <span className="px-2 py-0.5 text-xs font-bold bg-blue-100 text-blue-800 rounded">Multi-Channel Social</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 flex items-center mt-1">
            <Share2 className="w-7 h-7 mr-3 text-purple-600" /> Social Account Connections
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect authorized business accounts for Facebook Pages, Instagram Professional, and WhatsApp Business.
          </p>
        </div>

        <button
          onClick={loadConnections}
          disabled={loading}
          className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
        >
          <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh Status
        </button>
      </div>

      {/* Safety Notice Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-amber-950">
            Strict Multi-Channel Safety & Opt-In Policy
          </div>
          <p className="text-amber-800 leading-relaxed">
            In compliance with Meta Platform Terms, public social profile links do not constitute consent to receive unsolicited automated messages. Direct API messaging is restricted to authorized accounts and explicit user confirmation. Click-to-chat WhatsApp workflows (<code>https://wa.me/...</code>) are supported for manual user outreach.
          </p>
        </div>
      </div>

      {/* Notification */}
      {notice && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center gap-2.5 ${
            notice.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : notice.type === "error"
              ? "bg-red-50 border-red-200 text-red-800"
              : "bg-blue-50 border-blue-200 text-blue-800"
          }`}
        >
          {notice.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span>{notice.message}</span>
        </div>
      )}

      {/* Social Connection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {connections.map((conn) => {
          const isConnected = conn.connected;
          return (
            <div
              key={conn.channel}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition space-y-4"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg">
                      {getChannelIcon(conn.channel)}
                    </div>
                    <div>
                      <h2 className="font-bold text-slate-900 text-base">{conn.channel}</h2>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {conn.channel === "FACEBOOK"
                          ? "Meta Pages API"
                          : conn.channel === "INSTAGRAM"
                          ? "Instagram Graph API"
                          : "WhatsApp Cloud API"}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      isConnected
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        : "bg-slate-100 text-slate-600 border border-slate-200"
                    }`}
                  >
                    {isConnected ? "CONNECTED" : "DISCONNECTED"}
                  </span>
                </div>

                <div className="space-y-2.5 text-xs pt-2 border-t border-slate-100">
                  <div>
                    <span className="text-slate-500">Connected Account:</span>
                    <div className="font-semibold text-slate-900 mt-0.5">
                      {conn.account_name || "—"}
                    </div>
                  </div>

                  {conn.phone_number && (
                    <div>
                      <span className="text-slate-500">Business Phone:</span>
                      <div className="font-mono text-slate-800 mt-0.5">{conn.phone_number}</div>
                    </div>
                  )}

                  <div>
                    <span className="text-slate-500">Messaging Capability:</span>
                    <div className="mt-0.5 font-medium text-slate-700">
                      {conn.messaging_capability}
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-500">Permissions:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {conn.permissions.map((p) => (
                        <span key={p} className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>

                  {conn.last_error_message && (
                    <div className="p-2 bg-red-50 border border-red-200 rounded text-[11px] text-red-700">
                      <strong>Error:</strong> {conn.last_error_message}
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => openConfigModal(conn)}
                  className="flex-1 py-2 px-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
                >
                  {isConnected ? "Configure / Update" : "Connect Account"}
                </button>
                {isConnected && (
                  <button
                    onClick={() => handleDisconnect(conn.channel)}
                    disabled={actionLoading}
                    className="py-2 px-3 border border-red-200 text-red-600 hover:bg-red-50 rounded-lg text-xs font-semibold transition"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Configuration Modal */}
      {activeModalChannel && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                {getChannelIcon(activeModalChannel)}
                <h3 className="font-bold text-slate-900 text-base">
                  Configure {activeModalChannel} Connection
                </h3>
              </div>
              <button
                onClick={() => setActiveModalChannel(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveConnection} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Account / Page Name *
                </label>
                <input
                  type="text"
                  required
                  value={accountName}
                  onChange={(e) => setAccountName(e.target.value)}
                  placeholder="e.g. GrokxSEO Official"
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Page ID / Business Account ID (Optional)
                </label>
                <input
                  type="text"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  placeholder="e.g. 10928374659283"
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {activeModalChannel === "WHATSAPP" && (
                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    WhatsApp Business Phone Number *
                  </label>
                  <input
                    type="text"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="e.g. +52 55 1234 5678"
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">
                    Include country code. Used for click-to-chat links (https://wa.me/...) and Business Cloud API.
                  </p>
                </div>
              )}

              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  System User / Page Access Token (Protected)
                </label>
                <input
                  type="password"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="Paste Meta Graph Access Token"
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500"
                />
                <p className="mt-1 text-[11px] text-slate-500">
                  Encrypted at rest on the backend. Never exposed to frontend clients.
                </p>
              </div>

              <div className="pt-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={messagingEnabled}
                    onChange={(e) => setMessagingEnabled(e.target.checked)}
                    className="h-4 w-4 text-purple-600 rounded border-slate-300 focus:ring-purple-500"
                  />
                  <span className="font-semibold text-slate-800">
                    Enable Outbound API Messaging (Requires Explicit User Send Confirmation)
                  </span>
                </label>
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setActiveModalChannel(null)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold transition shadow-sm"
                >
                  {actionLoading ? "Saving..." : "Save Connection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
