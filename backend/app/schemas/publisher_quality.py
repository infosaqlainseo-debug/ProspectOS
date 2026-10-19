import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# =========================================================================
# Taxonomies & Constants
# =========================================================================

VALID_ISSUE_TYPES = [
    "MISSING_FIELD",
    "STALE_DATA",
    "INVALID_DATA",
    "DUPLICATE_RECORD",
    "CONFLICTING_DATA"
]

VALID_SEVERITIES = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "INFO"
]

VALID_FINDING_STATUSES = [
    "OPEN",
    "RESOLVED",
    "DISMISSED",
    "IN_REVIEW"
]

VALID_RESOLUTION_ACTIONS = [
    "MANUAL_OVERRIDE",
    "ACCEPTED_VALUE",
    "MERGED_NOTE",
    "DISMISSED_FALSE_POSITIVE",
    "REFRESHED_PROVIDER"
]

VALID_FRESHNESS_STATUSES = [
    "FRESH",
    "STALE",
    "MISSING",
    "EXPIRED",
    "UNKNOWN"
]

# Configurable Freshness Thresholds (in days)
DEFAULT_FRESHNESS_THRESHOLDS = {
    "price_days": 30,
    "metrics_days": 60,
    "site_days": 14
}


# =========================================================================
# 1. Finding Schemas
# =========================================================================

class PublisherQualityFindingResponse(BaseModel):
    id: uuid.UUID
    publisher_id: uuid.UUID
    issue_type: str
    field_name: str
    severity: str
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    recommended_action: str
    status: str
    resolution_action: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QualityFindingResolveRequest(BaseModel):
    resolution_action: str = Field(..., description="MANUAL_OVERRIDE, ACCEPTED_VALUE, MERGED_NOTE, DISMISSED_FALSE_POSITIVE, REFRESHED_PROVIDER")
    resolution_notes: Optional[str] = Field(None, description="Detailed reasoning or justification for resolution")
    actor: str = Field("human_reviewer", description="User identity performing resolution")


# =========================================================================
# 2. Quality Score Schemas
# =========================================================================

class PublisherQualityScoreResponse(BaseModel):
    id: uuid.UUID
    publisher_id: uuid.UUID
    overall_quality_score: float
    completeness_score: float
    freshness_score: float
    validity_score: float
    consistency_score: float
    price_freshness_status: str
    metrics_freshness_status: str
    site_freshness_status: str
    last_price_checked_at: Optional[datetime] = None
    last_metrics_checked_at: Optional[datetime] = None
    last_site_checked_at: Optional[datetime] = None
    open_issues_count: int
    critical_issues_count: int
    has_duplicates: bool
    has_conflicts: bool
    last_audited_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 3. Provenance & Observation Schemas
# =========================================================================

class PublisherObservationTimelineItem(BaseModel):
    id: uuid.UUID
    price: Optional[float] = None
    currency: Optional[str] = None
    pricing_model: Optional[str] = None
    metric_da: Optional[float] = None
    metric_dr: Optional[float] = None
    metric_traffic: Optional[float] = None
    observation_timestamp: datetime
    source_name: Optional[str] = None
    verification_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublisherDetailedQualityResponse(BaseModel):
    publisher_id: uuid.UUID
    company_id: uuid.UUID
    publisher_name: Optional[str] = None
    canonical_domain: Optional[str] = None
    original_submitted_url: Optional[str] = None
    audience_focus: Optional[str] = None
    status: str
    quality_score: Optional[PublisherQualityScoreResponse] = None
    open_findings: List[PublisherQualityFindingResponse] = Field(default_factory=list)
    resolved_findings: List[PublisherQualityFindingResponse] = Field(default_factory=list)
    observations_history: List[PublisherObservationTimelineItem] = Field(default_factory=list)
    field_freshness: Dict[str, Any] = Field(default_factory=dict)


# =========================================================================
# 4. Summary & Queue Schemas
# =========================================================================

class QualitySeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class QualityIssueBreakdown(BaseModel):
    missing_field: int = 0
    stale_data: int = 0
    invalid_data: int = 0
    duplicate_record: int = 0
    conflicting_data: int = 0


class PublisherQualitySummaryResponse(BaseModel):
    total_publishers: int
    audited_publishers: int
    average_quality_score: float
    publishers_with_critical_issues: int
    publishers_with_stale_data: int
    publishers_with_duplicates: int
    publishers_with_conflicts: int
    total_open_findings: int
    severity_breakdown: QualitySeverityBreakdown
    issue_type_breakdown: QualityIssueBreakdown
    last_audit_run_at: Optional[datetime] = None


# =========================================================================
# 5. Requests & Logs
# =========================================================================

class ManualCorrectionRequest(BaseModel):
    price: Optional[float] = Field(None, ge=0.0, description="Corrected placement price")
    currency: Optional[str] = Field(None, description="ISO Currency Code (e.g. USD, EUR, GBP)")
    metric_da: Optional[float] = Field(None, ge=0.0, le=100.0, description="Corrected Domain Authority")
    metric_dr: Optional[float] = Field(None, ge=0.0, le=100.0, description="Corrected Domain Rating")
    metric_traffic: Optional[float] = Field(None, ge=0.0, description="Estimated monthly traffic")
    pricing_model: Optional[str] = Field(None, description="FLAT, CPM, SPONSORED, GUEST_POST")
    notes: str = Field(..., description="Justification and provenance reference for manual correction")
    actor: str = Field("human_reviewer", description="Identifier of the editor making this correction")


class PublisherRefreshRequest(BaseModel):
    target_fields: List[str] = Field(default_factory=lambda: ["metrics", "site"], description="Fields to refresh: 'metrics', 'site'")
    actor: str = Field("user", description="Who requested the refresh")


class PublisherRefreshLogResponse(BaseModel):
    id: uuid.UUID
    publisher_id: uuid.UUID
    target_field: str
    provider_attempted: str
    status: str
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    initiated_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchAuditRequest(BaseModel):
    publisher_ids: Optional[List[uuid.UUID]] = Field(None, description="Specific IDs to audit or all if omitted")
    limit: Optional[int] = Field(100, ge=1, le=1000)
