import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class ScraperTask(Base):
    __tablename__ = "scraper_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String, default="CUSTOM", nullable=False, index=True) # CUSTOM, TEMPLATE, DISCOVERY, AUTO_DETECT
    template_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    target_url: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String, default="CLOUD", nullable=False) # CLOUD, LOCAL
    status: Mapped[str] = mapped_column(String, default="DRAFT", nullable=False, index=True) # DRAFT, QUEUED, RUNNING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, PAUSED, CANCELLED
    
    # Scheduling
    schedule_type: Mapped[str] = mapped_column(String, default="NONE", nullable=False) # NONE, ONCE, HOURLY, DAILY, WEEKLY, MONTHLY, CUSTOM
    schedule_cron: Mapped[str | None] = mapped_column(String, nullable=True)
    schedule_timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    is_schedule_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metrics
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ScraperTaskRun(Base):
    __tablename__ = "scraper_task_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scraper_tasks.id", ondelete="CASCADE"), index=True)
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String, default="CLOUD", nullable=False)
    status: Mapped[str] = mapped_column(String, default="QUEUED", nullable=False, index=True) # QUEUED, RUNNING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, CANCELLED
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    records_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_saved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[list] = mapped_column(JSONB, default=list, nullable=False) # List of {timestamp, level, message}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


class ExtractedRecord(Base):
    __tablename__ = "extracted_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scraper_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scraper_task_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    record_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    cleaned_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Core Lead Extraction fields
    company_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_profiles: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    discovery_source: Mapped[str] = mapped_column(String, default="SCRAPER", nullable=False, index=True)
    validation_status: Mapped[str] = mapped_column(String, default="VALID", nullable=False, index=True) # VALID, PARTIAL, FAILED
    quality_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    quality_status: Mapped[str] = mapped_column(String, default="HIGH", nullable=False) # HIGH, MEDIUM, LOW
    validation_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scraper_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    format: Mapped[str] = mapped_column(String, nullable=False) # CSV, XLSX, JSON, HTML, XML
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filter_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False) # PENDING, COMPLETED, FAILED
    download_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


class ScraperApiKey(Base):
    __tablename__ = "scraper_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    prefix: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

