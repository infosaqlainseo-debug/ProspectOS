from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid

class MediaPlanItemBase(BaseModel):
    publisher_id: uuid.UUID
    match_result_id: Optional[uuid.UUID] = None
    proposed_price: Optional[float] = None
    proposed_currency: Optional[str] = None
    notes: Optional[str] = None

class MediaPlanItemCreate(MediaPlanItemBase):
    pass

class MediaPlanItemResponse(MediaPlanItemBase):
    id: uuid.UUID
    media_plan_id: uuid.UUID
    created_at: datetime
    
    # We will include related data manually in the API response or use nested models
    publisher_name: Optional[str] = None
    canonical_domain: Optional[str] = None
    metric_da: Optional[float] = None
    metric_dr: Optional[float] = None
    metric_traffic: Optional[float] = None
    verification_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class MediaPlanBase(BaseModel):
    name: str = "Draft Media Plan"
    status: str = "DRAFT"
    notes: Optional[str] = None

class MediaPlanCreate(MediaPlanBase):
    pass

class MediaPlanUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MediaPlanResponse(MediaPlanBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    items: List[MediaPlanItemResponse] = []
    
    # Calculated totals
    total_price: Optional[float] = None
    currency: Optional[str] = None
    can_calculate_totals: bool = True
    calculation_warning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
