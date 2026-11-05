export interface AdminOverviewStats {
  total_users: number;
  active_users: number;
  suspended_users: number;
  super_admins: number;
  total_organizations: number;
  total_scraping_tasks: number;
  total_extracted_records: number;
  total_crm_leads: number;
  running_background_jobs: number;
  failed_background_jobs: number;
  daily_active_users: number;
  monthly_active_users: number;
}

export interface AdminSystemHealth {
  api_status: string;
  frontend_status: string;
  database_status: string;
  database_tables_count: number;
  database_latency_ms?: number;
  redis_status: string;
  redis_memory_used: string;
  redis_connected_clients: number;
  worker_status: string;
  worker_registered_functions: number;
  cron_schedulers_active: boolean;
  queue_depth: number;
  failed_job_count: number;
  storage_utilization_percent: number;
  last_successful_task?: string | null;
  last_successful_scraping_task?: string | null;
  last_health_check_timestamp?: string | null;
  worker_heartbeat?: string;
  last_backup_timestamp?: string | null;
  last_backup_filename?: string | null;
  last_backup_size_mb?: number | null;
  timestamp: string;
}

export interface AdminOverviewData {
  stats: AdminOverviewStats;
  health: AdminSystemHealth;
  recent_activity: any[];
  system_alerts: any[];
}

export interface AdminUserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  company_id?: string | null;
  company_name?: string | null;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RolePermissionItem {
  id: string;
  role_name: string;
  display_name: string;
  description?: string;
  permissions: Record<string, string[]>;
  is_system_role: boolean;
  updated_at: string;
}

export interface ScraperInfraStatus {
  worker_pool_status: string;
  active_workers_count: number;
  running_jobs: number;
  queued_jobs: number;
  completed_jobs_24h: number;
  failed_jobs_24h: number;
  concurrency_limit: number;
  default_timeout_seconds: number;
  queue_depth: number;
  average_duration_seconds: number;
  retry_policy_max_attempts: number;
}

export interface AIProviderItem {
  id: string;
  provider_name: string;
  display_name: string;
  is_enabled: boolean;
  is_default: boolean;
  default_model: string;
  available_models: string[];
  api_key_masked?: string;
  rpm_limit: number;
  tpm_limit: number;
  tokens_used_today: number;
  total_tokens_used: number;
  estimated_cost_usd: number;
  last_tested_at?: string;
  last_error?: string;
  feature_flags: Record<string, boolean>;
}

export interface IntegrationItem {
  id: string;
  name: string;
  category: string;
  description: string;
  status: string;
  configured: boolean;
  credentials_masked?: string;
  features: string[];
}

export interface SEOGlobalConfig {
  site_name: string;
  default_meta_title: string;
  default_meta_description: string;
  default_canonical_domain: string;
  default_og_image_url?: string;
  robots_txt_content?: string;
  sitemap_enabled: boolean;
  gsc_verification_code?: string;
  ga4_measurement_id?: string;
  bing_verification_code?: string;
}

export interface SEOPublicPageItem {
  id: string;
  path: string;
  page_name: string;
  meta_title: string;
  meta_description: string;
  canonical_url: string;
  og_title?: string;
  og_description?: string;
  og_image_url?: string;
  twitter_card: string;
  robots_directives: string;
  schema_type: string;
  structured_data_json?: any;
  sitemap_priority: number;
  change_frequency: string;
  is_published: boolean;
  last_audited_at?: string;
  audit_score: number;
  audit_issues: Array<{ severity: string; code: string; message: string }>;
}

export interface SEOAuditReport {
  audited_at: string;
  total_pages_checked: number;
  overall_health_score: number;
  critical_issues_count: number;
  warning_issues_count: number;
  passed_checks_count: number;
  pages: SEOPublicPageItem[];
  recommendations: Array<{ title: string; description: string }>;
}

