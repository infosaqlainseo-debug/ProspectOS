import { getApiBaseUrl } from './api';

export interface CRMLead {
  id: string;
  company_name: string;
  canonical_domain?: string;
  website_url?: string;
  industry?: string;
  sub_industry?: string;
  country?: string;
  city?: string;
  state?: string;
  description?: string;
  company_size?: string;
  sales_stage: string;
  lead_priority: string;
  lead_score?: number;
  lead_score_components?: {
    contact_reachability?: { score: number; max: number; signals: any };
    profile_completeness?: { score: number; max: number; signals: any };
    website_viability?: { score: number; max: number; signals: any };
    seo_opportunity?: { score: number; max: number; signals: any };
  };
  lead_source: string;
  tags: string[];
  custom_fields?: Record<string, any>;
  contact_person?: string;
  contact_title?: string;
  public_email?: string;
  phone_number?: string;
  linkedin_url?: string;
  facebook_url?: string;
  instagram_url?: string;
  whatsapp_number?: string;
  domain_rating?: number;
  organic_traffic?: number;
  website_status?: string;
  lead_owner?: string;
  stage_updated_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface CRMAIResearch {
  id: string;
  company_id: string;
  executive_summary?: string;
  target_market?: string;
  value_proposition?: string;
  seo_weaknesses: Array<{ issue: string; severity: string; details: string }>;
  backlink_opportunities: Array<{ category: string; relevance: string; rationale: string }>;
  recommended_services: string[];
  growth_opportunities: string[];
  tech_stack_detected: string[];
  confidence_score: number;
  model_used: string;
  analyzed_at: string;
}

export interface CRMLeadDetail {
  company: CRMLead;
  ai_research?: CRMAIResearch;
  notes: Array<{ id: string; author: string; content: string; created_at: string }>;
  activities: Array<{ id: string; activity_type: string; actor: string; title: string; details: any; created_at: string }>;
  tasks: Array<{ id: string; title: string; description?: string; task_type: string; priority: string; status: string; due_date?: string; created_at: string }>;
  deals: Array<{ id: string; deal_name: string; service_category: string; stage: string; estimated_value: number; created_at: string }>;
}

export interface CRMLeadSegment {
  id: string;
  name: string;
  description?: string;
  is_dynamic: boolean;
  filter_criteria: Record<string, any>;
  color: string;
  icon?: string;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineColumn {
  stage: string;
  stage_name: string;
  prospects_count: number;
  open_deals_count: number;
  total_pipeline_value: number;
  prospects: Array<{
    id: string;
    company_name: string;
    canonical_domain?: string;
    website_url?: string;
    industry?: string;
    sales_stage: string;
    lead_priority: string;
    lead_score?: number;
    public_email?: string;
    phone_number?: string;
    country?: string;
    city?: string;
    stage_updated_at?: string;
  }>;
}

export interface AIAssistantResponse {
  answer: string;
  suggested_actions: Array<{ action: string; label: string; href?: string; criteria?: any }>;
  matched_leads: Array<{
    id: string;
    company_name: string;
    canonical_domain?: string;
    industry?: string;
    country?: string;
    sales_stage: string;
    lead_score?: number;
    lead_priority: string;
    public_email?: string;
    phone_number?: string;
  }>;
  sql_or_filter_used?: string;
  confidence: number;
}

export interface CRMAnalyticsData {
  total_leads: number;
  stage_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  top_countries: Array<{ country: string; count: number }>;
  top_industries: Array<{ industry: string; count: number }>;
  score_distribution: Record<string, number>;
  data_completeness: {
    with_email: number;
    with_phone: number;
    with_website: number;
    email_coverage_percent: number;
    phone_coverage_percent: number;
  };
}

export interface ScraperImportResponse {
  success: boolean;
  total_processed: number;
  added: number;
  updated: number;
  skipped: number;
  flagged: number;
  imported_ids: string[];
  message: string;
}

const getBase = () => getApiBaseUrl();

export const crmApi = {
  // Scraper Bridge
  async importFromScraper(params: {
    extracted_record_ids?: string[];
    task_id?: string;
    auto_save_valid_only?: boolean;
    default_stage?: string;
    tags?: string[];
    conflict_resolution?: string;
  }): Promise<ScraperImportResponse> {
    const res = await fetch(`${getBase()}/crm/import-from-scraper`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to import to CRM' }));
      throw new Error(err.detail || 'Import failed');
    }
    return res.json();
  },

  // Leads
  async listLeads(params?: {
    q?: string;
    stage?: string;
    industry?: string;
    country?: string;
    priority?: string;
    min_score?: number;
    max_score?: number;
    tag?: string;
    lead_source?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_dir?: string;
  }): Promise<{ total: number; page: number; page_size: number; items: CRMLead[] }> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          query.append(k, String(v));
        }
      });
    }
    const res = await fetch(`${getBase()}/crm/leads?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch leads');
    return res.json();
  },

  async getLead(id: string): Promise<CRMLeadDetail> {
    const res = await fetch(`${getBase()}/crm/leads/${id}`);
    if (!res.ok) throw new Error('Failed to fetch lead details');
    return res.json();
  },

  async createLead(data: Partial<CRMLead>): Promise<{ success: boolean; lead_id: string; company_name: string }> {
    const res = await fetch(`${getBase()}/crm/leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create lead' }));
      throw new Error(err.detail || 'Create lead failed');
    }
    return res.json();
  },

  async updateLead(id: string, data: Partial<CRMLead>): Promise<any> {
    const res = await fetch(`${getBase()}/crm/leads/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update lead');
    return res.json();
  },

  async deleteLead(id: string): Promise<any> {
    const res = await fetch(`${getBase()}/crm/leads/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete lead');
    return res.json();
  },

  async bulkUpdateLeads(data: {
    lead_ids: string[];
    sales_stage?: string;
    lead_priority?: string;
    add_tags?: string[];
    remove_tags?: string[];
    lead_owner?: string;
  }): Promise<any> {
    const res = await fetch(`${getBase()}/crm/leads/bulk-update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Bulk update failed');
    return res.json();
  },

  async bulkDeleteLeads(leadIds: string[]): Promise<any> {
    const res = await fetch(`${getBase()}/crm/leads/bulk-delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_ids: leadIds }),
    });
    if (!res.ok) throw new Error('Bulk delete failed');
    return res.json();
  },

  async updateLeadStage(id: string, stage: string, reason?: string, notes?: string): Promise<any> {
    const res = await fetch(`${getBase()}/crm/leads/${id}/stage`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_stage: stage, reason, notes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Stage update failed' }));
      throw new Error(err.detail || 'Stage update failed');
    }
    return res.json();
  },

  // Deep AI Research
  async analyzeLeadWithAI(id: string): Promise<CRMAIResearch> {
    const res = await fetch(`${getBase()}/crm/leads/${id}/analyze-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('AI analysis failed');
    return res.json();
  },

  // Segments & Lists
  async listSegments(): Promise<CRMLeadSegment[]> {
    const res = await fetch(`${getBase()}/crm/segments`);
    if (!res.ok) throw new Error('Failed to fetch segments');
    return res.json();
  },

  async createSegment(data: Partial<CRMLeadSegment>): Promise<CRMLeadSegment> {
    const res = await fetch(`${getBase()}/crm/segments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create segment');
    return res.json();
  },

  async deleteSegment(id: string): Promise<any> {
    const res = await fetch(`${getBase()}/crm/segments/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete segment');
    return res.json();
  },

  async getSegmentLeads(id: string, page = 1, pageSize = 25): Promise<any> {
    const res = await fetch(`${getBase()}/crm/segments/${id}/leads?page=${page}&page_size=${pageSize}`);
    if (!res.ok) throw new Error('Failed to fetch segment leads');
    return res.json();
  },

  // Pipeline Board
  async getPipelineBoard(): Promise<PipelineColumn[]> {
    const res = await fetch(`${getBase()}/crm/pipeline/board`);
    if (!res.ok) throw new Error('Failed to fetch pipeline board');
    return res.json();
  },

  // AI Intelligence Assistant
  async queryAssistant(query: string, contextFilters?: any): Promise<AIAssistantResponse> {
    const res = await fetch(`${getBase()}/crm/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, context_filters: contextFilters }),
    });
    if (!res.ok) throw new Error('Assistant query failed');
    return res.json();
  },

  // Adaptive Learning Insights
  async getLearningInsights(): Promise<any> {
    const res = await fetch(`${getBase()}/crm/learning/insights`);
    if (!res.ok) throw new Error('Failed to fetch learning insights');
    return res.json();
  },

  async resetLearning(): Promise<any> {
    const res = await fetch(`${getBase()}/crm/learning/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset learning weights');
    return res.json();
  },

  // Analytics Dashboard
  async getCRMAnalytics(): Promise<CRMAnalyticsData> {
    const res = await fetch(`${getBase()}/crm/analytics/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch CRM analytics');
    return res.json();
  },

  // Import / Export
  async importBatchLeads(leads: any[]): Promise<any> {
    const res = await fetch(`${getBase()}/crm/import-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ leads }),
    });
    if (!res.ok) throw new Error('Failed to import batch');
    return res.json();
  },

  getExportUrl(format: 'csv' | 'json', filters?: Record<string, string>): string {
    const q = new URLSearchParams({ format, ...(filters || {}) });
    return `${getBase()}/crm/export-leads?${q.toString()}`;
  }
};

