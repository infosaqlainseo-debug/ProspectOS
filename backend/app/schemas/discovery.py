from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class DiscoveryRequest(BaseModel):
    target_count: int = Field(default=50, gt=0, le=1000)
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    company_type: Optional[str] = None
    company_size: Optional[str] = None
    website_or_domain: Optional[str] = None
    business_type: Optional[str] = None
    min_seo_score: Optional[float] = None
    max_seo_score: Optional[float] = None
    desired_service_opportunity: Optional[str] = None
    source_preferences: List[str] = Field(default_factory=lambda: ["duckduckgo", "directory"])
    exclusions: List[str] = Field(default_factory=list)
    exclusion_rules: List[str] = Field(default_factory=list)
    include_previously_discovered: bool = False
    min_data_quality: Optional[str] = "accessible_website"
    auto_sync_to_gdrive: bool = True
    auto_generate_drafts: bool = True
    freshness_window: Optional[str] = None
    query: Optional[str] = None
    template_id: Optional[str] = None


class DiscoveryResult(BaseModel):
    company_name: str
    website_url: Optional[str]
    canonical_domain: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    source_url: Optional[str] = None
    source_name: str
    discovery_method: str
    confidence: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    public_email: Optional[str] = None
    phone_number: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    whatsapp_number: Optional[str] = None


class NLQueryParseRequest(BaseModel):
    query: str = Field(..., min_length=3)


class StructuredSearchConfig(BaseModel):
    raw_query: str
    interpreted_summary: str
    target_count: int = 50
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website_or_domain: Optional[str] = None
    business_type: Optional[str] = None
    min_seo_score: Optional[float] = None
    max_seo_score: Optional[float] = None
    desired_service_opportunity: Optional[str] = None
    source_preferences: List[str] = Field(default_factory=lambda: ["duckduckgo", "directory"])
    exclusion_rules: List[str] = Field(default_factory=list)
    include_previously_discovered: bool = False
    min_data_quality: Optional[str] = "accessible_website"
    confidence_score: float = 0.95


class NLQueryParseResponse(BaseModel):
    success: bool
    config: StructuredSearchConfig
    parsing_method: str  # "anthropic_claude" or "rule_heuristic_engine"


class ScrapingTemplate(BaseModel):
    id: str
    name: str
    category: str
    country: str
    industry: str
    description: str
    target_count: int
    default_sources: List[str]
    extraction_fields: List[str]
    validation_rules: List[str]
    desired_services: List[str]
    min_seo_opportunity_score: float
    config_requirements: Dict[str, str] = Field(default_factory=dict)
    is_available: bool = True


class DiscoveryJobDetail(BaseModel):
    job_id: uuid.UUID
    status: str
    job_type: str
    job_name: Optional[str] = None
    search_criteria: Optional[Dict[str, Any]] = None
    data_sources: List[str] = Field(default_factory=list)
    requested_count: int
    discovered_count: int
    validated_count: int
    stored_count: int
    duplicate_count: int
    failed_count: int
    websites_analyzed: int = 0
    leads_saved: int = 0
    gdrive_synced_count: int = 0
    gdrive_sync_status: str = "IDLE"
    current_stage: str = "COMPLETED"
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    estimated_cost: float = 0.0
    api_usage_units: float = 0.0
    error_message: Optional[str] = None
    error_summary: List[str] = Field(default_factory=list)
    retry_eligible: bool = False
