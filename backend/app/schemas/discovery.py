from pydantic import BaseModel, Field
from typing import List, Optional

class DiscoveryRequest(BaseModel):
    target_count: int = Field(..., gt=0, le=1000)
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    company_type: Optional[str] = None
    freshness_window: Optional[str] = None
    query: Optional[str] = None
    exclusions: List[str] = Field(default_factory=list)

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
