"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  UserPlus,
  Shield,
  Key,
  CheckCircle2,
  XCircle,
  MoreVertical,
  RefreshCw,
  AlertTriangle,
  Lock,
  ChevronLeft
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi, AdminUserItem } from "@/lib/adminApi";

export default function UserManagementPage() {
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [resetResult, setResetResult] = useState<{ email: string; token: string } | null>(null);

  // New user form state
  const [newEmail, setNewEmail] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("MEMBER");
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.listUsers({
        search: search.trim() || undefined,
        role: roleFilter || undefined,
      });
      setUsers(res);
    } catch (err: any) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchUsers();
  };

  const handleToggleStatus = async (user: AdminUserItem) => {
    try {
      await adminApi.updateUser(user.id, { is_active: !user.is_active });
      await fetchUsers();
    } catch (err: any) {
      alert(`Error updating user status: ${err.message}`);
    }
  };

  const handleResetPassword = async (user: AdminUserItem) => {
    if (!confirm(`Generate temporary recovery password for ${user.email}?`)) return;
    try {
      const res = await adminApi.resetPassword(user.id);
      setResetResult({ email: user.email, token: res.temporary_token });
    } catch (err: any) {
      alert(`Password reset error: ${err.message}`);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail || !newFullName || !newPassword) {
      alert("Please fill in all required fields.");
      return;
    }
    try {
      setCreateLoading(true);
      await adminApi.createUser({
        email: newEmail,
        full_name: newFullName,
        password: newPassword,
        role: newRole,
      });
      setShowCreateModal(false);
      setNewEmail("");
      setNewFullName("");
      setNewPassword("");
      await fetchUsers();
    } catch (err: any) {
      alert(`Creation error: ${err.message}`);
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/admin" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
              <ChevronLeft className="w-3.5 h-3.5" /> Back to Admin
            </Link>
            <Badge variant="ai" size="sm">RBAC CONTROLS</Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-600" />
            User Administration &amp; RBAC
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Provision user accounts, assign roles, manage tenant status, and generate secure credentials.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchUsers}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-xs shadow-blue-500/20 transition"
          >
            <UserPlus className="w-3.5 h-3.5" />
            Provision User
          </button>
        </div>
      </div>

      {resetResult && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start justify-between gap-3 text-emerald-900 text-xs">
          <div>
            <span className="font-semibold">Temporary Recovery Password Generated:</span>
            <p className="mt-1 font-mono text-sm bg-white/80 p-2 rounded border border-emerald-200 font-bold">
              {resetResult.token}
            </p>
            <p className="text-[11px] text-emerald-700 mt-1">
              Provisioned for {resetResult.email}. User must change this password upon next sign-in.
            </p>
          </div>
          <button
            onClick={() => setResetResult(null)}
            className="text-emerald-700 hover:text-emerald-950 font-bold text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-hidden focus:border-blue-500 focus:bg-white text-slate-900"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 outline-hidden focus:border-blue-500"
            >
              <option value="">All Roles</option>
              <option value="SUPER_ADMIN">Super Admin</option>
              <option value="ADMIN">Administrator</option>
              <option value="MANAGER">Manager</option>
              <option value="MEMBER">Member</option>
              <option value="READ_ONLY">Read Only</option>
            </select>

            <Link
              href="/admin/roles"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition"
            >
              <Shield className="w-3.5 h-3.5 text-blue-600" />
              Role Matrix
            </Link>
          </div>
        </form>
      </Card>

      {/* Users Table */}
      <Card className="border border-slate-200/75 shadow-[0_1px_2px_rgba(15,23,42,0.03)] bg-white overflow-hidden">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/75 border-b border-slate-200/75 text-slate-500 font-medium text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Created</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100/80">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      Loading user accounts...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      No users match the search criteria.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-medium text-slate-900 text-[13px]">{u.full_name}</div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">{u.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        {u.role === "SUPER_ADMIN" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200/60">
                            Super Admin
                          </span>
                        ) : u.role === "ADMIN" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200/60">
                            Admin
                          </span>
                        ) : u.role === "MANAGER" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-600 border border-slate-200/60">
                            Manager
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-50 text-slate-500 border border-slate-200/50">
                            {u.role}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {u.is_active ? (
                          <Badge variant="success" size="sm" dot>Active</Badge>
                        ) : (
                          <Badge variant="destructive" size="sm" dot>Suspended</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => handleResetPassword(u)}
                            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded transition"
                            title="Reset Password"
                          >
                            <Key className="w-3.5 h-3.5 text-blue-600" />
                          </button>
                          <button
                            onClick={() => handleToggleStatus(u)}
                            className={`px-2 py-1 text-[11px] font-medium rounded transition ${
                              u.is_active
                                ? "text-rose-700 hover:bg-rose-50"
                                : "text-emerald-700 hover:bg-emerald-50"
                            }`}
                          >
                            {u.is_active ? "Suspend" : "Activate"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Provision User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 animate-in zoom-in-95 duration-150">
            <h3 className="text-base font-bold text-slate-900 mb-1">Provision Platform Account</h3>
            <p className="text-xs text-slate-500 mb-4">Create a new user with assigned RBAC access privileges.</p>

            <form onSubmit={handleCreateUser} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 focus:bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Business Email</label>
                <input
                  type="email"
                  required
                  placeholder="s.jenkins@prospectos.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 focus:bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Initial Password</label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500 focus:bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Assigned Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 outline-hidden focus:border-blue-500"
                >
                  <option value="MEMBER">Member (Standard discovery and CRM)</option>
                  <option value="MANAGER">Manager (Workflow and assignment control)</option>
                  <option value="ADMIN">Administrator (Infrastructure and user management)</option>
                  <option value="SUPER_ADMIN">Super Admin (Full platform governance)</option>
                  <option value="READ_ONLY">Read Only (Observer access)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition"
                >
                  {createLoading ? "Provisioning..." : "Provision User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

