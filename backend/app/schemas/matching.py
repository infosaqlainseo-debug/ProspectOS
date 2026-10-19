from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class CampaignProfileBase(BaseModel):
    target_geography: Optional[str] = None
    target_industry: Optional[str] = None
    target_audience: Optional[str] = None
    topics: Optional[List[str]] = None
    max_budget: Optional[float] = None
    budget_currency: str = "USD"
    campaign_objective: Optional[str] = None
    mandatory_constraints: Optional[Dict[str, Any]] = None

class CampaignProfileCreate(CampaignProfileBase):
    pass

class CampaignProfileResponse(CampaignProfileBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MatchResultResponse(BaseModel):
    id: uuid.UUID
    matching_run_id: uuid.UUID
    publisher_id: uuid.UUID
    overall_score: float
    rank: int
    component_scores: Dict[str, float]
    reasons: List[Dict[str, str]]
    warnings: Optional[List[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MatchingRunResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    profile_snapshot: Dict[str, Any]
    scoring_model_version: str
    status: str
    total_eligible: int
    total_excluded: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ShortlistCreate(BaseModel):
    name: str

class ShortlistResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
