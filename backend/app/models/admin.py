import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PlatformSetting(Base):
    """
    Stores platform-wide settings by category (GENERAL, APPEARANCE, SCRAPER, AI, NOTIFICATIONS, SECURITY, SYSTEM).
    """
    __tablename__ = "platform_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True) # GENERAL, APPEARANCE, SCRAPER, AI, NOTIFICATIONS, SECURITY, SYSTEM
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class RolePermission(Base):
    """
    Stores granular permissions for each platform role.
    """
    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True) # SUPER_ADMIN, ADMIN, MANAGER, MEMBER, READ_ONLY
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict) # {"scraper": ["read", "write", "execute"], ...}
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SEOGlobalConfig(Base):
    """
    Global SEO configuration for the public website.
    """
    __tablename__ = "seo_global_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_name: Mapped[str] = mapped_column(String, default="ProspectOS", nullable=False)
    default_meta_title: Mapped[str] = mapped_column(String, default="ProspectOS | AI Web Scraping & Lead Intelligence Platform", nullable=False)
    default_meta_description: Mapped[str] = mapped_column(Text, default="Enterprise web scraping, autonomous prospect discovery, and AI-powered CRM intelligence system.", nullable=False)
    default_canonical_domain: Mapped[str] = mapped_column(String, default="https://prospectos.com", nullable=False)
    default_og_image_url: Mapped[Optional[str]] = mapped_column(String, default="/og-image.png", nullable=True)
    robots_txt_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sitemap_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    gsc_verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ga4_measurement_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bing_verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class SEOPublicPage(Base):
    """
    Page-level SEO metadata and audit information for public website routes.
    """
    __tablename__ = "seo_public_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True) # e.g. "/", "/solutions", "/features", "/pricing", "/docs"
    page_name: Mapped[str] = mapped_column(String, nullable=False)
    meta_title: Mapped[str] = mapped_column(String, nullable=False)
    meta_description: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(String, nullable=False)
    og_title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    og_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    og_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    twitter_card: Mapped[str] = mapped_column(String, default="summary_large_image", nullable=False)
    robots_directives: Mapped[str] = mapped_column(String, default="index,follow", nullable=False) # index,follow or noindex,nofollow
    schema_type: Mapped[str] = mapped_column(String, default="SoftwareApplication", nullable=False) # SoftwareApplication, Organization, WebSite, Product, FAQPage
    structured_data_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    sitemap_priority: Mapped[float] = mapped_column(Float, default=0.8, nullable=False) # 0.1 to 1.0
    change_frequency: Mapped[str] = mapped_column(String, default="weekly", nullable=False) # always, hourly, daily, weekly, monthly, yearly
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    audit_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False) # 0 - 100
    audit_issues: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class AIProviderSetting(Base):
    """
    Configured AI providers, model parameters, quota tracking and feature availability.
    """
    __tablename__ = "ai_provider_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True) # gemini, openai, anthropic, deepseek, ollama
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_model: Mapped[str] = mapped_column(String, nullable=False)
    available_models: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    api_key_masked: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rpm_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    tpm_limit: Mapped[int] = mapped_column(Integer, default=100000, nullable=False)
    tokens_used_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feature_flags: Mapped[Dict[str, bool]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

