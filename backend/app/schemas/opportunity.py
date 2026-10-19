from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class OpportunityProfileBase(BaseModel):
    recommended_service: str
    opportunity_score: float
    supporting_evidence: List[Dict[str, Any]]
    identified_problems: List[str]
    confidence_level: float
    data_freshness: str
    missing_information: List[str]
    recommended_next_action: Optional[str] = None
    methodology_version: str

class OpportunityProfileCreate(OpportunityProfileBase):
    company_id: uuid.UUID

class OpportunityProfile(OpportunityProfileBase):
    id: uuid.UUID
    company_id: uuid.UUID
    calculation_timestamp: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
