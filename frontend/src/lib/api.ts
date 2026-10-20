import useSWR from 'swr';
import { SWRConfiguration } from 'swr';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  info: Record<string, unknown>;
  
  constructor(message: string, status: number, info: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.info = info;
  }
}

async function fetcher<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const url = typeof input === 'string' && input.startsWith('/') 
    ? `${API_BASE_URL}${input}`
    : input;
    
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let info;
    try {
      info = await response.json();
    } catch {
      info = { detail: response.statusText };
    }
    throw new ApiError(info.detail || 'An error occurred while fetching data.', response.status, info);
  }

  return response.json();
}

// Swr hook factory
export function useApi<T>(endpoint: string | null, options?: SWRConfiguration) {
  const { data, error, isLoading, mutate } = useSWR<T, ApiError>(
    endpoint,
    fetcher,
    options
  );

  return {
    data,
    error,
    isLoading,
    mutate
  };
}

// Types

export type VerificationStatus = 'VERIFIED' | 'UNVERIFIED' | 'REJECTED' | 'CONTRADICTED';

export interface Company {
  id: string;
  name?: string;
  normalized_domain?: string;
  company_name?: string;
  canonical_domain?: string;
  website_url?: string;
  industry?: string;
  sales_stage?: string;
  target_market?: string;
  country?: string;
  city?: string;
  lead_score?: number;
  lead_score_components?: Record<string, any>;
  recommended_services?: string[];
  seo_summary_findings?: string[];
  gdrive_sync_status?: string;
  gdrive_file_id?: string;
  gdrive_file_url?: string;
  gdrive_synced_at?: string;
  whatsapp_number?: string;
  whatsapp_click_url?: string;
  facebook_url?: string;
  instagram_url?: string;
  phone_number?: string;
  public_email?: string;
  contact_page_url?: string;
  lead_priority?: string;
  lead_owner?: string;
  next_followup_date?: string;
  created_at: string;
  updated_at: string;
  first_discovered_at?: string;
}

export interface SystemOverview {
  total_companies: number;
  websites_analyzed: number;
  total_scans: number;
  total_opportunities: number;
  qualified_leads: number;
  total_publishers: number;
  total_price_observations: number;
  media_plans_created: number;
  active_deals_count: number;
  open_pipeline_usd: number;
  won_deals_count: number;
  won_revenue_usd: number;
  active_jobs: number;
  provider_status: Record<string, any>;
  backup_health: {
    status: string;
    healthy: boolean;
    reason?: string;
    latest_backup?: {
      filename: string;
      size_mb: number;
      sha256: string;
      timestamp_utc: string;
      status: string;
    };
  };
  system_status: string;
  recent_activities: Array<{
    id: string;
    activity_type: string;
    title: string;
    details?: any;
    created_at: string;
    company_name?: string;
    company_domain?: string;
    company_id?: string;
    actor: string;
  }>;
  pipeline_distribution: Record<string, number>;
}

export interface HealthAndBackups {
  status: string;
  database: {
    connected: boolean;
    engine: string;
    database_name: string;
    latency_ms: number;
    status: string;
  };
  redis_queue: {
    connected: boolean;
    engine: string;
    used_memory_human: string;
    connected_clients: number;
    status: string;
  };
  table_counts: Record<string, number>;
  backup_manifest: Array<{
    id: string;
    filename: string;
    filepath: string;
    timestamp_utc: string;
    size_bytes: number;
    size_mb: number;
    sha256: string;
    duration_seconds: number;
    status: string;
    retention_days: number;
    database: string;
  }>;
  latest_backup?: any;
  provider_health: Record<string, any>;
  recent_audit_logs: Array<{
    id: string;
    action: string;
    resource_type: string;
    resource_id?: string;
    company_id?: string;
    user_id?: string;
    ip_address?: string;
    details?: any;
    timestamp: string;
  }>;
}

export interface WebsiteScan {
  id: string;
  company_id: string;
  final_url: string;
  http_status: number;
  is_https: boolean;
  html_metadata: {
    title?: string;
    description?: string;
    h1?: string[];
  };
  technologies: Record<string, string>;
  created_at: string;
}

export interface WebsiteAnalysisResult {
  status: string;
  http_status?: number;
  scanned_at?: string;
  title?: string;
  error_message?: string;
}

export interface Evidence {
  id: string;
  company_id: string;
  attribute_name: string;
  attribute_value: string;
  source_url: string;
  verification_status: VerificationStatus;
  created_at: string;
}

export interface ProviderObservation {
  id: string;
  company_id: string;
  provider: string;
  metric_name: string;
  metric_value: number;
  retrieved_at: string;
  created_at: string;
}

export interface AIObservation {
  id: string;
  company_id: string;
  attribute_name: string;
  attribute_value: string;
  evidence_text: string | null;
  source_url: string | null;
  confidence: number | null;
  verification_status: VerificationStatus;
  created_at: string;
}

export interface AIContradiction {
  id: string;
  company_id: string;
  attribute_name: string;
  existing_value: string;
  new_value: string;
  observation_id: string | null;
  created_at: string;
}