const API_BASE = "";

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("pos_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const adminApi = {
  // Telemetry & Overview
  getOverview: async (): Promise<AdminOverviewData> => {
    const res = await fetch(`${API_BASE}/admin/overview`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load admin overview telemetry");
    return res.json();
  },

  // Users
  listUsers: async (params?: { role?: string; is_active?: boolean; search?: string }): Promise<AdminUserItem[]> => {
    const q = new URLSearchParams();
    if (params?.role) q.append("role", params.role);
    if (params?.is_active !== undefined) q.append("is_active", String(params.is_active));
    if (params?.search) q.append("search", params.search);
    const res = await fetch(`${API_BASE}/admin/users?${q.toString()}`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to list users");
    return res.json();
  },

  createUser: async (data: { email: string; full_name: string; password: string; role: string }): Promise<AdminUserItem> => {
    const res = await fetch(`${API_BASE}/admin/users`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create user");
    }
    return res.json();
  },

  updateUser: async (id: string, data: { full_name?: string; role?: string; is_active?: boolean }): Promise<AdminUserItem> => {
    const res = await fetch(`${API_BASE}/admin/users/${id}`, {
      method: "PATCH",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update user");
    return res.json();
  },

  resetPassword: async (id: string): Promise<{ success: boolean; temporary_token: string; message: string }> => {
    const res = await fetch(`${API_BASE}/admin/users/${id}/reset-password`, {
      method: "POST",
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to reset password");
    return res.json();
  },

  unlockUser: async (id: string): Promise<{ success: boolean; message: string; unlocked_at: string }> => {
    const res = await fetch(`${API_BASE}/admin/users/${id}/unlock`, {
      method: "POST",
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to unlock user account");
    return res.json();
  },

  // Roles & Permissions
  getRoles: async (): Promise<RolePermissionItem[]> => {
    const res = await fetch(`${API_BASE}/admin/roles`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load roles");
    return res.json();
  },

  // Workspaces
  getWorkspaces: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/admin/workspaces`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load workspaces");
    return res.json();
  },

  // Scraper Infra
  getScraperInfraStatus: async (): Promise<ScraperInfraStatus> => {
    const res = await fetch(`${API_BASE}/admin/scraper-infra/status`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load scraper infrastructure status");
    return res.json();
  },

  executeScraperAction: async (action: string, concurrencyLimit?: number): Promise<any> => {
    const res = await fetch(`${API_BASE}/admin/scraper-infra/action`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify({ action, concurrency_limit: concurrencyLimit }),
    });
    if (!res.ok) throw new Error("Failed to execute infrastructure action");
    return res.json();
  },

  getScraperLogs: async (): Promise<{ lines: string[] }> => {
    const res = await fetch(`${API_BASE}/admin/scraper-infra/logs`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to fetch scraper logs");
    return res.json();
  },

  // AI Control
  getAIProviders: async (): Promise<AIProviderItem[]> => {
    const res = await fetch(`${API_BASE}/admin/ai-control`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load AI providers");
    return res.json();
  },

  testAIConnection: async (provider: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/admin/ai-control/test-connection?provider_name=${provider}`, {
      method: "POST",
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to test AI connection");
    return res.json();
  },

  // Integrations
  getIntegrations: async (): Promise<IntegrationItem[]> => {
    const res = await fetch(`${API_BASE}/admin/integrations`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load integrations");
    return res.json();
  },

  testIntegration: async (id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/admin/integrations/${id}/test`, {
      method: "POST",
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to test integration");
    return res.json();
  },

  // SEO Control Center
  getSEOGlobalConfig: async (): Promise<SEOGlobalConfig> => {
    const res = await fetch(`${API_BASE}/admin/seo/global`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load global SEO configuration");
    return res.json();
  },

  updateSEOGlobalConfig: async (config: SEOGlobalConfig): Promise<SEOGlobalConfig> => {
    const res = await fetch(`${API_BASE}/admin/seo/global`, {
      method: "PUT",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("Failed to update global SEO configuration");
    return res.json();
  },

  listSEOPages: async (): Promise<SEOPublicPageItem[]> => {
    const res = await fetch(`${API_BASE}/admin/seo/pages`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load SEO pages");
    return res.json();
  },

  saveSEOPage: async (page: any): Promise<SEOPublicPageItem> => {
    const res = await fetch(`${API_BASE}/admin/seo/pages`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify(page),
    });
    if (!res.ok) throw new Error("Failed to save SEO page metadata");
    return res.json();
  },

  runSEOAudit: async (): Promise<SEOAuditReport> => {
    const res = await fetch(`${API_BASE}/admin/seo/audit`, {
      method: "POST",
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to execute SEO audit");
    return res.json();
  },

  // Platform Settings
  getPlatformSettings: async (): Promise<Record<string, any>> => {
    const res = await fetch(`${API_BASE}/admin/settings`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load platform settings");
    return res.json();
  },

  updatePlatformSettings: async (category: string, settings: Record<string, any>): Promise<any> => {
    const res = await fetch(`${API_BASE}/admin/settings`, {
      method: "PUT",
      headers: getAuthHeaders({ "Content-Type": "application/json", "Accept": "application/json" }),
      body: JSON.stringify({ category, settings }),
    });
    if (!res.ok) throw new Error("Failed to update platform settings");
    return res.json();
  },

  // Audit Logs
  getAuditLogs: async (limit = 50): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/admin/audit-logs?limit=${limit}`, {
      headers: getAuthHeaders({ "Accept": "application/json" }),
    });
    if (!res.ok) throw new Error("Failed to load audit logs");
    return res.json();
  },
};

