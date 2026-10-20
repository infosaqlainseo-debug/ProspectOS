import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String, nullable=True)
    website_url: Mapped[str | None] = mapped_column(String, nullable=True)
    canonical_domain: Mapped[str | None] = mapped_column(String, nullable=True, index=True, unique=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    sub_industry: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_status: Mapped[str | None] = mapped_column(String, nullable=True)
    sales_stage: Mapped[str] = mapped_column(String, default="NEW", nullable=False, index=True) # NEW, RESEARCHED, QUALIFIED, CONTACTED, REPLIED, MEETING_SCHEDULED, PROPOSAL_SENT, NEGOTIATION, WON, LOST, NURTURE
    target_market: Mapped[str | None] = mapped_column(String, nullable=True)
    qualification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    stage_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Lead Social & Outreach Channels
    facebook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String, nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String, nullable=True)
    whatsapp_click_url: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    public_email: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_page_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Lead Scoring & GrokxSEO Opportunities
    lead_priority: Mapped[str] = mapped_column(String, default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    lead_score: Mapped[float | None] = mapped_column(Float, nullable=True) # 0-100 normalized score
    lead_score_components: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # SEO opp, business fit, evidence quality, website potential
    recommended_services: Mapped[list | None] = mapped_column(JSONB, nullable=True) # e.g. ["Technical SEO", "Link Building", "Digital PR"]
    seo_summary_findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Google Drive Synchronization
    gdrive_file_id: Mapped[str | None] = mapped_column(String, nullable=True)
    gdrive_file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    gdrive_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gdrive_sync_status: Mapped[str] = mapped_column(String, default="NOT_SYNCED", nullable=False) # NOT_SYNCED, PENDING, SYNCED, FAILED
    
    # Ownership & Follow-up
    lead_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    next_followup_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    first_discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class Domain(Base):
    __tablename__ = "domains"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    domain: Mapped[str] = mapped_column(String, nullable=False)
    canonical_domain: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    registrar: Mapped[str | None] = mapped_column(String, nullable=True)
    domain_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    domain_expiry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class Discovery(Base):
    __tablename__ = "discoveries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    discovery_method: Mapped[str] = mapped_column(String, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    query: Mapped[str | None] = mapped_column(String, nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True) # Will FK to jobs later
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    extraction_method: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, nullable=False)
    raw_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class WebsiteScan(Base):
    __tablename__ = "website_scans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    url: Mapped[str] = mapped_column(String, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    https_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    final_url: Mapped[str | None] = mapped_column(String, nullable=True)
    redirect_chain: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String, nullable=True)
    robots_meta: Mapped[str | None] = mapped_column(String, nullable=True)
    viewport: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    charset: Mapped[str | None] = mapped_column(String, nullable=True)
    h1: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    h2: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    open_graph: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    twitter_card: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    robots_txt_status: Mapped[str | None] = mapped_column(String, nullable=True)
    sitemap_status: Mapped[str | None] = mapped_column(String, nullable=True)
    schema_detected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cms_detected: Mapped[str | None] = mapped_column(String, nullable=True)
    technology_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    scan_status: Mapped[str] = mapped_column(String, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class SEOMetric(Base):
    __tablename__ = "seo_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_metric_name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, nullable=False)
    raw_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class SocialProfile(Base):
    __tablename__ = "social_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    platform: Mapped[str] = mapped_column(String, nullable=False)
    profile_url: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    verification_method: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, nullable=False) # LOW, MEDIUM, HIGH, UNKNOWN
    risk_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    methodology_version: Mapped[str] = mapped_column(String, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class HealthAssessment(Base):
    __tablename__ = "health_assessments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_status: Mapped[str] = mapped_column(String, nullable=False) # EXCELLENT, GOOD, NEEDS_ATTENTION, POOR, UNKNOWN
    health_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    methodology_version: Mapped[str] = mapped_column(String, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class HistoricalSnapshot(Base):
    __tablename__ = "historical_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_value: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class ProviderUsage(Base):
    __tablename__ = "provider_usage"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_units: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_units: Mapped[float | None] = mapped_column(Float, nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # QUEUED, RUNNING, PARTIAL, COMPLETED, FAILED, CANCELLED
    requested_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovered_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validated_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stored_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duplicate_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    successful_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partial_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_error_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics_created: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics_skipped: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class JobResult(Base):
    __tablename__ = "job_results"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    stage: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    input_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class Error(Base):
    __tablename__ = "errors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True)
    error_type: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    discovery_query: Mapped[str | None] = mapped_column(String, nullable=True)
    target_company_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_company_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    enabled_stages: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    schedule_cron: Mapped[str | None] = mapped_column(String, nullable=True)
    schedule_timezone: Mapped[str | None] = mapped_column(String, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    batch_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_request_limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    max_retries: Mapped[int | None] = mapped_column(Integer, nullable=True, default=3)
    retry_backoff_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, default=300)
    max_runtime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # QUEUED, RUNNING, PARTIAL, COMPLETED, FAILED, CANCELLED, PAUSED, PENDING_APPROVAL
    current_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    total_companies: Mapped[int] = mapped_column(Integer, default=0)
    successful_companies: Mapped[int] = mapped_column(Integer, default=0)
    failed_companies: Mapped[int] = mapped_column(Integer, default=0)
    skipped_stages: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    retry_counts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    provider_failures: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    stage_progress: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)


class AIExtractionRun(Base):
    __tablename__ = "ai_extraction_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    schema_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # COMPLETED, FAILED
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class AIObservation(Base):
    __tablename__ = "ai_observations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_extraction_runs.id"))
    attribute_name: Mapped[str] = mapped_column(String, nullable=False)
    attribute_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, nullable=False) # VERIFIED, UNVERIFIED, REJECTED
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class AIContradiction(Base):
    __tablename__ = "ai_contradictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    observation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_observations.id"))
    attribute_name: Mapped[str] = mapped_column(String, nullable=False)
    existing_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String, nullable=False, default="UNRESOLVED") # UNRESOLVED, ACCEPTED_NEW, KEPT_OLD
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class OpportunityProfile(Base):
    __tablename__ = "opportunity_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    recommended_service: Mapped[str] = mapped_column(String, nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_evidence: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    identified_problems: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    data_freshness: Mapped[str] = mapped_column(String, nullable=False)
    missing_information: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    recommended_next_action: Mapped[str | None] = mapped_column(String, nullable=True)
    methodology_version: Mapped[str] = mapped_column(String, nullable=False)
    calculation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class PublisherRecord(Base):
    __tablename__ = "publisher_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True)
    original_submitted_url: Mapped[str | None] = mapped_column(String, nullable=True)
    publisher_name: Mapped[str | None] = mapped_column(String, nullable=True)
    audience_focus: Mapped[str | None] = mapped_column(String, nullable=True)
    editorial_attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="UNVERIFIED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class PublisherObservation(Base):
    __tablename__ = "publisher_observations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"))
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String, nullable=True)
    pricing_model: Mapped[str | None] = mapped_column(String, nullable=True)
    metric_da: Mapped[float | None] = mapped_column(Float, nullable=True)
    metric_dr: Mapped[float | None] = mapped_column(Float, nullable=True)
    metric_traffic: Mapped[float | None] = mapped_column(Float, nullable=True)
    observation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    source_name: Mapped[str | None] = mapped_column(String, nullable=True)
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="UNVERIFIED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # PREVIEW, PROCESSING, COMPLETED, FAILED
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_records: Mapped[int] = mapped_column(Integer, default=0)
    updated_records: Mapped[int] = mapped_column(Integer, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class ImportAuditRow(Base):
    __tablename__ = "import_audit_rows"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_batches.id"))
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # SUCCESS, SKIPPED, FAILED
    action_taken: Mapped[str | None] = mapped_column(String, nullable=True) # CREATED, UPDATED
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    errors: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class CampaignProfile(Base):
    __tablename__ = "campaign_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True)
    target_geography: Mapped[str | None] = mapped_column(String, nullable=True)
    target_industry: Mapped[str | None] = mapped_column(String, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String, nullable=True)
    topics: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    max_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    campaign_objective: Mapped[str | None] = mapped_column(String, nullable=True)
    mandatory_constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class MatchingRun(Base):
    __tablename__ = "matching_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    profile_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scoring_model_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # RUNNING, COMPLETED, FAILED
    total_eligible: Mapped[int] = mapped_column(Integer, default=0)
    total_excluded: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matching_runs.id"))
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"))
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    component_scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reasons: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

class Shortlist(Base):
    __tablename__ = "shortlists"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shortlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shortlists.id"))
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"))
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("match_results.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class MediaPlan(Base):
    __tablename__ = "media_plans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String, nullable=False, default="Draft Media Plan")
    status: Mapped[str] = mapped_column(String, nullable=False, default="DRAFT") # DRAFT, FINAL
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class MediaPlanItem(Base):
    __tablename__ = "media_plan_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_plans.id"))
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"))
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("match_results.id"), nullable=True)
    proposed_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_currency: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class CompanyContact(Base):
    __tablename__ = "company_contacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    job_title: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False) # WEBSITE_PAGE, GITHUB_PUBLIC, MANUAL_ENTRY, SECURITY_TXT, DNS_RECORD
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    verification_status: Mapped[str] = mapped_column(String, default="UNVERIFIED", nullable=False) # VERIFIED, UNVERIFIED, INFERRED, REJECTED
    confidence: Mapped[float | None] = mapped_column(Float, default=0.5, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", nullable=False) # DRAFT, ACTIVE, PAUSED, ARCHIVED
    daily_send_limit: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    schedule_timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    follow_up_delay_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_follow_ups: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    stop_on_reply: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stop_on_bounce: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stop_on_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    template_subject: Mapped[str | None] = mapped_column(String, nullable=True)
    template_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id"), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subject_line: Mapped[str] = mapped_column(String, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_to_action: Mapped[str | None] = mapped_column(String, nullable=True)
    prospect_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_citations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", nullable=False) # DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, QUEUED, SENT, FAILED, CANCELLED
    approval_status: Mapped[str] = mapped_column(String, default="UNAPPROVED", nullable=False) # UNAPPROVED, APPROVED, REJECTED
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_draft_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outreach_drafts.id"), nullable=True)
    scheduled_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outreach_drafts.id"))
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id"), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False) # GMAIL, SMTP, MOCK
    provider_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_thread_id: Mapped[str | None] = mapped_column(String, nullable=True)
    sender_email: Mapped[str] = mapped_column(String, nullable=False)
    recipient_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject_line: Mapped[str] = mapped_column(String, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="SENT", nullable=False) # SENT, DELIVERED, OPENED, CLICKED, REPLIED, BOUNCED, UNSUBSCRIBED, FAILED
    delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bounced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class OutreachSuppression(Base):
    __tablename__ = "outreach_suppressions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String, nullable=False) # UNSUBSCRIBED, BOUNCED, MANUAL_OPTOUT, COMPLAINT
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class CRMDeal(Base):
    __tablename__ = "crm_deals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    deal_name: Mapped[str] = mapped_column(String, nullable=False)
    service_category: Mapped[str] = mapped_column(String, default="FULL_SERVICE", nullable=False) # TECHNICAL_SEO, LINK_BUILDING, CONTENT_STRATEGY, DIGITAL_PR, FULL_SERVICE, OTHER
    stage: Mapped[str] = mapped_column(String, default="DISCOVERY", nullable=False, index=True) # DISCOVERY, QUALIFICATION, PROPOSAL, NEGOTIATION, WON, LOST
    estimated_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    proposed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    closed_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    expected_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True) # WON, LOST, IN_PROGRESS
    loss_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    win_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    media_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_plans.id"), nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id"), nullable=True)
    cost_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    invoice_status: Mapped[str | None] = mapped_column(String, nullable=True) # UNINVOICED, DRAFT, ISSUED, PAID, PARTIALLY_PAID, REFUNDED
    invoiced_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    discount_amount: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    tax_amount: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    refunded_amount: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CRMTask(Base):
    __tablename__ = "crm_tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String, default="FOLLOW_UP", nullable=False) # CALL, MEETING, RESEARCH, FOLLOW_UP, EMAIL, OTHER
    priority: Mapped[str] = mapped_column(String, default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, URGENT
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False, index=True) # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CRMActivity(Base):
    __tablename__ = "crm_activities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    activity_type: Mapped[str] = mapped_column(String, nullable=False) # STAGE_CHANGE, TASK_CREATED, TASK_COMPLETED, NOTE_ADDED, DEAL_CREATED, DEAL_STAGE_CHANGE, DEAL_WON, DEAL_LOST, OUTREACH_DRAFTED, OUTREACH_SENT, REPLY_LOGGED, CALL_LOGGED, MEETING_LOGGED
    actor: Mapped[str] = mapped_column(String, default="human_reviewer", nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


class CRMNote(Base):
    __tablename__ = "crm_notes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=True)
    author: Mapped[str] = mapped_column(String, default="human_reviewer", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


# =========================================================================
# Phase 3.0: AI Sales Intelligence & Lead Prioritization
# =========================================================================

class SalesIntelligenceScore(Base):
    __tablename__ = "sales_intelligence_scores"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True, index=True)
    scoring_version: Mapped[str] = mapped_column(String, default="v3.0.0", nullable=False)
    overall_priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    seo_severity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    service_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    publisher_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    business_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    data_completeness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    primary_recommended_service: Mapped[str | None] = mapped_column(String, nullable=True)
    recommended_services: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    positive_indicators: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    limitations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    missing_information: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    component_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_next_action: Mapped[str | None] = mapped_column(String, nullable=True)
    review_status: Mapped[str] = mapped_column(String, default="UNREVIEWED", nullable=False, index=True) # UNREVIEWED, IN_REVIEW, QUALIFIED, REJECTED
    human_override_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_override_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    human_override_by: Mapped[str | None] = mapped_column(String, nullable=True)
    human_override_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True) # TECHNICAL_SEO, INDEXABILITY_CRAWLABILITY, PAGE_METADATA, CONTENT_COVERAGE, INTERNAL_LINKING, BACKLINK_AUTHORITY, COMPETITIVE_GAP, DIGITAL_PR_PUBLISHER
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, default="MEDIUM", nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW
    impact_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String, nullable=False)
    supporting_evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False, index=True) # ACTIVE, IN_PROGRESS, RESOLVED, IGNORED
    detection_rule: Mapped[str] = mapped_column(String, nullable=False)
    detection_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SalesBrief(Base):
    __tablename__ = "sales_briefs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company_overview: Mapped[str] = mapped_column(Text, nullable=False)
    seo_findings_summary: Mapped[str] = mapped_column(Text, nullable=False)
    top_opportunities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommended_services: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    matched_publishers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    data_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    discovery_questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommended_next_action: Mapped[str | None] = mapped_column(String, nullable=True)
    full_brief_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    is_customized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_edited_by: Mapped[str | None] = mapped_column(String, nullable=True)
    last_edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