export interface Job {
  id: string;
  job_type: string;
  status: string;
  target_scope: string | null;
  successful_count: number;
  failed_count: number;
  partial_count: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

// API Client object for POST/mutations
export const api = {
  
  // System Overview & Backups
  getSystemOverview: async () => {
    return fetcher<SystemOverview>('/system/overview');
  },
  getHealthAndBackups: async () => {
    return fetcher<HealthAndBackups>('/system/health-and-backups');
  },
  createBackup: async (retentionDays: number = 14) => {
    return fetcher<any>(`/system/backups/create?retention_days=${retentionDays}`, {
      method: 'POST'
    });
  },
  verifyBackup: async (filename?: string) => {
    const q = filename ? `?filename=${encodeURIComponent(filename)}` : '';
    return fetcher<any>(`/system/backups/verify${q}`, {
      method: 'POST'
    });
  },
  importCompany: async (data: { domain: string; company_name?: string; industry?: string; trigger_analysis?: boolean }) => {
    return fetcher<any>('/companies/import', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  post: async <T>(endpoint: string, data: Record<string, unknown>) => {
    return fetcher<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  triggerDiscovery: async (query: string, count: number) => {
    return fetcher<{enqueued_jobs: number}>('/discovery/jobs', {
      method: 'POST',
      body: JSON.stringify({ query, target_count: count })
    });
  },
  triggerAnalysis: async (companyIds: string[]) => {
    return fetcher<{enqueued_jobs: number}>('/analysis/batch', {
      method: 'POST',
      body: JSON.stringify({ company_ids: companyIds })
    });
  },
  triggerEnrichment: async (companyIds: string[]) => {
    return fetcher<{enqueued_jobs: number}>('/enrichment/seo', {
      method: 'POST',
      body: JSON.stringify({ company_ids: companyIds })
    });
  },
  triggerAIExtraction: async (companyIds: string[]) => {
    return fetcher<{enqueued_jobs: number}>('/ai/extraction/batch', {
      method: 'POST',
      body: JSON.stringify({ company_ids: companyIds })
    });
  },
  submitManualOverride: async (companyId: string, attribute: string, value: string, reason: string) => {
    return fetcher<{status: string}>('/ai/extraction/override', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId, attribute, value, reason })
    });
  },
  triggerOpportunityEvaluation: async (companyId: string) => {
    return fetcher<{message: string, job_id: string}>(`/opportunity/evaluate/${companyId}`, {
      method: 'POST',
      body: JSON.stringify({})
    });
  },
  
  // Phase 2.1 Matching
  getCampaignProfile: async (companyId: string) => {
    return fetcher<any>(`/matching/campaigns/prospect/${companyId}/profile`);
  },
  updateCampaignProfile: async (companyId: string, profile: any) => {
    return fetcher<any>(`/matching/campaigns/prospect/${companyId}/profile`, {
      method: 'PUT',
      body: JSON.stringify(profile)
    });
  },
  runMatching: async (companyId: string) => {
    return fetcher<any>(`/matching/runs/${companyId}`, {
      method: 'POST',
      body: JSON.stringify({})
    });
  },
  getMatchingResults: async (runId: string) => {
    return fetcher<any[]>(`/matching/runs/${runId}/results`);
  },
  
  // Phase 2.2 Media Plan
  getCompanyMediaPlans: async (companyId: string) => {
    return fetcher<any[]>(`/media-plans/company/${companyId}`);
  },
  createMediaPlan: async (companyId: string, name: string = "Draft Media Plan") => {
    return fetcher<any>(`/media-plans/company/${companyId}`, {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  },
  getMediaPlan: async (planId: string) => {
    return fetcher<any>(`/media-plans/${planId}`);
  },
  addPublisherToPlan: async (planId: string, publisherId: string, matchResultId?: string) => {
    return fetcher<any>(`/media-plans/${planId}/items`, {
      method: 'POST',
      body: JSON.stringify({ 
        publisher_id: publisherId,
        match_result_id: matchResultId
      })
    });
  },
  removePublisherFromPlan: async (planId: string, itemId: string) => {
    return fetcher<any>(`/media-plans/${planId}/items/${itemId}`, {
      method: 'DELETE'
    });
  },
  exportMediaPlanUrl: (planId: string) => {
    return `${API_BASE_URL}/media-plans/${planId}/export/excel`;
  },

  // Phase 2.3 Workflows
  listWorkflows: async () => {
    return fetcher<Workflow[]>('/workflows/');
  },
  getWorkflow: async (id: string) => {
    return fetcher<Workflow>(`/workflows/${id}`);
  },
  createWorkflow: async (data: Partial<Workflow>) => {
    return fetcher<Workflow>('/workflows/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  updateWorkflow: async (id: string, data: Partial<Workflow>) => {
    return fetcher<Workflow>(`/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  deleteWorkflow: async (id: string) => {
    return fetcher<void>(`/workflows/${id}`, {
      method: 'DELETE'
    });
  },
  startWorkflowRun: async (workflowId: string, options?: { trigger_type?: string, company_ids?: string[], force?: boolean }) => {
    return fetcher<WorkflowRun>(`/workflows/${workflowId}/runs`, {
      method: 'POST',
      body: JSON.stringify(options || {})
    });
  },
  listWorkflowRuns: async (workflowId: string) => {
    return fetcher<WorkflowRun[]>(`/workflows/${workflowId}/runs`);
  },
  getWorkflowRun: async (runId: string) => {
    return fetcher<WorkflowRun>(`/workflows/runs/${runId}`);
  },
  getRunJobs: async (runId: string) => {
    return fetcher<any[]>(`/workflows/runs/${runId}/jobs`);
  },
  cancelWorkflowRun: async (runId: string) => {
    return fetcher<WorkflowRun>(`/workflows/runs/${runId}/cancel`, {
      method: 'POST'
    });
  },
  retryWorkflowRun: async (runId: string) => {
    return fetcher<WorkflowRun>(`/workflows/runs/${runId}/retry`, {
      method: 'POST'
    });
  },
  approveWorkflowRun: async (runId: string, approvedBy?: string, notes?: string) => {
    return fetcher<WorkflowRun>(`/workflows/runs/${runId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_by: approvedBy || 'human_reviewer', notes })
    });
  },
  rejectWorkflowRun: async (runId: string, rejectedBy?: string, reason?: string) => {
    return fetcher<WorkflowRun>(`/workflows/runs/${runId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejected_by: rejectedBy || 'human_reviewer', reason })
    });
  },

  // Phase 2.4 Outreach
  getContacts: async (companyId?: string) => {
    const q = companyId ? `?company_id=${companyId}` : '';
    return fetcher<CompanyContact[]>(`/outreach/contacts${q}`);
  },
  createContact: async (data: any) => {
    return fetcher<CompanyContact>('/outreach/contacts', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  discoverContacts: async (companyId: string) => {
    return fetcher<CompanyContact[]>(`/outreach/contacts/discover/${companyId}`, {
      method: 'POST'
    });
  },
  getCampaigns: async () => {
    return fetcher<OutreachCampaign[]>('/outreach/campaigns');
  },
  createCampaign: async (data: any) => {
    return fetcher<OutreachCampaign>('/outreach/campaigns', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  getDrafts: async (params?: Record<string, any>) => {
    const q = params ? new URLSearchParams(params).toString() : '';
    return fetcher<OutreachDraft[]>(`/outreach/drafts${q ? `?${q}` : ''}`);
  },
  generateDraft: async (data: { company_id: string; contact_id?: string; campaign_id?: string; include_media_plan?: boolean; save_draft?: boolean }) => {
    return fetcher<any>('/outreach/drafts/generate', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  getDraft: async (id: string) => {
    return fetcher<OutreachDraft>(`/outreach/drafts/${id}`);
  },
  updateDraft: async (id: string, data: any) => {
    return fetcher<OutreachDraft>(`/outreach/drafts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  approveDraft: async (id: string, approvedBy?: string, notes?: string) => {
    return fetcher<OutreachDraft>(`/outreach/drafts/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_by: approvedBy || 'human_reviewer', notes })
    });
  },
  rejectDraft: async (id: string, reason: string, rejectedBy?: string) => {
    return fetcher<OutreachDraft>(`/outreach/drafts/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejected_by: rejectedBy || 'human_reviewer', reason })
    });
  },
  sendDraft: async (id: string, authorizedBy?: string, overrideRecipientEmail?: string) => {
    return fetcher<{
      success: boolean;
      draft_id: string;
      message_id?: string;
      provider: string;
      provider_message_id?: string;
      recipient_email: string;
      status: string;
      error?: string;
    }>(`/outreach/drafts/${id}/send`, {
      method: 'POST',
      body: JSON.stringify({
        authorized_by: authorizedBy || 'human_reviewer',
        override_recipient_email: overrideRecipientEmail
      })
    });
  },
  getSuppressions: async () => {
    return fetcher<OutreachSuppression[]>('/outreach/suppressions');
  },
  addSuppression: async (data: { email: string; domain?: string; reason?: string }) => {
    return fetcher<OutreachSuppression>('/outreach/suppressions', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  getOutreachMessages: async (companyId?: string) => {
    const q = companyId ? `?company_id=${companyId}` : '';
    return fetcher<OutreachMessage[]>(`/outreach/messages${q}`);
  },
  getEmailProviderStatus: async () => {
    return fetcher<EmailProviderStatus>('/outreach/provider/status');
  },
  getCompanies: async (limit: number = 100, q?: string) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (q) params.append('q', q);
    const res = await fetcher<{ total: number; items: Company[] }>(`/companies/?${params.toString()}`);
    return (res.items || []).map((c: any) => ({
      ...c,
      company_name: c.company_name || c.name,
      canonical_domain: c.canonical_domain || c.normalized_domain
    }));
  },

  // Phase 2.5 CRM & Pipeline
  getPipelineBoard: async () => {
    return fetcher<PipelineColumn[]>('/crm/pipeline/board');
  },
  getCrmProspects: async (params?: { sales_stage?: string; industry?: string; query?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.sales_stage) q.append('sales_stage', params.sales_stage);
    if (params?.industry) q.append('industry', params.industry);
    if (params?.query) q.append('query', params.query);
    if (params?.limit) q.append('limit', params.limit.toString());
    if (params?.offset) q.append('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return fetcher<{ total: number; limit: number; offset: number; items: UnifiedProspectSummary[] }>(`/crm/prospects${queryStr}`);
  },
  getUnifiedProspectDetail: async (companyId: string) => {
    return fetcher<UnifiedProspectDetail>(`/crm/prospects/${companyId}`);
  },
  updateProspectStage: async (companyId: string, data: { new_stage: string; reason?: string; notes?: string; actor?: string }) => {
    return fetcher<UnifiedProspectDetail>(`/crm/prospects/${companyId}/stage`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  getCrmDeals: async (params?: { company_id?: string; stage?: string; outcome?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.company_id) q.append('company_id', params.company_id);
    if (params?.stage) q.append('stage', params.stage);
    if (params?.outcome) q.append('outcome', params.outcome);
    if (params?.limit) q.append('limit', params.limit.toString());
    if (params?.offset) q.append('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return fetcher<CRMDeal[]>(`/crm/deals${queryStr}`);
  },
  createCrmDeal: async (data: {
    company_id: string;
    deal_name: string;
    service_category?: string;
    stage?: string;
    estimated_value?: number;
    proposed_value?: number;
    currency?: string;
    expected_close_date?: string;
    contact_id?: string;
    media_plan_id?: string;
    notes?: string;
  }) => {
    return fetcher<CRMDeal>('/crm/deals', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  updateCrmDeal: async (dealId: string, data: Partial<CRMDeal> & { actor?: string }) => {
    return fetcher<CRMDeal>(`/crm/deals/${dealId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  getCrmTasks: async (params?: { company_id?: string; deal_id?: string; status?: string; priority?: string; task_type?: string; overdue_only?: boolean; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.company_id) q.append('company_id', params.company_id);
    if (params?.deal_id) q.append('deal_id', params.deal_id);
    if (params?.status) q.append('status', params.status);
    if (params?.priority) q.append('priority', params.priority);
    if (params?.task_type) q.append('task_type', params.task_type);
    if (params?.overdue_only !== undefined) q.append('overdue_only', params.overdue_only.toString());
    if (params?.limit) q.append('limit', params.limit.toString());
    if (params?.offset) q.append('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return fetcher<CRMTask[]>(`/crm/tasks${queryStr}`);
  },
  createCrmTask: async (data: {
    company_id: string;
    title: string;
    description?: string;
    task_type?: string;
    priority?: string;
    status?: string;
    due_date?: string;
    contact_id?: string;
    deal_id?: string;
    idempotency_key?: string;
  }) => {
    return fetcher<CRMTask>('/crm/tasks', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  completeCrmTask: async (taskId: string, data?: { completed_by?: string; completion_notes?: string }) => {
    return fetcher<CRMTask>(`/crm/tasks/${taskId}/complete`, {
      method: 'POST',
      body: JSON.stringify(data || {})
    });
  },
  addProspectNote: async (companyId: string, data: { content: string; deal_id?: string; author?: string }) => {
    return fetcher<CRMNote>(`/crm/prospects/${companyId}/notes`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  getProspectActivities: async (companyId: string, limit: number = 50) => {
    return fetcher<CRMActivity[]>(`/crm/prospects/${companyId}/activities?limit=${limit}`);
  },
  getCrmReportMetrics: async () => {
    return fetcher<CRMReportMetrics>('/crm/reports/metrics');
  },

  // Phase 3.0 Sales Intelligence & Lead Prioritization
  getPrioritizedQueue: async (params?: {
    industry?: string;
    service_fit?: string;
    category?: string;
    min_score?: number;
    review_status?: string;
    crm_stage?: string;
    sort_by?: string;
    sort_desc?: boolean;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.industry) q.append('industry', params.industry);
    if (params?.service_fit) q.append('service_fit', params.service_fit);
    if (params?.category) q.append('category', params.category);
    if (params?.min_score !== undefined) q.append('min_score', params.min_score.toString());
    if (params?.review_status) q.append('review_status', params.review_status);
    if (params?.crm_stage) q.append('crm_stage', params.crm_stage);
    if (params?.sort_by) q.append('sort_by', params.sort_by);
    if (params?.sort_desc !== undefined) q.append('sort_desc', params.sort_desc.toString());
    if (params?.limit) q.append('limit', params.limit.toString());
    if (params?.offset) q.append('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return fetcher<PrioritizedQueueResponse>(`/sales-intelligence/queue${queryStr}`);
  },
  getSalesIntelligenceScore: async (companyId: string) => {
    return fetcher<SalesIntelligenceScore>(`/sales-intelligence/prospects/${companyId}/score`);
  },
  evaluateSalesProspect: async (companyId: string) => {
    return fetcher<SalesIntelligenceScore>(`/sales-intelligence/prospects/${companyId}/evaluate`, {
      method: 'POST'
    });
  },
  getSalesOpportunities: async (companyId: string) => {
    return fetcher<SalesOpportunity[]>(`/sales-intelligence/prospects/${companyId}/opportunities`);
  },
  getSalesBrief: async (companyId: string, forceRegenerate?: boolean) => {
    const q = forceRegenerate ? '?force_regenerate=true' : '';
    return fetcher<SalesBrief>(`/sales-intelligence/prospects/${companyId}/brief${q}`);
  },
  updateSalesBrief: async (companyId: string, data: { markdown: string; edited_by?: string }) => {
    return fetcher<SalesBrief>(`/sales-intelligence/prospects/${companyId}/brief`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  exportSalesBriefUrl: (companyId: string) => {
    return `${API_BASE_URL}/sales-intelligence/prospects/${companyId}/brief/export`;
  },
  overrideProspectScore: async (companyId: string, data: { score: number; reason: string; actor?: string }) => {
    return fetcher<SalesIntelligenceScore>(`/sales-intelligence/prospects/${companyId}/override`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  updateReviewStatus: async (companyId: string, data: { review_status: string; notes?: string; reviewer?: string }) => {
    return fetcher<SalesIntelligenceScore>(`/sales-intelligence/prospects/${companyId}/review-status`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  compareProspects: async (companyIds: string[]) => {
    return fetcher<ProspectComparisonResponse>('/sales-intelligence/compare', {
      method: 'POST',
      body: JSON.stringify({ company_ids: companyIds })
    });
  },
  batchEvaluateSalesIntelligence: async (companyIds: string[]) => {
    return fetcher<{ evaluated_count: number; enqueued_job_id?: string; scores: SalesIntelligenceScore[] }>(
      '/sales-intelligence/batch/evaluate',
      {
        method: 'POST',
        body: JSON.stringify({ company_ids: companyIds })
      }
    );
  },
  // Phase 3.1: Publisher Intelligence & Data Quality
  getPublishers: async (params?: { skip?: number; limit?: number; search?: string; quality_verdict?: string }) => {
    const q = params ? new URLSearchParams(Object.entries(params).filter(([_, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])).toString() : '';
    return fetcher<PublisherRecord[]>(`/publishers/${q ? `?${q}` : ''}`);
  },
  getPublisherQualitySummary: async () => {
    return fetcher<PublisherQualitySummary>('/publishers/quality/summary');
  },
  getPublisherQualityFindings: async (params?: { publisher_id?: string; issue_type?: string; severity?: string; status?: string; limit?: number; offset?: number }) => {
    const q = params ? new URLSearchParams(Object.entries(params).filter(([_, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])).toString() : '';
    return fetcher<PublisherQualityFinding[]>(`/publishers/quality/findings${q ? `?${q}` : ''}`);
  },
  getPublisherQualityDetail: async (publisherId: string) => {
    return fetcher<PublisherDetailedQuality>(`/publishers/${publisherId}/quality`);
  },
  runPublisherQualityAudit: async (publisherId?: string) => {
    return fetcher<{ publisher_id: string; quality_score: PublisherQualityScore; findings: PublisherQualityFinding[] }>(
      '/publishers/quality/audit',
      {
        method: 'POST',
        body: JSON.stringify({ publisher_id: publisherId })
      }
    );
  },
  runBatchPublisherQualityAudit: async (limit: number = 50) => {
    return fetcher<{ audited_count: number; duration_ms: number; enqueued_job_id?: string }>(
      '/publishers/quality/batch-audit',
      {
        method: 'POST',
        body: JSON.stringify({ limit })
      }
    );
  },
  refreshPublisher: async (publisherId: string, options?: { force_refresh?: boolean; providers?: string[] }) => {
    return fetcher<{ publisher_id: string; status: string; refreshed_fields: string[]; logs_count: number; message: string }>(
      `/publishers/${publisherId}/refresh`,
      {
        method: 'POST',
        body: JSON.stringify(options || {})
      }
    );
  },
  applyPublisherManualCorrection: async (publisherId: string, data: {
    field_name: string;
    new_value: string;
    correction_reason: string;
    operator_name?: string;
    currency?: string;
  }) => {
    return fetcher<{ publisher_id: string; updated_field: string; new_value: string; updated_observation_id?: string; message: string }>(
      `/publishers/${publisherId}/manual-correction`,
      {
        method: 'POST',
        body: JSON.stringify(data)
      }
    );
  },
  resolvePublisherQualityFinding: async (findingId: string, data: {
    resolution_status: string;
    resolution_notes: string;
    operator_name?: string;
  }) => {
    return fetcher<PublisherQualityFinding>(
      `/publishers/findings/${findingId}/resolve`,
      {
        method: 'POST',
        body: JSON.stringify(data)
      }
    );
  },
  getPublisherRefreshLogs: async (publisherId?: string, limit: number = 50) => {
    const q = new URLSearchParams();
    if (publisherId) q.append('publisher_id', publisherId);
    q.append('limit', String(limit));
    return fetcher<PublisherRefreshLog[]>(`/publishers/refresh/logs?${q.toString()}`);
  },

  // Module A: Discovery & Scraping
  parseDiscoveryQuery: async (query: string) => {
    return fetcher<NLQueryParseResponse>('/discovery/parse-query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  },
  getDiscoveryTemplates: async () => {
    return fetcher<ScrapingTemplate[]>('/discovery/templates');
  },
  getDiscoverySources: async () => {
    return fetcher<SourceAdapterInfo[]>('/discovery/sources');
  },
  createDiscoveryJob: async (data: {
    query?: string;
    target_count: number;
    country?: string;
    city?: string;
    industry?: string;
    website_url?: string;
    company_size?: string;
    business_type?: string;
    min_opportunity_score?: number;
    max_opportunity_score?: number;
    desired_service?: string;
    template_id?: string;
    source_preferences?: string[];
    exclusion_rules?: string[];
    include_previously_discovered?: boolean;
    min_data_quality?: string;
  }) => {
    return fetcher<{ job_id: string; job_name: string; status: string; requested_count: number }>('/discovery/jobs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  getDiscoveryJobs: async (status?: string, limit: number = 50) => {
    const q = new URLSearchParams();
    if (status) q.append('status', status);
    q.append('limit', String(limit));
    return fetcher<DiscoveryJobDetail[]>(`/discovery/jobs?${q.toString()}`);
  },
  getDiscoveryJob: async (jobId: string) => {
    return fetcher<DiscoveryJobDetail>(`/discovery/jobs/${jobId}`);
  },
  cancelDiscoveryJob: async (jobId: string) => {
    return fetcher<{ message: string; job_id: string; status: string }>(`/discovery/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },
  retryDiscoveryJob: async (jobId: string) => {
    return fetcher<{ message: string; job_id: string; status: string }>(`/discovery/jobs/${jobId}/retry`, {
      method: 'POST',
    });
  },

  // Module D: Google Drive Integration
  getGDriveStatus: async () => {
    return fetcher<GoogleDriveStatus>('/google-drive/status');
  },
  getGDriveAuthUrl: async (clientId: string, redirectUri: string) => {
    const q = new URLSearchParams({ client_id: clientId, redirect_uri: redirectUri });
    return fetcher<{ auth_url: string }>(`/google-drive/auth-url?${q.toString()}`);
  },
  connectGDriveOAuth: async (data: { code: string; client_id: string; client_secret: string; redirect_uri: string }) => {
    return fetcher<{ status: string; account_email: string; master_sheet_url: string }>('/google-drive/connect/oauth', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  connectGDriveManual: async (data: { client_id: string; client_secret: string; refresh_token: string; account_email?: string; selected_folder_path?: string }) => {
    return fetcher<{ status: string; account_email: string; master_sheet_url: string }>('/google-drive/connect/manual', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  disconnectGDrive: async () => {
    return fetcher<{ status: string; message: string }>('/google-drive/disconnect', {
      method: 'POST',
    });
  },
  updateGDriveSettings: async (data: { selected_folder_path?: string; export_format?: string; auto_sync_enabled?: boolean }) => {
    return fetcher<{ status: string; settings: any }>('/google-drive/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  syncCompanyToGDrive: async (companyId: string) => {
    return fetcher<{ status: string; gdrive_file_id: string; gdrive_file_url: string; row_index: number }>(`/google-drive/sync/${companyId}`, {
      method: 'POST',
    });
  },
  syncAllToGDrive: async () => {
    return fetcher<{ message: string; queued: boolean; candidate_count: number }>('/google-drive/sync-all', {
      method: 'POST',
    });
  },
  getGDriveSyncJobs: async (limit: number = 50) => {
    return fetcher<GoogleDriveSyncJob[]>(`/google-drive/jobs?limit=${limit}`);
  },

  // Module E & F: Social Connections & Outreach
  getSocialConnections: async () => {
    return fetcher<SocialConnectionStatus[]>('/social-connections');
  },
  connectSocialChannel: async (channel: string, data: { account_name: string; account_id?: string; phone_number?: string; access_token?: string; messaging_enabled?: boolean; settings_data?: any }) => {
    return fetcher<SocialConnectionStatus>(`/social-connections/${channel.toLowerCase()}/connect`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  disconnectSocialChannel: async (channel: string) => {
    return fetcher<{ status: string; channel: string }>(`/social-connections/${channel.toLowerCase()}/disconnect`, {
      method: 'POST',
    });
  },
  getMultiChannelDrafts: async (companyId: string) => {
    return fetcher<MultiChannelDrafts>(`/outreach/multi-channel-drafts/${companyId}`);
  },
  sendSocialMessage: async (data: { company_id: string; channel: string; message_text: string; recipient_identifier: string; explicit_user_confirmed: boolean; contact_id?: string }) => {
    return fetcher<{ status: string; channel: string; recipient: string; delivery_status: string; message_id?: string }>('/outreach/social-message', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  getSocialMessages: async (companyId?: string) => {
    const q = companyId ? `/${companyId}` : '';
    return fetcher<SocialMessageLog[]>(`/outreach/social-messages${q}`);
  }
};

// Module A: Discovery & Scraping Interfaces
export interface NLQueryParseResponse {
  interpreted_criteria: {
    target_count: number;
    country?: string;
    city?: string;
    industry?: string;
    website_url?: string;
    company_size?: string;
    business_type?: string;
    min_opportunity_score?: number;
    max_opportunity_score?: number;
    desired_services?: string[];
    source_preferences?: string[];
    exclusion_rules?: string[];
    include_previously_discovered: boolean;
    min_data_quality: string;
  };
  suggested_job_name: string;
  source_strategy: string[];
  extraction_targets: string[];
  confidence: number;
  explanation: string;
}

export interface ScrapingTemplate {
  id: string;
  name: string;
  target_market: string;
  industry: string;
  default_target_count: number;
  recommended_services: string[];
  description: string;
  sources: string[];
  extraction_fields: string[];
  validation_rules: Record<string, any>;
  scoring_focus: string;
  requires_paid_apis: boolean;
  required_api_names: string[];
}

export interface SourceAdapterInfo {
  name: string;
  source_type: string;
  is_available: boolean;
  rate_limit: string;
  description: string;
  supported_fields: string[];
  requires_config: boolean;
  config_status: string;
}

export interface DiscoveryJobDetail {
  id: string;
  job_name?: string;
  status: string;
  current_stage?: string;
  requested_count: number;
  leads_discovered: number;
  leads_validated: number;
  duplicates_skipped: number;
  records_rejected: number;
  websites_analyzed: number;
  leads_saved: number;
  gdrive_synced_count: number;
  sources_used: string[];
  error_summary?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  parameters?: Record<string, any>;
}

// Module D: Google Drive Interfaces
export interface GoogleDriveStatus {
  connected: boolean;
  account_email?: string;
  selected_folder_path: string;
  master_sheet_id?: string;
  master_sheet_url?: string;
  export_format: string;
  auto_sync_enabled: boolean;
  last_successful_sync?: string;
  last_error_message?: string;
  total_synced_records: number;
}

export interface GoogleDriveSyncJob {
  id: string;
  company_id: string;
  company_name: string;
  status: string;
  gdrive_file_id?: string;
  gdrive_file_url?: string;
  error_message?: string;
  retry_count: number;
  sync_started_at?: string;
  sync_completed_at?: string;
}

// Module E & F: Social Outreach Interfaces
export interface SocialConnectionStatus {
  channel: string;
  connected: boolean;
  account_name?: string;
  account_id?: string;
  phone_number?: string;
  messaging_enabled: boolean;
  messaging_capability: string;
  token_expiry?: string;
  last_successful_operation?: string;
  last_error_message?: string;
  permissions: string[];
}

export interface MultiChannelDrafts {
  company_id: string;
  company_name: string;
  domain: string;
  industry?: string;
  country?: string;
  dr_score?: number;
  opportunity_score?: number;
  recommended_services: string[];
  summary: string;
  evidence_points: string[];
  drafts: {
    facebook: {
      channel: string;
      eligible: boolean;
      recipient: string;
      message_text: string;
      cta: string;
      notes: string;
    };
    instagram: {
      channel: string;
      eligible: boolean;
      recipient: string;
      message_text: string;
      cta: string;
      notes: string;
    };
    whatsapp: {
      channel: string;
      eligible: boolean;
      recipient: string;
      message_text: string;
      cta: string;
      click_to_chat_url?: string;
      notes: string;
    };
    email: {
      channel: string;
      eligible: boolean;
      recipient: string;
      subject: string;
      message_text: string;
      cta: string;
      notes: string;
    };
  };
}

export interface SocialMessageLog {
  id: string;
  company_id: string;
  channel: string;
  sender_account?: string;
  recipient_identifier: string;
  message_text: string;
  delivery_status: string;
  error_details?: string;
  sent_at?: string;
}

export interface Workflow {
  id: string;
  name: string;
  discovery_query?: string | null;
  target_company_count?: number | null;
  selected_company_ids?: string[] | null;
  enabled_stages: string[];
  schedule_cron?: string | null;
  schedule_timezone?: string | null;
  last_run_at?: string | null;
  batch_size?: number | null;
  provider_request_limits?: Record<string, number> | null;
  max_retries?: number | null;
  retry_backoff_seconds?: number | null;
  max_runtime_seconds?: number | null;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  trigger_type: string;
  status: string;
  current_stage?: string | null;
  total_companies: number;
  successful_companies: number;
  failed_companies: number;
  skipped_stages?: string[] | null;
  retry_counts?: Record<string, number> | null;
  provider_failures?: Record<string, string> | null;
  stage_progress?: Record<string, {
    status: string;
    started_at?: string | null;
    completed_at?: string | null;
    total_items?: number;
    successful_items?: number;
    failed_items?: number;
    error_message?: string | null;
    notes?: string | null;
    approved_by?: string | null;
  }> | null;
  parameters?: Record<string, any> | null;
  error_summary?: string | null;
  planned_run_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
}

export interface OpportunityProfile {
  id: string;
  company_id: string;
  recommended_service: string;
  opportunity_score: number;
  supporting_evidence: Record<string, any>[];
  identified_problems: string[];
  confidence_level: number;
  data_freshness: string;
  missing_information: string[];
  recommended_next_action: string | null;
  methodology_version: string;
  calculation_timestamp: string;
  created_at: string;
}

export interface CompanyContact {
  id: string;
  company_id: string;
  email?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  full_name?: string | null;
  job_title?: string | null;
  department?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  source_type: string;
  source_url?: string | null;
  retrieval_timestamp: string;
  verification_status: string;
  confidence?: number | null;
  is_primary: boolean;
  opt_out: boolean;
  opt_out_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutreachCampaign {
  id: string;
  name: string;
  description?: string | null;
  status: string;
  daily_send_limit: number;
  schedule_timezone: string;
  follow_up_delay_days: number;
  max_follow_ups: number;
  stop_on_reply: boolean;
  stop_on_bounce: boolean;
  stop_on_unsubscribe: boolean;
  template_subject?: string | null;
  template_body?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutreachDraft {
  id: string;
  campaign_id?: string | null;
  company_id: string;
  contact_id?: string | null;
  recipient_email: string;
  recipient_name?: string | null;
  subject_line: string;
  body_text: string;
  body_html?: string | null;
  call_to_action?: string | null;
  prospect_summary?: string | null;
  evidence_citations?: Array<{
    claim: string;
    source_type: string;
    source_id?: string | null;
    field_name: string;
    value: any;
    confidence: number;
  }> | null;
  status: string;
  approval_status: string;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  is_follow_up: boolean;
  sequence_step: number;
  parent_draft_id?: string | null;
  scheduled_send_at?: string | null;
  sent_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutreachMessage {
  id: string;
  draft_id: string;
  campaign_id?: string | null;
  company_id: string;
  contact_id?: string | null;
  provider: string;
  provider_message_id?: string | null;
  sender_email: string;
  recipient_email: string;
  subject_line: string;
  body_text: string;
  status: string;
  delivery_error?: string | null;
  sent_at: string;
  opened_at?: string | null;
  replied_at?: string | null;
  bounced_at?: string | null;
  unsubscribed_at?: string | null;
  created_at: string;
}

export interface OutreachSuppression {
  id: string;
  email: string;
  domain?: string | null;
  reason: string;
  source?: string | null;
  created_at: string;
}

export interface EmailProviderStatus {
  configured_provider: string;
  is_ready_to_send: boolean;
  sender_email?: string | null;
  missing_configuration: string[];
  supported_providers: string[];
}

// ==========================================
// Phase 2.5 CRM Types
// ==========================================

export type SalesStage =
  | 'NEW'
  | 'RESEARCHED'
  | 'QUALIFIED'
  | 'CONTACTED'
  | 'REPLIED'
  | 'MEETING_SCHEDULED'
  | 'PROPOSAL_SENT'
  | 'NEGOTIATION'
  | 'WON'
  | 'LOST'
  | 'NURTURE';

export type DealStage =
  | 'DISCOVERY'
  | 'QUALIFICATION'
  | 'PROPOSAL'
  | 'NEGOTIATION'
  | 'WON'
  | 'LOST';

export type DealOutcome = 'OPEN' | 'WON' | 'LOST';

export type TaskType =
  | 'CALL'
  | 'MEETING'
  | 'RESEARCH'
  | 'FOLLOW_UP'
  | 'EMAIL'
  | 'OTHER';

export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type TaskStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface CRMDeal {
  id: string;
  company_id: string;
  deal_name: string;
  service_category: string;
  stage: string;
  estimated_value: number;
  proposed_value?: number | null;
  closed_amount?: number | null;
  currency: string;
  expected_close_date?: string | null;
  actual_close_date?: string | null;
  outcome?: string | null;
  loss_reason?: string | null;
  win_reason?: string | null;
  contact_id?: string | null;
  media_plan_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CRMTask {
  id: string;
  company_id: string;
  title: string;
  description?: string | null;
  task_type: string;
  priority: string;
  status: string;
  due_date?: string | null;
  completed_at?: string | null;
  completed_by?: string | null;
  completion_notes?: string | null;
  contact_id?: string | null;
  deal_id?: string | null;
  idempotency_key?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CRMActivity {
  id: string;
  company_id: string;
  deal_id?: string | null;
  contact_id?: string | null;
  activity_type: string;
  actor: string;
  title: string;
  details?: Record<string, any> | null;
  created_at: string;
}

export interface CRMNote {
  id: string;
  company_id: string;
  deal_id?: string | null;
  author: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface UnifiedProspectSummary {
  id: string;
  company_name?: string | null;
  canonical_domain?: string | null;
  website_url?: string | null;
  industry?: string | null;
  target_market?: string | null;
  country?: string | null;
  sales_stage: string;
  stage_updated_at: string;
  stage_reason?: string | null;
  opportunity_score?: number | null;
  lead_score?: number | null;
  recommended_service?: string | null;
  gdrive_sync_status?: string | null;
  gdrive_file_url?: string | null;
  whatsapp_number?: string | null;
  whatsapp_click_url?: string | null;
  facebook_url?: string | null;
  instagram_url?: string | null;
  total_deals: number;
  open_deal_value: number;
  pending_tasks_count: number;
  verified_contacts_count: number;
  created_at: string;
}

export interface UnifiedProspectDetail {
  company: Record<string, any>;
  sales_stage: string;
  stage_updated_at: string;
  stage_reason?: string | null;
  target_market?: string | null;
  qualification_notes?: string | null;
  opportunity_profile?: Record<string, any> | null;
  website_scan?: Record<string, any> | null;
  contacts: any[];
  media_plans: any[];
  outreach_drafts: any[];
  outreach_messages: any[];
  deals: CRMDeal[];
  tasks: CRMTask[];
  notes: CRMNote[];
  activities: CRMActivity[];
}

export interface PipelineColumn {
  stage: string;
  stage_name: string;
  prospects_count: number;
  open_deals_count: number;
  total_pipeline_value: number;
  prospects: UnifiedProspectSummary[];
}

export interface CRMReportMetrics {
  prospects_by_stage: Record<string, number>;
  total_prospects: number;
  qualified_prospects_count: number;
  outreach_sent_count: number;
  replies_received_count: number;
  meetings_scheduled_count: number;
  proposals_sent_count: number;
  won_deals_count: number;
  lost_deals_count: number;
  open_pipeline_value: number;
  closed_won_revenue: number;
  pipeline_currency: string;
  conversion_rates: Record<string, number | null>;
  notes: string[];
}

// Phase 3.0 Sales Intelligence Interfaces
export interface SalesOpportunity {
  id: string;
  company_id: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  impact_rationale: string;
  confidence: number;
  recommended_service: string;
  supporting_evidence: Array<Record<string, any>>;
  status: string;
  detection_rule?: string | null;
  detection_timestamp: string;
}

export interface SalesIntelligenceScore {
  id: string;
  company_id: string;
  company_name?: string | null;
  canonical_domain?: string | null;
  overall_priority_score: number;
  scoring_version: string;
  seo_severity_score: number;
  service_fit_score: number;
  publisher_fit_score: number;
  business_fit_score: number;
  evidence_confidence_score: number;
  primary_recommended_service: string;
  service_fit_breakdown: Record<string, number>;
  positive_indicators: string[];
  limitations: string[];
  missing_information: string[];
  recommended_next_action: string;
  scoring_weights_used: Record<string, number>;
  human_override_score?: number | null;
  human_override_reason?: string | null;
  human_override_by?: string | null;
  human_override_at?: string | null;
  review_status: string;
  review_notes?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  evaluated_at: string;
}

export interface SalesBrief {
  id: string;
  company_id: string;
  title: string;
  company_overview: Record<string, any>;
  seo_findings_summary: Record<string, any>;
  top_opportunities: Array<{
    id?: string;
    category: string;
    title: string;
    severity: string;
    recommended_service: string;
  }>;
  service_recommendations: Array<{
    service: string;
    fit_score: number;
    rationale: string;
  }>;
  matched_publishers: Array<{
    publisher_name: string;
    canonical_domain?: string;
    da?: number;
    dr?: number;
    price?: number;
    currency?: string;
  }>;
  data_gaps: string[];
  discovery_questions: string[];
  recommended_next_action: string;
  full_brief_markdown: string;
  is_customized: boolean;
  version: number;
  last_edited_by?: string | null;
  last_edited_at?: string | null;
  created_at: string;
}

export interface PrioritizedProspectItem {
  company_id: string;
  company_name: string;
  canonical_domain?: string | null;
  website_url?: string | null;
  industry?: string | null;
  sales_stage: string;
  effective_score: number;
  overall_priority_score: number;
  human_override_score?: number | null;
  human_override_reason?: string | null;
  review_status: string;
  primary_recommended_service: string;
  seo_severity_score: number;
  service_fit_score: number;
  publisher_fit_score: number;
  business_fit_score: number;
  evidence_confidence_score: number;
  critical_opportunities_count: number;
  total_opportunities_count: number;
  evaluated_at?: string | null;
}

export interface PrioritizedQueueResponse {
  total: number;
  limit: number;
  offset: number;
  items: PrioritizedProspectItem[];
}

export interface ProspectComparisonDetail {
  company_id: string;
  company_name: string;
  canonical_domain?: string | null;
  industry?: string | null;
  sales_stage: string;
  effective_score: number;
  primary_recommended_service: string;
  service_fits: Record<string, number>;
  opportunities_count_by_category: Record<string, number>;
  top_opportunities: string[];
  matched_publisher_count: number;
  review_status: string;
}

export interface ProspectComparisonResponse {
  compared_prospects: ProspectComparisonDetail[];
  comparison_timestamp: string;
}

// Phase 3.1: Publisher Intelligence & Data Quality Interfaces

export interface PublisherRecord {
  id: string;
  company_id: string;
  original_submitted_url?: string | null;
  publisher_name?: string | null;
  audience_focus?: string | null;
  status: string;
  created_at: string;
  canonical_domain?: string | null;
  price?: number | null;
  currency?: string | null;
  metric_da?: number | null;
  metric_dr?: number | null;
  metric_traffic?: number | null;
  quality_overall_score?: number | null;
  quality_verdict?: string | null;
  has_duplicates?: boolean | null;
  is_stale?: boolean | null;
}

export interface PublisherQualityFinding {
  id: string;
  publisher_id: string;
  issue_type: string;
  field_name: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  evidence: Record<string, any>;
  recommended_action: string;
  resolution_notes?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
  publisher_name?: string | null;
  canonical_domain?: string | null;
}

export interface PublisherQualityScore {
  id: string;
  publisher_id: string;
  overall_quality_score: number;
  completeness_score: number;
  validity_score: number;
  freshness_score: number;
  consistency_score: number;
  verdict: string;
  is_verified: boolean;
  is_stale: boolean;
  has_duplicates: boolean;
  has_conflicts: boolean;
  price_freshness_status: string;
  metrics_freshness_status: string;
  findings_count: number;
  critical_findings_count: number;
  high_findings_count: number;
  last_audited_at: string;
}

export interface QualitySeverityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface QualityIssueBreakdown {
  missing_field: number;
  stale_data: number;
  invalid_data: number;
  duplicate_record: number;
  conflicting_data: number;
  unsupported_currency: number;
}

export interface PublisherQualitySummary {
  total_publishers: number;
  audited_publishers: number;
  average_quality_score: number;
  publishers_with_critical_issues: number;
  publishers_with_stale_data: number;
  publishers_with_duplicates: number;
  publishers_with_conflicts: number;
  total_open_findings: number;
  severity_breakdown: QualitySeverityBreakdown;
  issue_type_breakdown: QualityIssueBreakdown;
  last_audit_run_at?: string | null;
}

export interface PublisherObservationTimelineItem {
  id: string;
  publisher_id: string;
  observation_timestamp: string;
  price?: number | null;
  currency?: string | null;
  pricing_model?: string | null;
  metric_da?: number | null;
  metric_dr?: number | null;
  metric_traffic?: number | null;
  source_name?: string | null;
  verification_status: string;
}

export interface PublisherRefreshLog {
  id: string;
  publisher_id: string;
  provider: string;
  field_refreshed: string;
  status: string;
  previous_value?: string | null;
  new_value?: string | null;
  evidence?: Record<string, any> | null;
  attempted_at: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  retry_count: number;
  error_message?: string | null;
}

export interface PublisherDetailedQuality {
  publisher_id: string;
  company_id: string;
  company_name: string;
  canonical_domain?: string | null;
  original_submitted_url?: string | null;
  publisher_name?: string | null;
  audience_focus?: string | null;
  status: string;
  quality_score?: PublisherQualityScore | null;
  findings: PublisherQualityFinding[];
  freshness_status: Record<string, any>;
  latest_observation?: PublisherObservationTimelineItem | null;
  historical_observations: PublisherObservationTimelineItem[];
  refresh_logs: PublisherRefreshLog[];
}

// ==========================================
// Phase 3.2: Revenue & Performance Analytics
// ==========================================

export interface RevenueSummary {
  reporting_currency: string;
  exchange_rates_used: Record<string, number>;
  rates_as_of: string;
  total_realized_revenue: number;
  net_realized_revenue: number;
  total_discounts: number;
  total_taxes: number;
  total_refunds: number;
  total_open_pipeline_value: number;
  weighted_pipeline_value: number;
  total_recorded_costs?: number | null;
  cost_coverage_pct: number;
  gross_profit?: number | null;
  gross_margin_pct?: number | null;
  total_invoiced_amount?: number | null;
  total_paid_amount?: number | null;
  total_outstanding_amount?: number | null;
  deal_count_total: number;
  deal_count_won: number;
  deal_count_lost: number;
  deal_count_open: number;
  win_rate_pct: number;
  average_deal_size_won?: number | null;
  average_sales_cycle_days?: number | null;
  currency_breakdown_realized: Record<string, number>;
  currency_breakdown_pipeline: Record<string, number>;
  data_limitations: string[];
}

export interface ServiceRevenueBreakdown {
  service_category: string;
  realized_revenue: number;
  deals_won: number;
  average_deal_size?: number | null;
  open_pipeline_value: number;
  open_deal_count: number;
  recorded_costs?: number | null;
  gross_profit?: number | null;
  gross_margin_pct?: number | null;
}

export interface ClientRevenueBreakdown {
  company_id: string;
  company_name: string;
  domain?: string | null;
  sales_stage: string;
  realized_revenue: number;
  deals_won: number;
  open_pipeline_value: number;
  open_deal_count: number;
  last_deal_date?: string | null;
}

export interface CampaignROIBreakdown {
  campaign_id?: string | null;
  campaign_name: string;
  deals_won: number;
  deal_count_total: number;
  realized_revenue: number;
  recorded_costs?: number | null;
  net_profit?: number | null;
  roi_pct?: number | null;
  attribution_model: string;
  sample_size: number;
  has_sufficient_sample: boolean;
  caveats: string[];
}

export interface SalesFunnelStage {
  stage: string;
  order: number;
  deal_count: number;
  total_value: number;
  probability_weight: number;
  weighted_value: number;
  conversion_rate_to_next?: number | null;
  dropoff_rate?: number | null;
  avg_days_in_stage?: number | null;
}

export interface FunnelAnalysis {
  stages: SalesFunnelStage[];
  overall_conversion_rate: number;
  bottleneck_stage?: string | null;
  bottleneck_reason?: string | null;
  total_deals_analyzed: number;
}

export interface RevenueTrendItem {
  period: string;
  realized_revenue: number;
  deals_won: number;
  pipeline_created_value: number;
  deals_created: number;
}

export interface RevenueDrilldownItem {
  id: string;
  deal_name: string;
  company_id: string;
  company_name: string;
  service_category: string;
  stage: string;
  outcome?: string | null;
  currency: string;
  native_closed_amount?: number | null;
  normalized_closed_amount?: number | null;
  native_estimated_value: number;
  normalized_estimated_value: number;
  cost_amount?: number | null;
  gross_margin_pct?: number | null;
  invoice_status?: string | null;
  invoiced_amount?: number | null;
  paid_amount?: number | null;
  discount_amount?: number | null;
  tax_amount?: number | null;
  refunded_amount?: number | null;
  created_at: string;
  actual_close_date?: string | null;
  sales_cycle_days?: number | null;
  campaign_id?: string | null;
  campaign_name?: string | null;
}

export interface RevenueDrilldownResponse {
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  drilldown_records: RevenueDrilldownItem[];
  calculation_notes: string[];
}

export interface SnapshotResponse {
  id: string;
  period_start?: string | null;
  period_end?: string | null;
  period_type: string;
  reporting_currency: string;
  total_realized_revenue: number;
  total_open_pipeline_value: number;
  weighted_pipeline_value: number;
  total_recorded_costs?: number | null;
  gross_profit?: number | null;
  gross_margin_pct?: number | null;
  deal_count_won: number;
  deal_count_lost: number;
  deal_count_open: number;
  average_deal_size_won?: number | null;
  average_sales_cycle_days?: number | null;
  revenue_by_service?: Record<string, any> | null;
  revenue_by_client?: Array<Record<string, any>> | null;
  revenue_by_campaign?: Array<Record<string, any>> | null;
  funnel_metrics?: Record<string, any> | null;
  currency_breakdown?: Record<string, any> | null;
  data_limitations?: string[] | null;
  created_at: string;
  created_by: string;
}

export async function getRevenueSummary(params?: Record<string, string>): Promise<RevenueSummary> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<RevenueSummary>(`/analytics/revenue${query}`);
}

export async function getServiceRevenue(params?: Record<string, string>): Promise<ServiceRevenueBreakdown[]> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<ServiceRevenueBreakdown[]>(`/analytics/services${query}`);
}

export async function getClientRevenue(params?: Record<string, string>): Promise<ClientRevenueBreakdown[]> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<ClientRevenueBreakdown[]>(`/analytics/clients${query}`);
}

export async function getCampaignROI(params?: Record<string, string>): Promise<CampaignROIBreakdown[]> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<CampaignROIBreakdown[]>(`/analytics/campaigns${query}`);
}

export async function getFunnelAnalysis(params?: Record<string, string>): Promise<FunnelAnalysis> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<FunnelAnalysis>(`/analytics/funnel${query}`);
}

export async function getRevenueTrends(params?: Record<string, string>): Promise<RevenueTrendItem[]> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<RevenueTrendItem[]>(`/analytics/trends${query}`);
}

export async function getRevenueDealsDrilldown(params?: Record<string, string>): Promise<RevenueDrilldownResponse> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetcher<RevenueDrilldownResponse>(`/analytics/drilldown/deals${query}`);
}

export async function createAnalyticsSnapshot(data: { period_type: string; period_start?: string; period_end?: string; created_by?: string }): Promise<SnapshotResponse> {
  return fetcher<SnapshotResponse>('/analytics/snapshots', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAnalyticsSnapshots(limit: number = 20): Promise<SnapshotResponse[]> {
  return fetcher<SnapshotResponse[]>(`/analytics/snapshots?limit=${limit}`);
}

// ==========================================
// Phase 3.3: Competitive SEO Intelligence
// ==========================================

export interface CompetitorCandidate {
  company_id?: string | null;
  company_name: string;
  canonical_domain: string;
  industry?: string | null;
  relevance_score: number;
  relevance_tier: 'DIRECT' | 'INDIRECT' | 'TOPICAL_PEER' | 'IRRELEVANT';
  overlap_evidence: Record<string, any>;
  discovery_method: string;
}

export interface CompetitorResponse {
  id: string;
  company_id: string;
  competitor_company_id?: string | null;
  competitor_name: string;
  competitor_domain: string;
  relevance_score: number;
  relevance_tier: string;
  validation_status: string;
  validation_evidence?: Record<string, any> | null;
  discovery_method: string;
  is_active: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentGapItem {
  topic: string;
  search_intent: 'INFORMATIONAL' | 'COMMERCIAL' | 'TRANSACTIONAL' | 'NAVIGATIONAL';
  competitor_coverage: string;
  prospect_coverage: string;
  opportunity_level: string;
  recommended_service: string;
  recommended_action: string;
  confidence: number;
}

export interface TechnicalGapItem {
  metric_or_feature: string;
  prospect_state: string;
  competitor_state: string;
  gap_description: string;
  severity: string;
  recommended_service: string;
  recommended_action: string;
  confidence: number;
}

export interface InternalLinkingGapItem {
  silo_topic: string;
  prospect_issue: string;
  competitor_advantage: string;
  recommended_service: string;
  recommended_action: string;
  severity: string;
  confidence: number;
}

export interface BacklinkGapSummary {
  prospect_domain: string;
  competitor_domain: string;
  prospect_da?: number | null;
  competitor_da?: number | null;
  da_differential?: number | null;
  prospect_dr?: number | null;
  competitor_dr?: number | null;
  dr_differential?: number | null;
  prospect_ref_domains?: number | null;
  competitor_ref_domains?: number | null;
  provider_source: string;
  is_provider_configured: boolean;
  limitations: string[];
}

export interface PublisherPROpportunityItem {
  publisher_id: string;
  publisher_name: string;
  canonical_domain: string;
  audience_focus: string;
  da?: number | null;
  dr?: number | null;
  price?: number | null;
  currency?: string | null;
  relevance_rationale: string;
  recommended_service: string;
}

export interface CompetitiveRecommendation {
  id: string;
  title: string;
  category: string;
  service: string;
  severity: string;
  rationale: string;
  action: string;
  supporting_evidence: Record<string, any>;
  confidence: number;
  effort: string;
  impact: string;
  priority_score: number;
}

export interface CompetitiveAnalysisRunResponse {
  id: string;
  company_id: string;
  company_name: string;
  competitor_id: string;
  competitor_name: string;
  competitor_domain: string;
  status: string;
  prospect_scan_available: boolean;
  competitor_scan_available: boolean;
  summary_findings: Record<string, any>;
  content_gaps: ContentGapItem[];
  technical_gaps: TechnicalGapItem[];
  internal_linking_gaps: InternalLinkingGapItem[];
  backlink_gaps: BacklinkGapSummary;
  publisher_opportunities: PublisherPROpportunityItem[];
  prioritized_recommendations: CompetitiveRecommendation[];
  data_limitations: string[];
  analyzed_at: string;
  created_at: string;
}

export interface CompetitiveOverviewResponse {
  company_id: string;
  company_name: string;
  canonical_domain?: string | null;
  competitors_count: number;
  analyzed_runs_count: number;
  top_competitors: CompetitorResponse[];
  latest_run?: CompetitiveAnalysisRunResponse | null;
  total_content_gaps: number;
  total_technical_gaps: number;
  total_publisher_opportunities: number;
  data_limitations: string[];
}

export async function discoverCompetitors(companyId: string, maxResults: number = 5, persist: boolean = false): Promise<CompetitorCandidate[]> {
  return fetcher<CompetitorCandidate[]>(`/competitive/companies/${companyId}/discover?max_results=${maxResults}&persist=${persist}`, {
    method: 'POST'
  });
}

export async function getCompanyCompetitors(companyId: string): Promise<CompetitorResponse[]> {
  return fetcher<CompetitorResponse[]>(`/competitive/companies/${companyId}/competitors`);
}

export async function addCompanyCompetitor(companyId: string, data: {
  competitor_name: string;
  competitor_domain: string;
  competitor_company_id?: string;
  relevance_tier?: string;
  relevance_score?: number;
  discovery_method?: string;
  notes?: string;
}): Promise<CompetitorResponse> {
  return fetcher<CompetitorResponse>(`/competitive/companies/${companyId}/competitors`, {
    method: 'POST',
    body: JSON.stringify({ company_id: companyId, ...data })
  });
}

export async function updateCompanyCompetitor(competitorId: string, data: {
  competitor_name?: string;
  relevance_score?: number;
  relevance_tier?: string;
  validation_status?: string;
  notes?: string;
  is_active?: boolean;
}): Promise<CompetitorResponse> {
  return fetcher<CompetitorResponse>(`/competitive/competitors/${competitorId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function runCompetitiveAnalysis(companyId: string, data: {
  competitor_id?: string;
  competitor_domain?: string;
  sync_to_sales_opportunities?: boolean;
}): Promise<CompetitiveAnalysisRunResponse> {
  return fetcher<CompetitiveAnalysisRunResponse>(`/competitive/companies/${companyId}/analyze`, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function getCompanyCompetitiveRuns(companyId: string, limit: number = 15): Promise<CompetitiveAnalysisRunResponse[]> {
  return fetcher<CompetitiveAnalysisRunResponse[]>(`/competitive/companies/${companyId}/runs?limit=${limit}`);
}

export async function getCompetitiveRun(runId: string): Promise<CompetitiveAnalysisRunResponse> {
  return fetcher<CompetitiveAnalysisRunResponse>(`/competitive/runs/${runId}`);
}

export async function getCompanyCompetitiveOverview(companyId: string): Promise<CompetitiveOverviewResponse> {
  return fetcher<CompetitiveOverviewResponse>(`/competitive/companies/${companyId}/overview`);
}

// =========================================================================
// Phase 3.4: Automated Reporting & Client Portals
// =========================================================================

export interface PortalUser {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'AGENCY_STAFF' | 'CLIENT_USER';
  company_id?: string | null;
  company_name?: string | null;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
}

export interface ClientReport {
  id: string;
  company_id: string;
  company_name: string;
  title: string;
  report_type: string;
  reporting_period_start?: string | null;
  reporting_period_end?: string | null;
  status: 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED' | 'DELIVERED' | 'ARCHIVED';
  approval_status: 'UNAPPROVED' | 'APPROVED' | 'REJECTED';
  approved_by_user_id?: string | null;
  approved_at?: string | null;
  branding?: {
    agency_name?: string;
    client_name?: string;
    primary_color?: string;
    logo_url?: string | null;
    footer_text?: string;
  };
  sections: Array<{
    section_id: string;
    title: string;
    section_type: string;
    content: Record<string, unknown>;
  }>;
  summary_metrics?: Record<string, unknown>;
  delivery_status: 'NOT_DELIVERED' | 'SCHEDULED' | 'SENT' | 'FAILED' | 'DELIVERED';
  generated_by: string;
  data_limitations: string[];
  export_formats?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ReportSchedule {
  id: string;
  company_id: string;
  company_name?: string | null;
  report_type: string;
  frequency: 'WEEKLY' | 'MONTHLY' | 'QUARTERLY';
  day_of_month: number;
  day_of_week: number;
  time_of_day: string;
  time_zone: string;
  recipients: string[];
  is_active: boolean;
  requires_approval: boolean;
  last_generated_at?: string | null;
  next_run_at?: string | null;
  created_at: string;
}

export interface DeliveryLog {
  id: string;
  report_id: string;
  recipient_email: string;
  delivery_channel: string;
  idempotency_key: string;
  status: string;
  sent_at?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface PortalWorkspace {
  company_id: string;
  company_name: string;
  canonical_domain?: string | null;
  industry?: string | null;
  client_user: PortalUser;
  latest_approved_report?: ClientReport | null;
  available_reports_count: number;
  active_campaigns_count: number;
  approved_media_plans_count: number;
  verified_seo_health: {
    crawl_status?: string;
    http_status?: number;
    https_secure?: boolean;
    title_tag?: string;
    last_scanned_at?: string;
  };
  client_visible_opportunities: Array<{
    category: string;
    summary: string;
    deliverable: string;
  }>;
  branding: {
    client_name: string;
    brand_domain?: string;
    primary_color: string;
    agency_name: string;
  };
  data_freshness: {
    data_source: string;
    last_updated: string;
    policy: string;
  };
}

export interface PortalAuditLog {
  id: string;
  user_id?: string | null;
  user_email?: string | null;
  company_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, unknown>;
  ip_address?: string | null;
  timestamp: string;
}

export async function portalLogin(data: { email: string; password: string }): Promise<{ access_token: string; user: PortalUser }> {
  return fetcher<{ access_token: string; token_type: string; user: PortalUser }>('/portal/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function portalRegister(data: {
  email: string;
  password: string;
  full_name: string;
  company_id?: string;
  role?: string;
}): Promise<PortalUser> {
  return fetcher<PortalUser>('/portal/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function portalGetMe(token?: string): Promise<PortalUser> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<PortalUser>('/portal/auth/me', { headers });
}

export async function getClientReports(params?: {
  company_id?: string;
  status_filter?: string;
  approval_filter?: string;
}, token?: string): Promise<ClientReport[]> {
  const query = new URLSearchParams();
  if (params?.company_id) query.set('company_id', params.company_id);
  if (params?.status_filter) query.set('status_filter', params.status_filter);
  if (params?.approval_filter) query.set('approval_filter', params.approval_filter);
  
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  return fetcher<ClientReport[]>(`/portal/reports?${query.toString()}`, { headers });
}

export async function getClientReport(reportId: string, token?: string): Promise<ClientReport> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ClientReport>(`/portal/reports/${reportId}`, { headers });
}

export async function generateClientReport(data: {
  company_id: string;
  title: string;
  report_type?: string;
  reporting_period_start?: string;
  reporting_period_end?: string;
  branding?: Record<string, unknown>;
  custom_notes?: string;
}, token?: string): Promise<ClientReport> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ClientReport>('/portal/reports', {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

export async function approveClientReport(
  reportId: string,
  data: { approval_status: string; notes?: string },
  token?: string
): Promise<ClientReport> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ClientReport>(`/portal/reports/${reportId}/approve`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

export async function deliverClientReport(
  reportId: string,
  data: { recipients?: string[]; delivery_channel?: string; simulate?: boolean },
  token?: string
): Promise<DeliveryLog[]> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<DeliveryLog[]>(`/portal/reports/${reportId}/deliver`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

export async function exportClientReport(reportId: string, format: 'markdown' | 'html', token?: string): Promise<string> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const response = await fetch(`${API_BASE_URL}/portal/reports/${reportId}/export?format=${format}`, {
    headers,
  });
  return response.text();
}

export async function getReportSchedules(companyId?: string, token?: string): Promise<ReportSchedule[]> {
  const query = companyId ? `?company_id=${companyId}` : '';
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ReportSchedule[]>(`/portal/schedules${query}`, { headers });
}

export async function createReportSchedule(data: {
  company_id: string;
  report_type?: string;
  frequency?: string;
  time_of_day?: string;
  time_zone?: string;
  recipients?: string[];
  requires_approval?: boolean;
}, token?: string): Promise<ReportSchedule> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ReportSchedule>('/portal/schedules', {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

export async function triggerReportSchedules(token?: string): Promise<ClientReport[]> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<ClientReport[]>('/portal/schedules/trigger', {
    method: 'POST',
    headers,
  });
}

export async function getClientWorkspace(companyId: string, token?: string): Promise<PortalWorkspace> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<PortalWorkspace>(`/portal/workspace/${companyId}`, { headers });
}

export async function getPortalAuditLogs(params?: {
  company_id?: string;
  action?: string;
  limit?: number;
}, token?: string): Promise<PortalAuditLog[]> {
  const query = new URLSearchParams();
  if (params?.company_id) query.set('company_id', params.company_id);
  if (params?.action) query.set('action', params.action);
  if (params?.limit) query.set('limit', String(params.limit));

  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<PortalAuditLog[]>(`/portal/audit-logs?${query.toString()}`, { headers });
}

export async function createClientInvitation(data: {
  company_id: string;
  email: string;
  role?: string;
}, token?: string): Promise<{ id: string; email: string; invitation_token: string; status: string }> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetcher<{ id: string; email: string; invitation_token: string; status: string }>('/portal/invitations', {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

