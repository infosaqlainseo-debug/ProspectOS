import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# =========================================================================
# Taxonomies & Enumerations
# =========================================================================

VALID_OPPORTUNITY_CATEGORIES = [
    "TECHNICAL_SEO",
    "INDEXABILITY_CRAWLABILITY",
    "PAGE_METADATA",
    "CONTENT_COVERAGE",
    "INTERNAL_LINKING",
    "BACKLINK_AUTHORITY",
    "COMPETITIVE_GAP",
    "DIGITAL_PR_PUBLISHER"
]

VALID_SEVERITIES = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW"
]

VALID_GROKXSEO_SERVICES = [
    "TECHNICAL_SEO",
    "SEO_STRATEGY",
    "CONTENT_STRATEGY",
    "CONTENT_ARCHITECTURE",
    "LINK_BUILDING",
    "DIGITAL_PR",
    "GUEST_POSTING",
    "LOCAL_SEO",
    "CONVERSION_OPTIMIZATION",
    "WEB_DESIGN_DEVELOPMENT"
]

VALID_REVIEW_STATUSES = [
    "UNREVIEWED",
    "IN_REVIEW",
    "QUALIFIED",
    "REJECTED"
]

DEFAULT_SCORING_WEIGHTS = {
    "seo_severity": 0.35,
    "service_fit": 0.25,
    "publisher_fit": 0.20,
    "business_fit": 0.10,
    "evidence_confidence": 0.10
}


# =========================================================================
# 1. Opportunity Schemas
# =========================================================================

class OpportunityItemResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    category: str
    title: str
    description: str
    severity: str
    impact_rationale: str
    confidence: float
    recommended_service: str
    supporting_evidence: Optional[List[Dict[str, Any]]] = None
    status: str
    detection_rule: str
    detection_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 2. Service Recommendation Schemas
# =========================================================================

class ServiceRecommendation(BaseModel):
    service_name: str
    fit_score: float
    rationale: str
    supporting_opportunities_count: int


# =========================================================================
# 3. Scoring & Priority Schemas
# =========================================================================

class SalesIntelligenceScoreResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    scoring_version: str
    overall_priority_score: float
    seo_severity_score: float
    service_fit_score: float
    publisher_fit_score: float
    business_fit_score: float
    evidence_confidence_score: float
    data_completeness: float
    primary_recommended_service: Optional[str] = None
    recommended_services: Optional[List[Dict[str, Any]]] = None
    positive_indicators: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    component_weights: Optional[Dict[str, float]] = None
    recommended_next_action: Optional[str] = None
    review_status: str
    human_override_score: Optional[float] = None
    human_override_reason: Optional[str] = None
    human_override_by: Optional[str] = None
    human_override_at: Optional[datetime] = None
    evaluated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScoreOverrideRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Override score between 0 and 100")
    reason: str = Field(..., min_length=3, description="Documented rationale for score override")
    actor: Optional[str] = "human_reviewer"


class ReviewStatusUpdateRequest(BaseModel):
    review_status: str = Field(..., description="UNREVIEWED, IN_REVIEW, QUALIFIED, REJECTED")
    notes: Optional[str] = None
    actor: Optional[str] = "human_reviewer"


# =========================================================================
# 4. Sales Brief Schemas
# =========================================================================

class SalesBriefResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    company_overview: str
    seo_findings_summary: str
    top_opportunities: Optional[List[Dict[str, Any]]] = None
    recommended_services: Optional[List[Dict[str, Any]]] = None
    matched_publishers: Optional[List[Dict[str, Any]]] = None
    data_gaps: Optional[List[str]] = None
    discovery_questions: Optional[List[str]] = None
    recommended_next_action: Optional[str] = None
    full_brief_markdown: str
    is_customized: bool
    last_edited_by: Optional[str] = None
    last_edited_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesBriefUpdateRequest(BaseModel):
    full_brief_markdown: str
    title: Optional[str] = None
    editor: Optional[str] = "human_reviewer"


# =========================================================================
# 5. Prioritization Queue & Comparison Schemas
# =========================================================================

class PrioritizedProspectItem(BaseModel):
    company_id: uuid.UUID
    company_name: Optional[str] = None
    canonical_domain: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    target_market: Optional[str] = None
    sales_stage: str
    overall_priority_score: float
    effective_score: float # human_override_score if present else overall_priority_score
    has_human_override: bool
    seo_severity_score: float
    service_fit_score: float
    publisher_fit_score: float
    evidence_confidence_score: float
    primary_recommended_service: Optional[str] = None
    total_opportunities: int
    critical_opportunities_count: int
    matched_publishers_count: int
    review_status: str
    evaluated_at: Optional[datetime] = None


class PrioritizedQueueResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[PrioritizedProspectItem]


class ProspectComparisonDetail(BaseModel):
    company_id: uuid.UUID
    company_name: Optional[str] = None
    canonical_domain: Optional[str] = None
    industry: Optional[str] = None
    sales_stage: str
    score: Optional[SalesIntelligenceScoreResponse] = None
    opportunities: List[OpportunityItemResponse] = []
    top_matched_publishers: List[Dict[str, Any]] = []
    brief_overview: Optional[str] = None


class ProspectComparisonResponse(BaseModel):
    compared_prospects: List[ProspectComparisonDetail]


class BatchEvaluationRequest(BaseModel):
    company_ids: Optional[List[uuid.UUID]] = None
    evaluate_all: Optional[bool] = False
    force_recalculate: Optional[bool] = False
