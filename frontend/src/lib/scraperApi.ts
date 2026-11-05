import { getApiBaseUrl } from './api';

export interface ScraperTask {
  id: string;
  name: string;
  description?: string;
  task_type: string;
  template_id?: string;
  target_url?: string;
  workflow_config: Record<string, any>;
  execution_mode: string;
  status: string;
  schedule_type: string;
  schedule_cron?: string;
  schedule_timezone: string;
  is_schedule_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  total_records: number;
  successful_records: number;
  failed_records: number;
  duplicate_records: number;
  last_error?: string;
  created_at: string;
  updated_at?: string;
  recent_runs?: ScraperRun[];
}

export interface ScraperRun {
  id: string;
  task_id: string;
  run_number: number;
  execution_mode: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds: number;
  records_extracted: number;
  records_saved: number;
  records_duplicate: number;
  error_message?: string;
  logs?: Array<{ timestamp: string; level: string; message: string }>;
  created_at: string;
}

export interface ExtractedRecord {
  id: string;
  task_id?: string;
  record_hash?: string;
  company_name?: string;
  website?: string;
  domain?: string;
  industry?: string;
  category?: string;
  country?: string;
  city?: string;
  email?: string;
  phone?: string;
  address?: string;
  description?: string;
  social_profiles?: Record<string, string>;
  source_url?: string;
  discovery_source: string;
  validation_status: string;
  quality_score: number;
  quality_status: string;
  is_duplicate: boolean;
  created_at: string;
  raw_data?: Record<string, any>;
  cleaned_data?: Record<string, any>;
  validation_details?: Record<string, any>;
}

export interface ScraperTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  data_source: string;
  required_credentials: string;
  limitations: string;
  input_parameters: Array<{
    key: string;
    label: string;
    type: string;
    default: any;
    required: boolean;
  }>;
  output_fields: string[];
  example_output: Record<string, any>;
  workflow_config: Record<string, any>;
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  if (!res.ok) {
    let errDetail = 'Request failed';
    try {
      const data = await res.json();
      errDetail = data.detail || data.message || JSON.stringify(data);
    } catch {
      errDetail = await res.text();
    }
    throw new Error(errDetail);
  }
  return res.json();
}

