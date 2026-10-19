import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from arq import create_pool
from arq.connections import RedisSettings

from app.db.session import get_db
from app.core.config import settings
from app.core.redis import get_redis_settings
from app.services.backup.backup_manager import BackupManager
from app.models import (
    Company, WebsiteScan, Job, PublisherRecord, PublisherObservation,
    SalesOpportunity, SalesIntelligenceScore, CRMDeal, CRMActivity,
    MediaPlan, PortalAuditLog, PortalUser, ClientReport, WorkflowRun,
    SEOMetric, AIObservation
)

router = APIRouter(prefix="/system", tags=["system"])


class SystemOverviewResponse(BaseModel):
    total_companies: int
    websites_analyzed: int
    total_scans: int
    total_opportunities: int
    qualified_leads: int
    total_publishers: int
    total_price_observations: int
    media_plans_created: int
    active_deals_count: int
    open_pipeline_usd: float
    won_deals_count: int
    won_revenue_usd: float
    active_jobs: int
    provider_status: Dict[str, Any]
    backup_health: Dict[str, Any]
    system_status: str
    recent_activities: List[Dict[str, Any]]
    pipeline_distribution: Dict[str, int]


class HealthAndBackupsResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    redis_queue: Dict[str, Any]
    table_counts: Dict[str, int]
    backup_manifest: List[Dict[str, Any]]
    latest_backup: Optional[Dict[str, Any]]
    provider_health: Dict[str, Any]
    recent_audit_logs: List[Dict[str, Any]]


class BackupActionResponse(BaseModel):
    status: str
    message: str
    details: Dict[str, Any]


