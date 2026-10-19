import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


VALID_RELEVANCE_TIERS = ["DIRECT", "INDIRECT", "TOPICAL_PEER", "IRRELEVANT"]
VALID_VALIDATION_STATUSES = ["VERIFIED", "UNVERIFIED", "REJECTED"]
VALID_SEARCH_INTENTS = ["INFORMATIONAL", "COMMERCIAL", "TRANSACTIONAL", "NAVIGATIONAL"]
VALID_GAP_CATEGORIES = [
    "CONTENT_GAP",
    "TECHNICAL_GAP",
    "INTERNAL_LINKING_GAP",
    "BACKLINK_GAP",
    "DIGITAL_PR_GAP"
]


# ==========================================
# 1. Competitor Management Schemas
# ==========================================

class CompetitorBase(BaseModel):
    competitor_name: str
    competitor_domain: str
    relevance_tier: str = "DIRECT"
    notes: Optional[str] = None


class CompetitorCreate(CompetitorBase):
    company_id: uuid.UUID
    competitor_company_id: Optional[uuid.UUID] = None
    relevance_score: float = 0.85
    discovery_method: str = "MANUAL"


class CompetitorUpdate(BaseModel):
    competitor_name: Optional[str] = None
    relevance_score: Optional[float] = None
    relevance_tier: Optional[str] = None
    validation_status: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CompetitorResponse(CompetitorBase):
    id: uuid.UUID
    company_id: uuid.UUID
    competitor_company_id: Optional[uuid.UUID] = None
    relevance_score: float
    relevance_tier: str
    validation_status: str
    validation_evidence: Optional[Dict[str, Any]] = None
    discovery_method: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorCandidate(BaseModel):
    company_id: Optional[uuid.UUID] = None
    company_name: str
    canonical_domain: str
    industry: Optional[str] = None
    relevance_score: float
    relevance_tier: str
    overlap_evidence: Dict[str, Any]
    discovery_method: str


class CompetitorDiscoveryRequest(BaseModel):
    company_id: uuid.UUID
    max_results: int = 5
    persist_discovered: bool = False


# ==========================================
# 2. Granular Gap Objects
# ==========================================

class ContentGapItem(BaseModel):
    topic: str
    search_intent: str # INFORMATIONAL, COMMERCIAL, TRANSACTIONAL, NAVIGATIONAL
    competitor_coverage: str
    prospect_status: str # ABSENT, THIN, POORLY_STRUCTURED
    prospect_coverage: Optional[str] = None
    recommended_action: str
    recommended_service: str # CONTENT_STRATEGY, CONTENT_ARCHITECTURE
    severity: str # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float = 1.0
    estimated_effort: str = "MEDIUM" # LOW, MEDIUM, HIGH
    potential_impact: str = "HIGH" # HIGH, MEDIUM, LOW


class TechnicalGapItem(BaseModel):
    metric_or_feature: str # Schema, Headings, Robots, Sitemap, Viewport, CMS
    prospect_state: str
    competitor_state: str
    gap_description: str
    severity: str
    confidence: float = 1.0
    recommended_service: str # TECHNICAL_SEO, WEB_DESIGN_DEVELOPMENT
    recommended_action: str


class InternalLinkingGapItem(BaseModel):
    silo_topic: str
    prospect_issue: str
    competitor_advantage: str
    recommended_service: str # CONTENT_ARCHITECTURE, TECHNICAL_SEO
    recommended_action: str
    severity: str
    confidence: float = 1.0


class BacklinkGapSummary(BaseModel):
    prospect_domain: str
    competitor_domain: str
    prospect_da: Optional[float] = None
    competitor_da: Optional[float] = None
    da_differential: Optional[float] = None
    prospect_dr: Optional[float] = None
    competitor_dr: Optional[float] = None
    dr_differential: Optional[float] = None
    prospect_ref_domains: Optional[int] = None
    competitor_ref_domains: Optional[int] = None
    provider_source: str
    is_provider_configured: bool = False
    limitations: List[str] = Field(default_factory=list)


class PublisherPROpportunityItem(BaseModel):
    publisher_id: uuid.UUID
    publisher_name: str
    canonical_domain: str
    audience_focus: str
    da: Optional[float] = None
    dr: Optional[float] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    relevance_rationale: str
    recommended_service: str # DIGITAL_PR, LINK_BUILDING, GUEST_POSTING


class CompetitiveRecommendation(BaseModel):
    id: str
    title: str
    category: str # CONTENT_GAP, TECHNICAL_GAP, INTERNAL_LINKING_GAP, BACKLINK_GAP, DIGITAL_PR_GAP
    service: str # Maps to GrokxSEO services
    severity: str
    rationale: str
    action: str
    supporting_evidence: Dict[str, Any]
    confidence: float
    effort: str
    impact: str
    priority_score: float # 0.0 to 100.0


# ==========================================
# 3. Competitive Analysis Run Schemas
# ==========================================

class RunAnalysisRequest(BaseModel):
    competitor_id: Optional[uuid.UUID] = None
    competitor_domain: Optional[str] = None
    sync_to_sales_opportunities: bool = True


class CompetitiveAnalysisRunResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    competitor_id: uuid.UUID
    competitor_name: str
    competitor_domain: str
    status: str
    prospect_scan_available: bool
    competitor_scan_available: bool
    summary_findings: Dict[str, Any]
    content_gaps: List[ContentGapItem]
    technical_gaps: List[TechnicalGapItem]
    internal_linking_gaps: List[InternalLinkingGapItem]
    backlink_gaps: BacklinkGapSummary
    publisher_opportunities: List[PublisherPROpportunityItem]
    prioritized_recommendations: List[CompetitiveRecommendation]
    data_limitations: List[str]
    analyzed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitiveOverviewResponse(BaseModel):
    company_id: uuid.UUID
    company_name: str
    canonical_domain: Optional[str] = None
    competitors_count: int
    analyzed_runs_count: int
    top_competitors: List[CompetitorResponse]
    latest_run: Optional[CompetitiveAnalysisRunResponse] = None
    total_content_gaps: int = 0
    total_technical_gaps: int = 0
    total_publisher_opportunities: int = 0
    data_limitations: List[str] = Field(default_factory=list)