# =========================================================================
# Phase 3.1: Publisher Intelligence & Data Quality Monitoring
# =========================================================================

class PublisherQualityScore(Base):
    __tablename__ = "publisher_quality_scores"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"), unique=True, index=True)
    overall_quality_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False, index=True)
    completeness_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    validity_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    price_freshness_status: Mapped[str] = mapped_column(String, default="UNKNOWN", nullable=False) # FRESH, STALE, MISSING, EXPIRED
    metrics_freshness_status: Mapped[str] = mapped_column(String, default="UNKNOWN", nullable=False) # FRESH, STALE, MISSING, EXPIRED
    site_freshness_status: Mapped[str] = mapped_column(String, default="UNKNOWN", nullable=False) # FRESH, STALE, MISSING, EXPIRED
    last_price_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_metrics_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_site_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_duplicates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_conflicts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class PublisherQualityFinding(Base):
    __tablename__ = "publisher_quality_findings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"), index=True)
    issue_type: Mapped[str] = mapped_column(String, nullable=False, index=True) # MISSING_FIELD, STALE_DATA, INVALID_DATA, DUPLICATE_RECORD, CONFLICTING_DATA
    field_name: Mapped[str] = mapped_column(String, nullable=False) # price, currency, metric_da, metric_dr, metric_traffic, audience_focus, website_url, canonical_domain
    severity: Mapped[str] = mapped_column(String, default="MEDIUM", nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="OPEN", nullable=False, index=True) # OPEN, RESOLVED, DISMISSED, IN_REVIEW
    resolution_action: Mapped[str | None] = mapped_column(String, nullable=True) # MANUAL_OVERRIDE, ACCEPTED_VALUE, MERGED_NOTE, DISMISSED_FALSE_POSITIVE, REFRESHED_PROVIDER
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class PublisherRefreshLog(Base):
    __tablename__ = "publisher_refresh_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publisher_records.id"), index=True)
    target_field: Mapped[str] = mapped_column(String, nullable=False) # metrics, site, price, all
    provider_attempted: Mapped[str] = mapped_column(String, nullable=False) # Moz, Ahrefs, Semrush, Crawler, Manual
    status: Mapped[str] = mapped_column(String, nullable=False, index=True) # SUCCESS, FAILED, RATE_LIMITED, PROVIDER_NOT_CONFIGURED, UNAVAILABLE
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    initiated_by: Mapped[str] = mapped_column(String, default="system_audit", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


# =========================================================================
# Phase 3.2: Revenue & Performance Analytics
# =========================================================================

class RevenueAnalyticsSnapshot(Base):
    __tablename__ = "revenue_analytics_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_type: Mapped[str] = mapped_column(String, default="ALL_TIME", nullable=False, index=True) # ALL_TIME, 30D, 90D, 180D, YTD, MONTHLY, CUSTOM
    reporting_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_realized_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_open_pipeline_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weighted_pipeline_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_recorded_costs: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    deal_count_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deal_count_lost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deal_count_open: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_deal_size_won: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_sales_cycle_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_by_service: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    revenue_by_client: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    revenue_by_campaign: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    funnel_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    currency_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_limitations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_by: Mapped[str] = mapped_column(String, default="system", nullable=False)


# =========================================================================
# Phase 3.3: Advanced Competitive SEO Intelligence
# =========================================================================

class CompanyCompetitor(Base):
    __tablename__ = "company_competitors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    competitor_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    competitor_name: Mapped[str] = mapped_column(String, nullable=False)
    competitor_domain: Mapped[str] = mapped_column(String, nullable=False, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # 0.0 to 1.0
    relevance_tier: Mapped[str] = mapped_column(String, default="DIRECT", nullable=False) # DIRECT, INDIRECT, TOPICAL_PEER, IRRELEVANT
    validation_status: Mapped[str] = mapped_column(String, default="VERIFIED", nullable=False) # VERIFIED, UNVERIFIED, REJECTED
    validation_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    discovery_method: Mapped[str] = mapped_column(String, default="INDUSTRY_TOPICAL_OVERLAP", nullable=False) # MANUAL, INDUSTRY_TOPICAL_OVERLAP, SEARCH_SERP_OVERLAP, CONTENT_COMPARISON
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CompetitiveAnalysisRun(Base):
    __tablename__ = "competitive_analysis_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    competitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company_competitors.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="COMPLETED", nullable=False, index=True) # PENDING, RUNNING, COMPLETED, FAILED
    prospect_scan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("website_scans.id"), nullable=True)
    competitor_scan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("website_scans.id"), nullable=True)
    summary_findings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Keyword/topical clusters and search intent gaps
    technical_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Metadata, schema, mobile, robots, sitemaps
    internal_linking_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Silo depth, orphan topics, hierarchy
    backlink_gaps: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # Referring domains, DA/DR diff, authorized provider citations
    publisher_opportunities: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Relevant inventory publishers for digital PR
    prioritized_recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Mapped to GrokxSEO service categories
    data_limitations: Mapped[list | None] = mapped_column(JSONB, nullable=True) # Known gaps, unconfigured provider notices
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


