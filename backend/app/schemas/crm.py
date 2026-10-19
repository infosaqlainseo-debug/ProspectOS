import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

VALID_SALES_STAGES = [
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
