from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ImportPreviewRequest(BaseModel):
    file_name: str
    rows: List[Dict[str, Any]]

class PublisherMapping(BaseModel):
    url_column: str
    publisher_name_column: Optional[str] = None
    price_column: Optional[str] = None
    currency_column: Optional[str] = None
    da_column: Optional[str] = None
    dr_column: Optional[str] = None
    traffic_column: Optional[str] = None
    industry_column: Optional[str] = None
    audience_column: Optional[str] = None

class ImportCommitRequest(BaseModel):
    batch_id: UUID
    mapping: PublisherMapping
    rows: List[Dict[str, Any]]
    dry_run: bool = False

from pydantic import ConfigDict

class PublisherRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    original_submitted_url: Optional[str] = None
    publisher_name: Optional[str] = None
    audience_focus: Optional[str] = None
    status: str
    created_at: datetime
    canonical_domain: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    metric_da: Optional[float] = None
    metric_dr: Optional[float] = None
    metric_traffic: Optional[float] = None
    quality_overall_score: Optional[float] = None
    quality_verdict: Optional[str] = None
    has_duplicates: Optional[bool] = None
    is_stale: Optional[bool] = None

class ImportBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    created_records: int
    updated_records: int
    skipped_rows: int
    failed_rows: int
    created_at: datetime