# =========================================================================
# Phase 3.4: Automated Reporting & Client Portals
# =========================================================================

class PortalUser(Base):
    __tablename__ = "portal_users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="CLIENT_USER", nullable=False, index=True) # ADMIN, AGENCY_STAFF, CLIENT_USER
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ClientInvitation(Base):
    __tablename__ = "client_invitations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    invitation_token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, default="CLIENT_USER", nullable=False) # CLIENT_USER, AGENCY_STAFF
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False, index=True) # PENDING, ACCEPTED, EXPIRED, REVOKED
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class ClientReport(Base):
    __tablename__ = "client_reports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    report_type: Mapped[str] = mapped_column(String, default="MONTHLY_PERFORMANCE", nullable=False, index=True) # MONTHLY_PERFORMANCE, QUARTERLY_REVIEW, SEO_AUDIT_DELIVERABLE, EXECUTIVE_SUMMARY, CAMPAIGN_SUMMARY
    reporting_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporting_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", nullable=False, index=True) # DRAFT, PENDING_REVIEW, APPROVED, DELIVERED, ARCHIVED
    approval_status: Mapped[str] = mapped_column(String, default="UNAPPROVED", nullable=False, index=True) # UNAPPROVED, APPROVED, REJECTED
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    branding: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # logo_url, brand_name, primary_color, client_name, footer_text
    sections: Mapped[list | None] = mapped_column(JSONB, nullable=True) # structured sections array
    summary_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # client-visible high-level metrics
    delivery_status: Mapped[str] = mapped_column(String, default="NOT_DELIVERED", nullable=False) # NOT_DELIVERED, SCHEDULED, SENT, FAILED
    generated_by: Mapped[str] = mapped_column(String, default="manual_operator", nullable=False) # manual_operator, automated_job
    data_limitations: Mapped[list | None] = mapped_column(JSONB, nullable=True) # transparency notes and caveats
    export_formats: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # html, markdown, pdf paths and metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ReportSchedule(Base):
    __tablename__ = "report_schedules"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String, default="MONTHLY_PERFORMANCE", nullable=False)
    frequency: Mapped[str] = mapped_column(String, default="MONTHLY", nullable=False) # WEEKLY, MONTHLY, QUARTERLY
    day_of_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # 0=Monday
    time_of_day: Mapped[str] = mapped_column(String, default="09:00", nullable=False)
    time_zone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    recipients: Mapped[list | None] = mapped_column(JSONB, nullable=True) # list of recipient email strings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # safety gate before delivery
    last_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ReportDeliveryLog(Base):
    __tablename__ = "report_delivery_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("client_reports.id"), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    delivery_channel: Mapped[str] = mapped_column(String, default="EMAIL", nullable=False) # EMAIL, PORTAL_NOTIFICATION
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False, index=True) # PENDING, SENT, FAILED, SIMULATED
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class PortalAuditLog(Base):
    __tablename__ = "portal_audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("portal_users.id"), nullable=True, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True) # LOGIN, LOGOUT, VIEW_REPORT, EXPORT_REPORT, INVITE_USER, REVOKE_USER, APPROVE_REPORT, UNAUTHORIZED_ACCESS_ATTEMPT
    resource_type: Mapped[str] = mapped_column(String, nullable=False) # REPORT, INVITATION, USER, PORTAL_PAGE
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