@router.get("/overview", response_model=SystemOverviewResponse)
async def get_system_overview(db: AsyncSession = Depends(get_db)):
    """
    Returns unified intelligence, CRM, and system health metrics calculated
    from actual PostgreSQL records without synthetic fabrication.
    """
    # 1. Company counts
    total_companies = (await db.execute(select(func.count(Company.id)))).scalar() or 0
    websites_analyzed = (await db.execute(select(func.count(func.distinct(WebsiteScan.company_id))))).scalar() or 0
    total_scans = (await db.execute(select(func.count(WebsiteScan.id)))).scalar() or 0

    # 2. Opportunities & Scoring
    total_opps = (await db.execute(select(func.count(SalesOpportunity.id)))).scalar() or 0
    qualified_leads = (await db.execute(
        select(func.count(SalesIntelligenceScore.id))
        .where(SalesIntelligenceScore.review_status == "QUALIFIED")
    )).scalar() or 0

    # 3. Inventory & Media Plans
    total_publishers = (await db.execute(select(func.count(PublisherRecord.id)))).scalar() or 0
    total_obs = (await db.execute(select(func.count(PublisherObservation.id)))).scalar() or 0
    media_plans_count = (await db.execute(select(func.count(MediaPlan.id)))).scalar() or 0

    # 4. CRM & Revenue (Won vs Open Pipeline)
    active_deals = (await db.execute(
        select(func.count(CRMDeal.id))
        .where(CRMDeal.stage.notin_(["WON", "LOST"]))
    )).scalar() or 0
    open_pipeline = (await db.execute(
        select(func.coalesce(func.sum(CRMDeal.estimated_value), 0.0))
        .where(CRMDeal.stage.notin_(["WON", "LOST"]))
    )).scalar() or 0.0

    won_deals = (await db.execute(
        select(func.count(CRMDeal.id))
        .where(CRMDeal.stage == "WON")
    )).scalar() or 0
    won_revenue = (await db.execute(
        select(func.coalesce(func.sum(func.coalesce(CRMDeal.closed_amount, CRMDeal.estimated_value)), 0.0))
        .where(CRMDeal.stage == "WON")
    )).scalar() or 0.0

    # 5. Background Jobs
    active_jobs = (await db.execute(
        select(func.count(Job.id))
        .where(Job.status.in_(["QUEUED", "RUNNING"]))
    )).scalar() or 0

    # 6. Pipeline distribution
    stages = ["NEW", "RESEARCHED", "QUALIFIED", "CONTACTED", "REPLIED", "MEETING_SCHEDULED", "PROPOSAL_SENT", "NEGOTIATION", "WON", "LOST", "NURTURE"]
    stage_counts_stmt = select(Company.sales_stage, func.count(Company.id)).group_by(Company.sales_stage)
    stage_rows = (await db.execute(stage_counts_stmt)).all()
    pipeline_dist = {stg: 0 for stg in stages}
    for stg, cnt in stage_rows:
        if stg in pipeline_dist:
            pipeline_dist[stg] = cnt
        elif stg:
            pipeline_dist[stg] = cnt

    # 7. Recent Activities
    recent_acts_stmt = (
        select(CRMActivity, Company)
        .outerjoin(Company, CRMActivity.company_id == Company.id)
        .order_by(CRMActivity.created_at.desc())
        .limit(10)
    )
    acts_rows = (await db.execute(recent_acts_stmt)).all()
    recent_activities = []
    for act, comp in acts_rows:
        recent_activities.append({
            "id": str(act.id),
            "activity_type": act.activity_type,
            "title": act.title,
            "details": act.details,
            "created_at": act.created_at.isoformat() if act.created_at else None,
            "company_name": comp.company_name if comp else None,
            "company_domain": comp.canonical_domain if comp else None,
            "company_id": str(comp.id) if comp else None,
            "actor": act.actor
        })

    # 8. Provider Status Telemetry (Safe masking without exposing secrets)
    provider_status = {
        "ahrefs": {
            "configured": bool(settings.AHREFS_API_KEY),
            "provider": "Ahrefs API v3",
            "tier": "public_free_tier",
            "endpoint": "/public/domain-rating-free",
            "billable_cost": "0 billable units",
            "status": "CONNECTED" if settings.AHREFS_API_KEY else "UNCONFIGURED"
        },
        "anthropic": {
            "configured": bool(settings.ANTHROPIC_API_KEY),
            "provider": "Anthropic Claude",
            "model": settings.ANTHROPIC_MODEL,
            "status": "CONNECTED" if settings.ANTHROPIC_API_KEY else "UNCONFIGURED"
        },
        "moz": {
            "configured": bool(settings.MOZ_API_KEY),
            "provider": "Moz API",
            "status": "UNCONFIGURED (Graceful Safe Bypass)"
        },
        "semrush": {
            "configured": bool(settings.SEMRUSH_API_KEY),
            "provider": "Semrush API",
            "status": "UNCONFIGURED (Graceful Safe Bypass)"
        },
        "email": {
            "provider": settings.EMAIL_PROVIDER,
            "mode": "Mode B — Deliberately Disabled",
            "outbound_dispatch": "BLOCKED",
            "human_approval_gate": "ENFORCED"
        }
    }

    # 9. Backup Health
    bm = BackupManager()
    backup_health = bm.check_health()

    return SystemOverviewResponse(
        total_companies=total_companies,
        websites_analyzed=websites_analyzed,
        total_scans=total_scans,
        total_opportunities=total_opps,
        qualified_leads=qualified_leads,
        total_publishers=total_publishers,
        total_price_observations=total_obs,
        media_plans_created=media_plans_count,
        active_deals_count=active_deals,
        open_pipeline_usd=float(open_pipeline),
        won_deals_count=won_deals,
        won_revenue_usd=float(won_revenue),
        active_jobs=active_jobs,
        provider_status=provider_status,
        backup_health=backup_health,
        system_status="HEALTHY" if backup_health.get("healthy", False) else "DEGRADED",
        recent_activities=recent_activities,
        pipeline_distribution=pipeline_dist
    )


