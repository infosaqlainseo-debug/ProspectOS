import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

def get_utc_now():
    return datetime.now(timezone.utc)


class CRMLeadSegment(Base):
    __tablename__ = "crm_lead_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    filter_criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    color: Mapped[str] = mapped_column(String, default="blue", nullable=False)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CRMSegmentMember(Base):
    __tablename__ = "crm_segment_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_lead_segments.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class CRMUserPreference(Base):
    __tablename__ = "crm_user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, default="default_user", unique=True, index=True, nullable=False)
    preferred_industries: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    preferred_countries: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    min_lead_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    scoring_weights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    target_market_rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CRMFeedbackLog(Base):
    __tablename__ = "crm_feedback_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    action_taken: Mapped[str] = mapped_column(String, nullable=False, index=True)  # QUALIFIED, REJECTED, STAGE_CHANGE, SCORE_OVERRIDE, PRIORITY_CHANGE
    previous_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    new_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String, default="human_reviewer", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)


class CRMAIResearch(Base):
    __tablename__ = "crm_ai_research"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), unique=True, index=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_market: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_proposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_weaknesses: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    backlink_opportunities: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    recommended_services: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    growth_opportunities: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    tech_stack_detected: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    model_used: Mapped[str] = mapped_column(String, default="gemini-2.5-pro", nullable=False)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CRMCustomField(Base):
    __tablename__ = "crm_custom_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    field_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    field_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_type: Mapped[str] = mapped_column(String, default="TEXT", nullable=False)  # TEXT, NUMBER, DATE, SELECT, BOOLEAN

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

