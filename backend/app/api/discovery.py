import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from arq import create_pool
from arq.connections import RedisSettings

from app.db.session import get_db
from app.models import Job, JobResult, Company
from app.schemas.discovery import (
    DiscoveryRequest, NLQueryParseRequest, NLQueryParseResponse,
    ScrapingTemplate, DiscoveryJobDetail
)
from app.services.discovery.nl_parser import parse_natural_language_query
from app.services.discovery.templates import PROSPECTING_TEMPLATES, get_template_by_id
from app.services.discovery.manager import source_manager
from app.core.config import settings

router = APIRouter()

async def get_redis_pool():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


@router.post("/parse-query", response_model=NLQueryParseResponse)
async def parse_query_endpoint(payload: NLQueryParseRequest):
    """Parses a natural-language prospecting instruction into a structured, editable search configuration."""
    try:
        return await parse_natural_language_query(payload.query)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to interpret query: {str(e)}")


@router.get("/templates", response_model=List[ScrapingTemplate])
async def list_templates_endpoint():
    """Lists the reusable prospecting templates."""
    return PROSPECTING_TEMPLATES


@router.get("/sources")
async def list_sources_endpoint():
    """Lists available data source adapters with permissions, rate limits, and status."""
    return source_manager.list_sources()


@router.post("/jobs")
async def create_discovery_job(
    request: DiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis_pool)
):
    """Creates and enqueues a lead discovery job with configured parameters and sources."""
    # Determine job name from query, template, or criteria
    job_name = request.query
    if request.template_id:
        tmpl = get_template_by_id(request.template_id)
        if tmpl:
            job_name = f"{tmpl.name} ({request.target_count} leads)"
    if not job_name:
        job_name = f"Discover {request.target_count} leads in {request.country or 'Target Market'} ({request.industry or 'General'})"

    params = request.model_dump()
    params["job_name"] = job_name

    job = Job(
        job_type="company_discovery",
        status="QUEUED",
        requested_count=request.target_count,
        parameters=params
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        await redis.enqueue_job(
            "company_discovery_job",
            str(job.id),
            request.model_dump()
        )
    except Exception as e:
        job.status = "FAILED"
        job.error_message = f"Failed to enqueue background job: {str(e)}"
        await db.commit()
        await redis.close()
        raise HTTPException(status_code=503, detail="Job queue unavailable")

    await redis.close()

    return {
        "job_id": job.id,
        "job_name": job_name,
        "status": job.status,
        "requested_count": job.requested_count
    }


@router.get("/jobs")
async def list_discovery_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns paginated history of discovery jobs with execution metrics."""
    stmt = (
        select(Job)
        .where(Job.job_type == "company_discovery")
        .order_by(desc(Job.created_at))
    )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    jobs = (await db.execute(stmt)).scalars().all()

    items = []
    for j in jobs:
        params = j.parameters or {}
        items.append({
            "job_id": str(j.id),
            "job_name": params.get("job_name") or f"Discovery Job #{str(j.id)[:8]}",
            "status": j.status,
            "job_type": j.job_type,
            "country": params.get("country"),
            "industry": params.get("industry"),
            "sources": params.get("source_preferences", ["duckduckgo", "directory"]),
            "requested_count": j.requested_count or 0,
            "discovered_count": j.discovered_count or 0,
            "validated_count": j.validated_count or 0,
            "stored_count": j.stored_count or 0,
            "duplicate_count": j.duplicate_count or 0,
            "failed_count": j.failed_count or 0,
            "error_message": j.error_message,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/jobs/{job_id}")
async def get_discovery_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns detailed status and statistics for a specific discovery job."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    params = job.parameters or {}

    # Query leads saved by this job
    stmt_results = (
        select(Company)
        .join(JobResult, JobResult.company_id == Company.id)
        .where(JobResult.job_id == job.id, JobResult.status == "COMPLETED")
        .limit(20)
    )
    saved_companies = (await db.execute(stmt_results)).scalars().all()

    leads_preview = [
        {
            "id": str(c.id),
            "company_name": c.company_name or c.canonical_domain,
            "canonical_domain": c.canonical_domain,
            "country": c.country,
            "industry": c.industry,
            "lead_score": c.lead_score,
            "lead_priority": c.lead_priority,
            "sales_stage": c.sales_stage,
            "gdrive_sync_status": c.gdrive_sync_status,
            "whatsapp_click_url": c.whatsapp_click_url
        }
        for c in saved_companies
    ]

    return {
        "job_id": job.id,
        "job_name": params.get("job_name") or f"Discovery Job #{str(job.id)[:8]}",
        "status": job.status,
        "job_type": job.job_type,
        "search_criteria": params,
        "data_sources": params.get("source_preferences", ["duckduckgo", "directory"]),
        "requested_count": job.requested_count or 0,
        "discovered_count": job.discovered_count or 0,
        "validated_count": job.validated_count or 0,
        "stored_count": job.stored_count or 0,
        "duplicate_count": job.duplicate_count or 0,
        "failed_count": job.failed_count or 0,
        "error_message": job.error_message,
        "start_time": job.started_at.isoformat() if job.started_at else None,
        "completion_time": job.completed_at.isoformat() if job.completed_at else None,
        "leads_preview": leads_preview,
        "retry_eligible": job.status in ["FAILED", "PARTIAL"]
    }


@router.post("/jobs/{job_id}/cancel")
async def cancel_discovery_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Safely cancels an in-progress discovery job."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["COMPLETED", "FAILED", "CANCELLED"]:
        return {"status": job.status, "message": f"Job is already {job.status}"}

    job.status = "CANCELLED"
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = "Cancelled by user operator."
    await db.commit()

    return {"status": "CANCELLED", "job_id": str(job.id)}


@router.post("/jobs/{job_id}/retry")
async def retry_discovery_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis_pool)
):
    """Resumes or retries a failed discovery job without generating duplicate records."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    params = job.parameters or {}
    job.status = "QUEUED"
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    await db.commit()

    await redis.enqueue_job(
        "company_discovery_job",
        str(job.id),
        params
    )
    await redis.close()

    return {"status": "QUEUED", "job_id": str(job.id), "message": "Job re-enqueued for safe processing."}