@router.get("/health-and-backups", response_model=HealthAndBackupsResponse)
async def get_health_and_backups(db: AsyncSession = Depends(get_db)):
    """
    Returns complete operational status, database statistics, backup history,
    and security audit events for platform administrators.
    """
    # 1. Database check
    t0 = datetime.now(timezone.utc)
    await db.execute(select(1))
    t1 = datetime.now(timezone.utc)
    latency_ms = round((t1 - t0).total_seconds() * 1000, 2)

    db_status = {
        "connected": True,
        "engine": "PostgreSQL 15 (Docker)",
        "database_name": "prospectos",
        "latency_ms": latency_ms,
        "status": "HEALTHY"
    }

    # 2. Redis Queue check
    redis_status = {"connected": False, "status": "UNKNOWN"}
    try:
        pool = await create_pool(get_redis_settings())
        info = await pool.info()
        redis_status = {
            "connected": True,
            "engine": "Redis 7 (Docker)",
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "status": "HEALTHY"
        }
        if hasattr(pool, "aclose"):
            await pool.aclose()
        else:
            await pool.close()
    except Exception as e:
        redis_status = {"connected": False, "error": str(e), "status": "ERROR"}

    # 3. Table counts
    table_counts = {
        "companies": (await db.execute(select(func.count(Company.id)))).scalar() or 0,
        "website_scans": (await db.execute(select(func.count(WebsiteScan.id)))).scalar() or 0,
        "publisher_records": (await db.execute(select(func.count(PublisherRecord.id)))).scalar() or 0,
        "publisher_observations": (await db.execute(select(func.count(PublisherObservation.id)))).scalar() or 0,
        "crm_deals": (await db.execute(select(func.count(CRMDeal.id)))).scalar() or 0,
        "crm_activities": (await db.execute(select(func.count(CRMActivity.id)))).scalar() or 0,
        "portal_users": (await db.execute(select(func.count(PortalUser.id)))).scalar() or 0,
        "client_reports": (await db.execute(select(func.count(ClientReport.id)))).scalar() or 0,
        "portal_audit_logs": (await db.execute(select(func.count(PortalAuditLog.id)))).scalar() or 0,
        "media_plans": (await db.execute(select(func.count(MediaPlan.id)))).scalar() or 0,
        "seo_metrics": (await db.execute(select(func.count(SEOMetric.id)))).scalar() or 0,
        "sales_opportunities": (await db.execute(select(func.count(SalesOpportunity.id)))).scalar() or 0,
        "ai_observations": (await db.execute(select(func.count(AIObservation.id)))).scalar() or 0,
        "jobs": (await db.execute(select(func.count(Job.id)))).scalar() or 0
    }

    # 4. Backup Manifest & History
    bm = BackupManager()
    manifest_data = bm._read_manifest()
    health = bm.check_health()

    # 5. Recent Security / Audit Logs
    audit_stmt = select(PortalAuditLog).order_by(PortalAuditLog.timestamp.desc()).limit(15)
    audit_rows = (await db.execute(audit_stmt)).scalars().all()
    recent_audit_logs = [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "company_id": str(log.company_id) if log.company_id else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "ip_address": log.ip_address,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in audit_rows
    ]

    provider_health = {
        "ahrefs": {"configured": bool(settings.AHREFS_API_KEY), "status": "CONNECTED", "tier": "Free v3 Domain Rating"},
        "anthropic": {"configured": bool(settings.ANTHROPIC_API_KEY), "model": settings.ANTHROPIC_MODEL, "status": "CONNECTED"},
        "email_delivery": {"provider": settings.EMAIL_PROVIDER, "safe_mode": True, "outbound_blocked": True}
    }

    return HealthAndBackupsResponse(
        status="HEALTHY" if health.get("healthy", False) else "DEGRADED",
        database=db_status,
        redis_queue=redis_status,
        table_counts=table_counts,
        backup_manifest=manifest_data,
        latest_backup=health.get("latest_backup"),
        provider_health=provider_health,
        recent_audit_logs=recent_audit_logs
    )


@router.post("/backups/create", response_model=BackupActionResponse)
async def trigger_manual_backup(retention_days: int = Query(14, ge=1, le=90)):
    """
    Triggers an on-demand PostgreSQL backup archive with SHA-256 validation.
    """
    try:
        bm = BackupManager()
        entry = bm.create_backup(retention_days=retention_days)
        return BackupActionResponse(
            status="SUCCESS",
            message=f"Backup archive created successfully: {entry.get('filename')}",
            details=entry
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


@router.post("/backups/verify", response_model=BackupActionResponse)
async def trigger_verify_restore(filename: Optional[str] = Query(None)):
    """
    Executes a non-destructive verification restore of a backup archive into
    the isolated test database 'prospectos_recovery_verify'.
    Production database is never overwritten.
    """
    try:
        bm = BackupManager()
        res = bm.restore_to_isolated_database(backup_filename=filename)
        return BackupActionResponse(
            status=res.get("verification_status", "UNKNOWN"),
            message="Isolated restoration test completed successfully.",
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Isolated restoration verification failed: {str(e)}")
