import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# CONTACT SCHEMAS
# ============================================================================

class ContactBase(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    source_type: str = "WEBSITE_PAGE"  # WEBSITE_PAGE, GITHUB_PUBLIC, MANUAL_ENTRY, SECURITY_TXT, DNS_RECORD
    source_url: Optional[str] = None
    verification_status: str = "UNVERIFIED"  # VERIFIED, UNVERIFIED, INFERRED, REJECTED
    confidence: Optional[float] = 0.5
    is_primary: bool = False
    opt_out: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    company_id: uuid.UUID


class ContactUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    verification_status: Optional[str] = None
    confidence: Optional[float] = None
    is_primary: Optional[bool] = None
    opt_out: Optional[bool] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    id: uuid.UUID
    company_id: uuid.UUID
    retrieval_timestamp: datetime
    opt_out_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CAMPAIGN SCHEMAS
# ============================================================================

class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    daily_send_limit: int = 20
    schedule_timezone: str = "UTC"
    follow_up_delay_days: int = 3
    max_follow_ups: int = 2
    stop_on_reply: bool = True
    stop_on_bounce: bool = True
    stop_on_unsubscribe: bool = True
    template_subject: Optional[str] = None
    template_body: Optional[str] = None


class CampaignCreate(CampaignBase):
    status: str = "DRAFT"


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    daily_send_limit: Optional[int] = None
    schedule_timezone: Optional[str] = None
    follow_up_delay_days: Optional[int] = None
    max_follow_ups: Optional[int] = None
    stop_on_reply: Optional[bool] = None
    stop_on_bounce: Optional[bool] = None
    stop_on_unsubscribe: Optional[bool] = None
    template_subject: Optional[str] = None
    template_body: Optional[str] = None


class CampaignResponse(CampaignBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EVIDENCE & DRAFT SCHEMAS
# ============================================================================

class EvidenceCitation(BaseModel):
    claim: str
    source_type: str  # WebsiteScan, OpportunityProfile, SEOMetric, MediaPlan, PublisherRecord
    source_id: Optional[str] = None
    field_name: str
    value: Any
    confidence: float = 1.0


class DraftBase(BaseModel):
    recipient_email: str
    recipient_name: Optional[str] = None
    subject_line: str
    body_text: str
    body_html: Optional[str] = None
    call_to_action: Optional[str] = None
    prospect_summary: Optional[str] = None


class DraftCreate(DraftBase):
    company_id: uuid.UUID
    campaign_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    evidence_citations: Optional[List[Dict[str, Any]]] = None
    scheduled_send_at: Optional[datetime] = None


class DraftUpdate(BaseModel):
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    subject_line: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    call_to_action: Optional[str] = None
    prospect_summary: Optional[str] = None
    scheduled_send_at: Optional[datetime] = None


class DraftGenerateRequest(BaseModel):
    company_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    include_media_plan: bool = True
    save_draft: bool = True


class DraftPreviewResponse(BaseModel):
    company_id: uuid.UUID
    company_name: str
    canonical_domain: Optional[str]
    recipient_email: Optional[str]
    recipient_name: Optional[str]
    subject_line: str
    body_text: str
    body_html: Optional[str]
    call_to_action: Optional[str]
    prospect_summary: Optional[str]
    evidence_citations: List[Dict[str, Any]]


class DraftApproveRequest(BaseModel):
    approved_by: str = "human_reviewer"
    notes: Optional[str] = None


class DraftRejectRequest(BaseModel):
    rejected_by: str = "human_reviewer"
    reason: str


class DraftResponse(DraftBase):
    id: uuid.UUID
    campaign_id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    evidence_citations: Optional[List[Dict[str, Any]]] = None
    status: str
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    is_follow_up: bool
    sequence_step: int
    parent_draft_id: Optional[uuid.UUID] = None
    scheduled_send_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SEND & MESSAGE SCHEMAS
# ============================================================================

class SendDraftRequest(BaseModel):
    authorized_by: str = "human_reviewer"
    override_recipient_email: Optional[str] = None


class SendDraftResult(BaseModel):
    success: bool
    draft_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    provider: str
    provider_message_id: Optional[str] = None
    recipient_email: str
    status: str
    error: Optional[str] = None


class OutreachMessageResponse(BaseModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    campaign_id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    provider: str
    provider_message_id: Optional[str] = None
    sender_email: str
    recipient_email: str
    subject_line: str
    body_text: str
    status: str
    delivery_error: Optional[str] = None
    sent_at: datetime
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SUPPRESSION & PROVIDER SCHEMAS
# ============================================================================

class SuppressionCreate(BaseModel):
    email: str
    domain: Optional[str] = None
    reason: str = "MANUAL_OPTOUT"  # UNSUBSCRIBED, BOUNCED, MANUAL_OPTOUT, COMPLAINT
    source: Optional[str] = "admin_dashboard"


class SuppressionResponse(BaseModel):
    id: uuid.UUID
    email: str
    domain: Optional[str] = None
    reason: str
    source: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailProviderStatusResponse(BaseModel):
    configured_provider: str
    is_ready_to_send: bool
    sender_email: Optional[str] = None
    missing_configuration: List[str]
    supported_providers: List[str]