export const scraperApi = {
  // Overview
  async getOverview() {
    return apiRequest<{
      metrics: {
        total_tasks: number;
        active_schedules: number;
        total_records: number;
        valid_records: number;
        duplicate_records: number;
        total_runs: number;
        total_crm_leads?: number;
        completed_runs?: number;
        failed_runs?: number;
        success_rate_percent?: number;
        failure_rate_percent?: number;
      };
      daily_extractions?: Array<{ date: string; count: number; valid: number; duplicates: number }>;
      monthly_extractions?: Array<{ month: string; count: number }>;
      lead_sources?: Array<{ source: string; count: number; percentage: number }>;
      crm_funnel?: Array<{ stage: string; count: number; percentage: number }>;
      recent_tasks: any[];
      recent_runs: any[];
      recent_activities?: any[];
    }>('/api/scraper/overview');
  },

  // Tasks
  async getTasks(params: { status?: string; task_type?: string; search?: string; limit?: number; offset?: number } = {}) {
    const q = new URLSearchParams();
    if (params.status) q.set('status', params.status);
    if (params.task_type) q.set('task_type', params.task_type);
    if (params.search) q.set('search', params.search);
    if (params.limit) q.set('limit', String(params.limit));
    if (params.offset) q.set('offset', String(params.offset));
    return apiRequest<{ total: number; items: ScraperTask[] }>(`/api/scraper/tasks?${q.toString()}`);
  },

  async getTask(id: string) {
    return apiRequest<ScraperTask>(`/api/scraper/tasks/${id}`);
  },

  async createTask(data: any) {
    return apiRequest<{ message: string; task: { id: string; name: string } }>('/api/scraper/tasks', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateTask(id: string, data: any) {
    return apiRequest<{ message: string; task: { id: string; name: string } }>(`/api/scraper/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async deleteTask(id: string) {
    return apiRequest<{ message: string }>(`/api/scraper/tasks/${id}`, {
      method: 'DELETE'
    });
  },

  async duplicateTask(id: string) {
    return apiRequest<{ message: string; task: { id: string; name: string } }>(`/api/scraper/tasks/${id}/duplicate`, {
      method: 'POST'
    });
  },

  async pauseTask(id: string) {
    return apiRequest<{ message: string }>(`/api/scraper/tasks/${id}/pause`, {
      method: 'POST'
    });
  },

  async resumeTask(id: string) {
    return apiRequest<{ message: string }>(`/api/scraper/tasks/${id}/resume`, {
      method: 'POST'
    });
  },

  async runTask(id: string, mode?: 'CLOUD' | 'LOCAL') {
    const q = mode ? `?mode=${mode}` : '';
    return apiRequest<{
      message: string;
      run_id: string;
      status: string;
      records_extracted?: number;
      records_saved?: number;
      records_duplicate?: number;
      duration_seconds?: number;
      runner_command?: string;
    }>(`/api/scraper/tasks/${id}/run${q}`, {
      method: 'POST'
    });
  },

  async getRun(id: string) {
    return apiRequest<ScraperRun>(`/api/scraper/runs/${id}`);
  },

  async cancelRun(id: string) {
    return apiRequest<{ message: string }>(`/api/scraper/runs/${id}/cancel`, {
      method: 'POST'
    });
  },

  // Auto Detect & Inspector
  async autoDetect(url: string, htmlOverride?: string) {
    return apiRequest<{
      success: boolean;
      target_url: string;
      page_title?: string;
      meta_description?: string;
      detected_container: string;
      elements_found: number;
      detected_fields: any[];
      pagination: any;
      sample_records: any[];
      workflow_config: any;
    }>('/api/scraper/auto-detect', {
      method: 'POST',
      body: JSON.stringify({ url, html_override: htmlOverride })
    });
  },

  async previewDom(url: string) {
    return apiRequest<{
      url: string;
      title: string;
      sanitized_html: string;
    }>('/api/scraper/preview-dom', {
      method: 'POST',
      body: JSON.stringify({ url })
    });
  },

  async testSelector(url: string, selector: string, attribute: string = 'text') {
    return apiRequest<{
      selector: string;
      matches_count: number;
      sample_values: string[];
    }>('/api/scraper/test-selector', {
      method: 'POST',
      body: JSON.stringify({ url, selector, attribute })
    });
  },

  async aiGenerate(url: string, prompt: string) {
    return apiRequest<{
      success: boolean;
      target_url: string;
      interpreted_goal: string;
      workflow_config: any;
      sample_records: any[];
    }>('/api/scraper/ai-generate', {
      method: 'POST',
      body: JSON.stringify({ url, prompt })
    });
  },

  // Templates
  async getTemplates() {
    return apiRequest<{ templates: ScraperTemplate[] }>('/api/scraper/templates');
  },

  async getTemplate(id: string) {
    return apiRequest<ScraperTemplate>(`/api/scraper/templates/${id}`);
  },

  async instantiateTemplate(id: string, customName?: string, targetUrl?: string) {
    const q = new URLSearchParams();
    if (customName) q.set('custom_name', customName);
    if (targetUrl) q.set('target_url', targetUrl);
    return apiRequest<{ message: string; task_id: string; name: string }>(
      `/api/scraper/templates/${id}/instantiate?${q.toString()}`,
      { method: 'POST' }
    );
  },

  // Data Center
  async getData(params: {
    task_id?: string;
    search?: string;
    validation_status?: string;
    quality_status?: string;
    country?: string;
    is_duplicate?: boolean;
    sort_by?: string;
    sort_order?: string;
    limit?: number;
    offset?: number;
  } = {}) {
    const q = new URLSearchParams();
    if (params.task_id) q.set('task_id', params.task_id);
    if (params.search) q.set('search', params.search);
    if (params.validation_status) q.set('validation_status', params.validation_status);
    if (params.quality_status) q.set('quality_status', params.quality_status);
    if (params.country) q.set('country', params.country);
    if (params.is_duplicate !== undefined) q.set('is_duplicate', String(params.is_duplicate));
    if (params.sort_by) q.set('sort_by', params.sort_by);
    if (params.sort_order) q.set('sort_order', params.sort_order);
    if (params.limit) q.set('limit', String(params.limit));
    if (params.offset) q.set('offset', String(params.offset));
    return apiRequest<{ total: number; items: ExtractedRecord[] }>(`/api/scraper/data?${q.toString()}`);
  },

  async getRecord(id: string) {
    return apiRequest<ExtractedRecord>(`/api/scraper/data/${id}`);
  },

  async cleanData(taskId?: string) {
    const q = taskId ? `?task_id=${taskId}` : '';
    return apiRequest<{ message: string }>(`/api/scraper/data/clean${q}`, { method: 'POST' });
  },

  async deduplicateData(taskId?: string) {
    const q = taskId ? `?task_id=${taskId}` : '';
    return apiRequest<{ message: string }>(`/api/scraper/data/deduplicate${q}`, { method: 'POST' });
  },

  // Export Center
  async createExport(data: { task_id?: string; format: string; filter_criteria?: any }) {
    return apiRequest<{
      message: string;
      export_id: string;
      format: string;
      record_count: number;
      file_size_bytes: number;
      download_url: string;
    }>('/api/scraper/export', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async getExportHistory() {
    return apiRequest<{ items: any[] }>('/api/scraper/export/history');
  },

  async testDatabase(data: any) {
    return apiRequest<{ status: string; database: string; target_table: string; message: string }>(
      '/api/scraper/export/db-test',
      { method: 'POST', body: JSON.stringify(data) }
    );
  },

  // API Keys
  async getApiKeys() {
    return apiRequest<{ items: any[] }>('/api/scraper/api-keys');
  },

  async createApiKey(data: { name: string; rate_limit_rpm: number }) {
    return apiRequest<{
      message: string;
      api_key: string;
      id: string;
      name: string;
      prefix: string;
      rate_limit_rpm: number;
    }>('/api/scraper/api-keys', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async revokeApiKey(id: string) {
    return apiRequest<{ message: string }>(`/api/scraper/api-keys/${id}`, { method: 'DELETE' });
  }
};
