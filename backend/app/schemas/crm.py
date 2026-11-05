import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

VALID_SALES_STAGES = [
    "NEW",
    "DATA_VALIDATION_REQUIRED",
    "RESEARCHED",
    "QUALIFIED",
    "READY_FOR_OUTREACH",
    "CONTACTED",
    "REPLIED",
    "INTERESTED",
    "MEETING_SCHEDULED",
    "PROPOSAL_SENT",
    "PROPOSAL_PREPARED",
    "NEGOTIATION",
    "WON",
    "LOST",
    "NOT_A_FIT",
    "NURTURE"
]

KANBAN_BOARD_STAGES = [
    "NEW",
    "RESEARCHED",
    "QUALIFIED",
    "CONTACTED",
    "REPLIED",
    "MEETING_SCHEDULED",
    "PROPOSAL_SENT",
    "NEGOTIATION",
    "WON",
    "LOST",
    "NURTURE"
]

VALID_DEAL_STAGES = [
    "DISCOVERY",
    "QUALIFICATION",
    "PROPOSAL",
    "NEGOTIATION",
    "WON",
    "LOST"
]

VALID_TASK_TYPES = [
    "CALL",
    "MEETING",
    "RESEARCH",
    "FOLLOW_UP",
    "EMAIL",
    "OTHER"
]

VALID_TASK_PRIORITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT"
]

VALID_TASK_STATUSES = [
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED"
]

VALID_SERVICE_CATEGORIES = [
    "TECHNICAL_SEO",
    "LINK_BUILDING",
    "CONTENT_STRATEGY",
    "DIGITAL_PR",
    "FULL_SERVICE",
    "OTHER"
]


# ==========================================
# 1. Pipeline Stage Change
# ==========================================

class StageUpdateRequest(BaseModel):
    new_stage: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


# ==========================================
# 2. Deal Schemas
# ==========================================

class DealBase(BaseModel):
    deal_name: str
    service_category: str = "FULL_SERVICE"
    stage: str = "DISCOVERY"
    estimated_value: float = 0.0
    proposed_value: Optional[float] = None
    currency: str = "USD"
    expected_close_date: Optional[datetime] = None
    contact_id: Optional[uuid.UUID] = None
    media_plan_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    cost_amount: Optional[float] = None
    invoice_status: Optional[str] = None
    invoiced_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    discount_amount: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    refunded_amount: Optional[float] = 0.0
    notes: Optional[str] = None


class DealCreate(DealBase):
    company_id: uuid.UUID


class DealUpdate(BaseModel):
    deal_name: Optional[str] = None
    service_category: Optional[str] = None
    stage: Optional[str] = None
    estimated_value: Optional[float] = None
    proposed_value: Optional[float] = None
    closed_amount: Optional[float] = None
    cost_amount: Optional[float] = None
    invoice_status: Optional[str] = None
    invoiced_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    refunded_amount: Optional[float] = None
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    outcome: Optional[str] = None
    loss_reason: Optional[str] = None
    win_reason: Optional[str] = None
    contact_id: Optional[uuid.UUID] = None
    media_plan_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


class DealResponse(DealBase):
    id: uuid.UUID
    company_id: uuid.UUID
    closed_amount: Optional[float] = None
    actual_close_date: Optional[datetime] = None
    outcome: Optional[str] = None
    loss_reason: Optional[str] = None
    win_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Task Schemas
# ==========================================

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: str = "FOLLOW_UP"
    priority: str = "MEDIUM"
    status: str = "PENDING"
    due_date: Optional[datetime] = None
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None


class TaskCreate(TaskBase):
    company_id: uuid.UUID
    idempotency_key: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    completed_notes: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


class TaskCompleteRequest(BaseModel):
    completed_by: Optional[str] = "human_reviewer"
    completion_notes: Optional[str] = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    company_id: uuid.UUID
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    completion_notes: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Activity & Note Schemas
# ==========================================

class ActivityResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    activity_type: str
    actor: str
    title: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    content: str
    deal_id: Optional[uuid.UUID] = None
    author: Optional[str] = "human_reviewer"


class NoteResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    deal_id: Optional[uuid.UUID] = None
    author: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Unified Prospect & Pipeline Views
# ==========================================

class UnifiedProspectSummary(BaseModel):
    id: uuid.UUID
    company_name: Optional[str] = None
    canonical_domain: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    target_market: Optional[str] = None
    sales_stage: str
    stage_updated_at: datetime
    stage_reason: Optional[str] = None
    opportunity_score: Optional[float] = None
    recommended_service: Optional[str] = None
    total_deals: int = 0
    open_deal_value: float = 0.0
    pending_tasks_count: int = 0
    verified_contacts_count: int = 0
    created_at: datetime
    
    # Social & Google Drive Extensions
    country: Optional[str] = None
    city: Optional[str] = None
    public_email: Optional[str] = None
    phone_number: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_click_url: Optional[str] = None
    gdrive_file_id: Optional[str] = None
    gdrive_file_url: Optional[str] = None
    gdrive_sync_status: Optional[str] = "NOT_SYNCED"
    lead_priority: Optional[str] = "MEDIUM"
    lead_score: Optional[float] = None
    lead_score_components: Optional[Dict[str, Any]] = None
    recommended_services: Optional[List[str]] = None
    seo_summary_findings: Optional[List[str]] = None
    lead_owner: Optional[str] = None



