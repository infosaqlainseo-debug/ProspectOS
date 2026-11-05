import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ==========================================
# Super Admin Overview & Telemetry Schemas
# ==========================================

class AdminOverviewStats(BaseModel):
    total_users: int = 0
    active_users: int = 0
    suspended_users: int = 0
    super_admins: int = 0
    total_organizations: int = 0
    total_scraping_tasks: int = 0
    total_extracted_records: int = 0
    total_crm_leads: int = 0
    running_background_jobs: int = 0
    failed_background_jobs: int = 0
    daily_active_users: int = 0
    monthly_active_users: int = 0


class AdminSystemHealth(BaseModel):
    api_status: str = "HEALTHY"
    frontend_status: str = "HEALTHY"
    database_status: str = "HEALTHY"
    database_tables_count: int = 0
    database_latency_ms: float = 0.0
    redis_status: str = "HEALTHY"
    redis_memory_used: str = "0M"
    redis_connected_clients: int = 0
    worker_status: str = "HEALTHY"
    worker_registered_functions: int = 25
    cron_schedulers_active: bool = True
    queue_depth: int = 0
    failed_job_count: int = 0
    storage_utilization_percent: float = 14.5
    last_successful_task: Optional[datetime] = None
    last_successful_scraping_task: Optional[datetime] = None
    last_health_check_timestamp: Optional[datetime] = None
    worker_heartbeat: str = "ONLINE"
    last_backup_timestamp: Optional[str] = None
    last_backup_filename: Optional[str] = None
    last_backup_size_mb: Optional[float] = None
    timestamp: datetime


class AdminOverviewResponse(BaseModel):
    stats: AdminOverviewStats
    health: AdminSystemHealth
    recent_activity: List[Dict[str, Any]] = []
    system_alerts: List[Dict[str, Any]] = []


# ==========================================
# User & RBAC Management Schemas
# ==========================================

class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str # SUPER_ADMIN, ADMIN, MANAGER, MEMBER, READ_ONLY
    is_active: bool
    company_name: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AdminUserCreateRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "MEMBER" # SUPER_ADMIN, ADMIN, MANAGER, MEMBER, READ_ONLY
    company_id: Optional[uuid.UUID] = None


class AdminUserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    company_id: Optional[uuid.UUID] = None


class AdminUserPasswordResetResponse(BaseModel):
    success: bool
    user_id: uuid.UUID
    email: str
    temporary_token: str
    message: str


# ==========================================
# Role Permissions Matrix Schemas
# ==========================================

class RolePermissionItem(BaseModel):
    id: uuid.UUID
    role_name: str
    display_name: str
    description: Optional[str] = None
    permissions: Dict[str, Any]
    is_system_role: bool
    updated_at: datetime


class RolePermissionUpdateRequest(BaseModel):
    permissions: Dict[str, Any]
    description: Optional[str] = None


# ==========================================
# Scraper Infrastructure Management Schemas
# ==========================================

class ScraperInfraStatus(BaseModel):
    worker_pool_status: str = "ACTIVE" # ACTIVE, PAUSED, DEGRADED
    active_workers_count: int = 1
    running_jobs: int = 0
    queued_jobs: int = 0
    completed_jobs_24h: int = 0
    failed_jobs_24h: int = 0
    concurrency_limit: int = 5
    default_timeout_seconds: int = 300
    queue_depth: int = 0
    average_duration_seconds: float = 4.2
    retry_policy_max_attempts: int = 3


class ScraperInfraActionRequest(BaseModel):
    action: str # PAUSE, RESUME, RETRY_FAILED, SET_CONCURRENCY
    concurrency_limit: Optional[int] = None
    job_id: Optional[str] = None


class ScraperInfraActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    current_status: ScraperInfraStatus


# ==========================================
# AI Control Center Schemas
# ==========================================

class AIProviderItem(BaseModel):
    id: uuid.UUID
    provider_name: str
    display_name: str
    is_enabled: bool
    is_default: bool
    default_model: str
    available_models: List[str]
    api_key_masked: Optional[str] = None
    rpm_limit: int
    tpm_limit: int
    tokens_used_today: int
    total_tokens_used: int
    estimated_cost_usd: float
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None
    feature_flags: Dict[str, bool]


class AIProviderUpdateRequest(BaseModel):
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    default_model: Optional[str] = None
    api_key: Optional[str] = None
    rpm_limit: Optional[int] = None
    tpm_limit: Optional[int] = None
    feature_flags: Optional[Dict[str, bool]] = None


class AITestConnectionResponse(BaseModel):
    provider_name: str
    status: str # SUCCESS, FAILED
    latency_ms: float
    model_tested: str
    response_snippet: Optional[str] = None
    error: Optional[str] = None


# ==========================================
# Integrations Management Schemas
# ==========================================

class IntegrationItem(BaseModel):
    id: str
    name: str
    category: str # DATA_SOURCE, CLOUD_STORAGE, SEARCH_API, CRM_WEBHOOK
    description: str
    status: str # CONNECTED, CONFIGURED, DISCONNECTED, PLANNED
    configured: bool
    credentials_masked: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None
    features: List[str]


class IntegrationTestResponse(BaseModel):
    integration_id: str
    success: bool
    message: str
    details: Dict[str, Any] = {}


# ==========================================
# SEO Control Center Schemas
# ==========================================

class SEOGlobalConfigSchema(BaseModel):
    site_name: str = "ProspectOS"
    default_meta_title: str
    default_meta_description: str
    default_canonical_domain: str
    default_og_image_url: Optional[str] = None
    robots_txt_content: Optional[str] = None
    sitemap_enabled: bool = True
    gsc_verification_code: Optional[str] = None
    ga4_measurement_id: Optional[str] = None
    bing_verification_code: Optional[str] = None


class SEOPublicPageItem(BaseModel):
    id: uuid.UUID
    path: str
    page_name: str
    meta_title: str
    meta_description: str
    canonical_url: str
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None
    twitter_card: str = "summary_large_image"
    robots_directives: str = "index,follow"
    schema_type: str = "SoftwareApplication"
    structured_data_json: Optional[Dict[str, Any]] = None
    sitemap_priority: float = 0.8
    change_frequency: str = "weekly"
    is_published: bool = True
    last_audited_at: Optional[datetime] = None
    audit_score: int = 100
    audit_issues: List[Dict[str, Any]] = []


class SEOPublicPageCreateOrUpdate(BaseModel):
    path: str
    page_name: str
    meta_title: str
    meta_description: str
    canonical_url: str
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None
    twitter_card: str = "summary_large_image"
    robots_directives: str = "index,follow"
    schema_type: str = "SoftwareApplication"
    structured_data_json: Optional[Dict[str, Any]] = None
    sitemap_priority: float = 0.8
    change_frequency: str = "weekly"
    is_published: bool = True


class SEOAuditReport(BaseModel):
    audited_at: datetime
    total_pages_checked: int
    overall_health_score: int # 0 - 100
    critical_issues_count: int
    warning_issues_count: int
    passed_checks_count: int
    pages: List[SEOPublicPageItem]
    recommendations: List[Dict[str, Any]]


# ==========================================
# Platform Settings & Audit Log Schemas
# ==========================================

class PlatformSettingCategory(BaseModel):
    category: str
    settings: Dict[str, Any]


class PlatformSettingsUpdateRequest(BaseModel):
    category: str
    settings: Dict[str, Any]


class AdminAuditLogItem(BaseModel):
    id: uuid.UUID
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