# =========================================================================
# Phase 4.1: Google Drive Sync & Social Multi-Channel Outreach
# =========================================================================

class GoogleDriveConnection(Base):
    __tablename__ = "google_drive_connections"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    account_email: Mapped[str | None] = mapped_column(String, nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String, nullable=True)
    client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_folder_id: Mapped[str | None] = mapped_column(String, nullable=True)
    selected_folder_path: Mapped[str] = mapped_column(String, default="ProspectOS/Leads/", nullable=False)
    master_sheet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    master_sheet_url: Mapped[str | None] = mapped_column(String, nullable=True)
    export_format: Mapped[str] = mapped_column(String, default="GOOGLE_SHEET", nullable=False) # GOOGLE_SHEET, CSV, JSON
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str] = mapped_column(String, default="IDLE", nullable=False) # IDLE, RUNNING, SUCCESS, FAILED
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class GoogleDriveSyncJob(Base):
    __tablename__ = "google_drive_sync_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False, index=True) # PENDING, RUNNING, COMPLETED, FAILED
    sync_type: Mapped[str] = mapped_column(String, default="AUTOMATIC", nullable=False) # AUTOMATIC, MANUAL
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True) # Drive file ID or sheet row ID
    resource_url: Mapped[str | None] = mapped_column(String, nullable=True)
    destination_folder: Mapped[str | None] = mapped_column(String, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SocialConnection(Base):
    __tablename__ = "social_connections"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True) # FACEBOOK, INSTAGRAM, WHATSAPP
    account_name: Mapped[str | None] = mapped_column(String, nullable=True)
    account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True) # For WhatsApp Business
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permissions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messaging_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_successful_operation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    configuration_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SocialMessageLog(Base):
    __tablename__ = "social_message_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("company_contacts.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String, nullable=False, index=True) # FACEBOOK, INSTAGRAM, WHATSAPP
    direction: Mapped[str] = mapped_column(String, default="OUTBOUND", nullable=False) # OUTBOUND, INBOUND
    recipient_identifier: Mapped[str] = mapped_column(String, nullable=False) # phone, page url, or profile handle
    sender_account: Mapped[str | None] = mapped_column(String, nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    template_name: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PREPARED", nullable=False, index=True) # PREPARED, CLICK_TO_CHAT, SENT, DELIVERED, READ, FAILED, BLOCKED
    api_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    click_to_chat_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    explicit_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


