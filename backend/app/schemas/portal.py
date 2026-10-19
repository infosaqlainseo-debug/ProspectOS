import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


VALID_ROLES = ["ADMIN", "AGENCY_STAFF", "CLIENT_USER"]
VALID_REPORT_TYPES = [
    "MONTHLY_PERFORMANCE",
    "QUARTERLY_REVIEW",
    "SEO_AUDIT_DELIVERABLE",
    "EXECUTIVE_SUMMARY",
    "CAMPAIGN_SUMMARY"
]
VALID_REPORT_STATUSES = ["DRAFT", "PENDING_REVIEW", "APPROVED", "DELIVERED", "ARCHIVED"]
VALID_APPROVAL_STATUSES = ["UNAPPROVED", "APPROVED", "REJECTED"]
VALID_FREQUENCIES = ["WEEKLY", "MONTHLY", "QUARTERLY"]


# =========================================================================
# 1. User & Authentication Schemas
# =========================================================================

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_id: Optional[uuid.UUID] = None
    role: str = "CLIENT_USER"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InviteCreateRequest(BaseModel):
    company_id: uuid.UUID
    email: EmailStr
    role: str = "CLIENT_USER"


class InviteAcceptRequest(BaseModel):
    invitation_token: str
    password: str
    full_name: str


class InviteResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: Optional[str] = None
    email: str
    invitation_token: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 2. Client Reporting Schemas
# =========================================================================

class ReportCreateRequest(BaseModel):
    company_id: uuid.UUID
    title: str
    report_type: str = "MONTHLY_PERFORMANCE"
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    branding: Optional[Dict[str, Any]] = None
    custom_notes: Optional[str] = None


class ReportUpdateRequest(BaseModel):
    title: Optional[str] = None
    branding: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ReportApprovalRequest(BaseModel):
    approval_status: str # APPROVED, REJECTED
    notes: Optional[str] = None


class ReportDeliveryRequest(BaseModel):
    recipients: Optional[List[str]] = None
    delivery_channel: str = "EMAIL"
    simulate: bool = False


class ClientReportResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    title: str
    report_type: str
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    status: str
    approval_status: str
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    branding: Optional[Dict[str, Any]] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    summary_metrics: Optional[Dict[str, Any]] = None
    delivery_status: str
    generated_by: str
    data_limitations: List[str] = Field(default_factory=list)
    export_formats: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 3. Report Scheduling Schemas
# =========================================================================

class ScheduleCreateRequest(BaseModel):
    company_id: uuid.UUID
    report_type: str = "MONTHLY_PERFORMANCE"
    frequency: str = "MONTHLY"
    day_of_month: int = 1
    day_of_week: int = 0
    time_of_day: str = "09:00"
    time_zone: str = "UTC"
    recipients: List[str] = Field(default_factory=list)
    requires_approval: bool = True


class ScheduleUpdateRequest(BaseModel):
    frequency: Optional[str] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    time_of_day: Optional[str] = None
    time_zone: Optional[str] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: Optional[str] = None
    report_type: str
    frequency: str
    day_of_month: int
    day_of_week: int
    time_of_day: str
    time_zone: str
    recipients: List[str] = Field(default_factory=list)
    is_active: bool
    requires_approval: bool
    last_generated_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryLogResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    recipient_email: str
    delivery_channel: str
    idempotency_key: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 4. Portal Workspace & Audit Schemas
# =========================================================================

class PortalWorkspaceResponse(BaseModel):
    company_id: uuid.UUID
    company_name: str
    canonical_domain: Optional[str] = None
    industry: Optional[str] = None
    client_user: UserResponse
    latest_approved_report: Optional[ClientReportResponse] = None
    available_reports_count: int = 0
    active_campaigns_count: int = 0
    approved_media_plans_count: int = 0
    verified_seo_health: Dict[str, Any] = Field(default_factory=dict)
    client_visible_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    branding: Dict[str, Any] = Field(default_factory=dict)
    data_freshness: Dict[str, Any] = Field(default_factory=dict)


class PortalAuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