class UnifiedProspectDetail(BaseModel):
    company: Dict[str, Any]
    sales_stage: str
    stage_updated_at: datetime
    stage_reason: Optional[str] = None
    target_market: Optional[str] = None
    qualification_notes: Optional[str] = None
    opportunity_profile: Optional[Dict[str, Any]] = None
    website_scan: Optional[Dict[str, Any]] = None
    contacts: List[Dict[str, Any]] = []
    media_plans: List[Dict[str, Any]] = []
    outreach_drafts: List[Dict[str, Any]] = []
    outreach_messages: List[Dict[str, Any]] = []
    deals: List[DealResponse] = []
    tasks: List[TaskResponse] = []
    notes: List[NoteResponse] = []
    activities: List[ActivityResponse] = []


class PipelineColumn(BaseModel):
    stage: str
    stage_name: str
    prospects_count: int
    open_deals_count: int
    total_pipeline_value: float
    prospects: List[UnifiedProspectSummary]


class CRMReportMetrics(BaseModel):
    prospects_by_stage: Dict[str, int]
    total_prospects: int
    qualified_prospects_count: int
    outreach_sent_count: int
    replies_received_count: int
    meetings_scheduled_count: int
    proposals_sent_count: int
    won_deals_count: int
    lost_deals_count: int
    open_pipeline_value: float
    closed_won_revenue: float
    pipeline_currency: str = "USD"
    conversion_rates: Dict[str, Optional[float]]
    notes: List[str]


# ==========================================
# 6. Scraper-to-CRM Bridge Schemas
# ==========================================

class ScraperImportRequest(BaseModel):
    extracted_record_ids: Optional[List[uuid.UUID]] = None
    task_id: Optional[uuid.UUID] = None
    auto_save_valid_only: bool = True
    default_stage: str = "NEW"
    tags: List[str] = Field(default_factory=list)
    lead_source: str = "SCRAPER"
    conflict_resolution: str = "MERGE" # MERGE, OVERWRITE, SKIP


class ScraperImportResponse(BaseModel):
    success: bool
    total_processed: int
    added: int
    updated: int
    skipped: int
    flagged: int
    imported_ids: List[str] = Field(default_factory=list)
    message: str


# ==========================================
# 7. Lead Create & Update Schemas
# ==========================================

class LeadCreate(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    canonical_domain: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    company_size: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    public_email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    sales_stage: str = "NEW"
    lead_priority: str = "MEDIUM"
    lead_source: str = "MANUAL"
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    website_url: Optional[str] = None
    canonical_domain: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    company_size: Optional[str] = None
    contact_person: Optional[str] = None
    contact_title: Optional[str] = None
    public_email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    sales_stage: Optional[str] = None
    lead_priority: Optional[str] = None
    lead_score: Optional[float] = None
    lead_owner: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    qualification_notes: Optional[str] = None


class LeadBulkUpdateRequest(BaseModel):
    lead_ids: List[uuid.UUID]
    sales_stage: Optional[str] = None
    lead_priority: Optional[str] = None
    add_tags: Optional[List[str]] = None
    remove_tags: Optional[List[str]] = None
    lead_owner: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


class LeadBulkDeleteRequest(BaseModel):
    lead_ids: List[uuid.UUID]


# ==========================================
# 8. Segments & Lists Schemas
# ==========================================

class CRMLeadSegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_dynamic: bool = True
    filter_criteria: Dict[str, Any] = Field(default_factory=dict)
    color: str = "blue"
    icon: Optional[str] = "folder"


class CRMLeadSegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_dynamic: Optional[bool] = None
    filter_criteria: Optional[Dict[str, Any]] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CRMLeadSegmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_dynamic: bool
    filter_criteria: Dict[str, Any]
    color: str
    icon: Optional[str] = None
    member_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 9. Adaptive Learning & User Preferences Schemas
# ==========================================

class CRMUserPreferenceUpdate(BaseModel):
    preferred_industries: Optional[List[str]] = None
    preferred_countries: Optional[List[str]] = None
    min_lead_score: Optional[float] = None
    scoring_weights: Optional[Dict[str, float]] = None
    target_market_rules: Optional[Dict[str, Any]] = None


class CRMUserPreferenceResponse(BaseModel):
    user_id: str
    preferred_industries: List[str]
    preferred_countries: List[str]
    min_lead_score: float
    scoring_weights: Dict[str, float]
    target_market_rules: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMFeedbackLogCreate(BaseModel):
    company_id: uuid.UUID
    action_taken: str
    previous_stage: Optional[str] = None
    new_stage: Optional[str] = None
    previous_score: Optional[float] = None
    new_score: Optional[float] = None
    feedback_reason: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


class CRMFeedbackLogResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    action_taken: str
    previous_stage: Optional[str] = None
    new_stage: Optional[str] = None
    previous_score: Optional[float] = None
    new_score: Optional[float] = None
    feedback_reason: Optional[str] = None
    actor: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 10. AI Research & Intelligence Assistant Schemas
# ==========================================

class CRMAIResearchResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    executive_summary: Optional[str] = None
    target_market: Optional[str] = None
    value_proposition: Optional[str] = None
    seo_weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    backlink_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_services: List[str] = Field(default_factory=list)
    growth_opportunities: List[str] = Field(default_factory=list)
    tech_stack_detected: List[str] = Field(default_factory=list)
    confidence_score: float
    model_used: str
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAssistantQueryRequest(BaseModel):
    query: str
    context_filters: Optional[Dict[str, Any]] = None


class AIAssistantQueryResponse(BaseModel):
    answer: str
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    matched_leads: List[Dict[str, Any]] = Field(default_factory=list)
    sql_or_filter_used: Optional[str] = None
    confidence: float = 0.95

