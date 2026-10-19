from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

VALID_WORKFLOW_STAGES = [
    'discovery',
    'website_analysis',
    'seo_enrichment',
    'ai_extraction',
    'opportunity_scoring',
    'publisher_matching',
    'media_plan_generation',
    'human_review'
]

class WorkflowBase(BaseModel):
    name: str
    discovery_query: Optional[str] = None
    target_company_count: Optional[int] = Field(default=None, le=1000)
    selected_company_ids: Optional[List[str]] = None
    enabled_stages: List[str]
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    batch_size: Optional[int] = Field(default=10, le=100)
    provider_request_limits: Optional[Dict[str, int]] = None
    max_retries: Optional[int] = Field(default=3, le=10)
    retry_backoff_seconds: Optional[int] = Field(default=300)
    max_runtime_seconds: Optional[int] = Field(default=3600)
    is_enabled: bool = False
    
    @field_validator('enabled_stages')
    def validate_stages(cls, v):
        for stage in v:
            if stage not in VALID_WORKFLOW_STAGES:
                raise ValueError(f"Invalid stage: {stage}. Must be one of {VALID_WORKFLOW_STAGES}")
        return v
        
    @field_validator('target_company_count')
    def validate_limits(cls, v, info):
        enabled = info.data.get('enabled_stages', [])
        selected = info.data.get('selected_company_ids')
        if not v and 'discovery' in enabled and not selected:
            # If discovery is in stages and no explicit target count or selected companies, default or require
            raise ValueError("Target company count required for discovery stage unless selected_company_ids are provided")
        return v

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    discovery_query: Optional[str] = None
    target_company_count: Optional[int] = Field(default=None, le=1000)
    selected_company_ids: Optional[List[str]] = None
    enabled_stages: Optional[List[str]] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    batch_size: Optional[int] = Field(default=None, le=100)
    provider_request_limits: Optional[Dict[str, int]] = None
    max_retries: Optional[int] = Field(default=None, le=10)
    retry_backoff_seconds: Optional[int] = None
    max_runtime_seconds: Optional[int] = None
    is_enabled: Optional[bool] = None

class WorkflowInDB(WorkflowBase):
    id: uuid.UUID
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class WorkflowRunTriggerRequest(BaseModel):
    trigger_type: str = "manual"
    company_ids: Optional[List[str]] = None
    force: bool = False

class WorkflowRunApproveRequest(BaseModel):
    approved_by: str = "human_reviewer"
    notes: Optional[str] = None

class WorkflowRunRejectRequest(BaseModel):
    rejected_by: str = "human_reviewer"
    reason: Optional[str] = "Rejected during human review"

class WorkflowRunBase(BaseModel):
    workflow_id: uuid.UUID
    trigger_type: str
    status: str
    current_stage: Optional[str] = None
    total_companies: int = 0
    successful_companies: int = 0
    failed_companies: int = 0
    skipped_stages: Optional[List[str]] = None
    retry_counts: Optional[Dict[str, int]] = None
    provider_failures: Optional[Dict[str, int]] = None
    stage_progress: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    planned_run_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

class WorkflowRunInDB(WorkflowRunBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
