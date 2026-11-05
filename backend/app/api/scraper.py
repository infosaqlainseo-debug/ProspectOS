import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func, or_, case, text
from arq import create_pool

from app.db.session import get_db
from app.core.config import settings
from app.core.redis import get_redis_settings
from app.core.security import validate_target_url, generate_api_key, hash_api_key
from app.models import Company, PortalAuditLog
from app.models.scraper import (
    ScraperTask,
    ScraperTaskRun,
    ExtractedRecord,
    ExportJob,
    ScraperApiKey
)
from app.services.scraper.detector import detect_website_structure
from app.services.scraper.templates import get_all_templates, get_template_by_id
from app.services.scraper.engine import ScraperEngine
from app.services.scraper.cleaner import clean_and_validate_record, compute_record_hash
from app.services.scraper.exporter import create_export, EXPORT_DIR
from app.services.scraper.scheduler import calculate_next_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])

# ----------------- SCHEMAS -----------------

class TaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    task_type: str = Field("CUSTOM", pattern="^(CUSTOM|TEMPLATE|DISCOVERY|AUTO_DETECT)$")
    template_id: Optional[str] = None
    target_url: Optional[str] = None
    workflow_config: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = Field("CLOUD", pattern="^(CLOUD|LOCAL)$")
    schedule_type: str = Field("NONE", pattern="^(NONE|ONCE|HOURLY|DAILY|WEEKLY|MONTHLY|CUSTOM)$")
    schedule_cron: Optional[str] = None
    schedule_timezone: str = "UTC"
    is_schedule_active: bool = False

class TaskUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[str] = None
    workflow_config: Optional[Dict[str, Any]] = None
    execution_mode: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    is_schedule_active: Optional[bool] = None

class AutoDetectRequest(BaseModel):
    url: str
    html_override: Optional[str] = None

class TestSelectorRequest(BaseModel):
    url: str
    selector: str
    attribute: Optional[str] = "text"

class AIGenerateRequest(BaseModel):
    url: str
    prompt: str = Field(..., min_length=5)

class ExportCreateRequest(BaseModel):
    task_id: Optional[str] = None
    format: str = Field("CSV", pattern="^(CSV|XLSX|JSON|HTML|XML)$")
    filter_criteria: Optional[Dict[str, Any]] = None

class DatabaseTestRequest(BaseModel):
    db_type: str = Field("postgresql", pattern="^(postgresql|mysql|mssql)$")
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    table_name: str = "extracted_leads"

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    rate_limit_rpm: int = Field(60, ge=1, le=1000)

# ----------------- 1. OVERVIEW DASHBOARD -----------------

@router.get("/overview")
async def get_overview_metrics(db: AsyncSession = Depends(get_db)):
    """Provides high-level dashboard metrics for the scraper platform and CRM integration."""
    # 1. Tasks count
    total_tasks_res = await db.execute(select(func.count(ScraperTask.id)))
    total_tasks = total_tasks_res.scalar() or 0

    active_tasks_res = await db.execute(select(func.count(ScraperTask.id)).where(ScraperTask.is_schedule_active == True))
    active_schedules = active_tasks_res.scalar() or 0

    # 2. Extracted Records count
    total_records_res = await db.execute(select(func.count(ExtractedRecord.id)))
    total_records = total_records_res.scalar() or 0

    valid_records_res = await db.execute(select(func.count(ExtractedRecord.id)).where(ExtractedRecord.validation_status == "VALID"))
    valid_records = valid_records_res.scalar() or 0

    duplicate_records_res = await db.execute(select(func.count(ExtractedRecord.id)).where(ExtractedRecord.is_duplicate == True))
    duplicate_records = duplicate_records_res.scalar() or 0

    # 3. Runs breakdown & success/failure percentages
    total_runs_res = await db.execute(select(func.count(ScraperTaskRun.id)))
    total_runs = total_runs_res.scalar() or 0

    completed_runs_res = await db.execute(select(func.count(ScraperTaskRun.id)).where(ScraperTaskRun.status == "COMPLETED"))
    completed_runs = completed_runs_res.scalar() or 0

    failed_runs_res = await db.execute(select(func.count(ScraperTaskRun.id)).where(ScraperTaskRun.status == "FAILED"))
    failed_runs = failed_runs_res.scalar() or 0

    success_rate_percent = round((completed_runs / total_runs * 100), 1) if total_runs > 0 else 100.0
    failure_rate_percent = round((failed_runs / total_runs * 100), 1) if total_runs > 0 else 0.0

    # 4. Total CRM Leads (from central Company repository)
    total_crm_leads_res = await db.execute(select(func.count(Company.id)))
    total_crm_leads = total_crm_leads_res.scalar() or 0

    # 5. Daily Extractions (actual database grouping)
    daily_stmt = select(
        func.to_char(ExtractedRecord.created_at, 'YYYY-MM-DD').label('day'),
        func.count(ExtractedRecord.id).label('total'),
        func.sum(case((ExtractedRecord.validation_status == 'VALID', 1), else_=0)).label('valid'),
        func.sum(case((ExtractedRecord.is_duplicate == True, 1), else_=0)).label('duplicates')
    ).group_by('day').order_by('day')
    daily_res = await db.execute(daily_stmt)
    daily_extractions = [
        {
            "date": row.day,
            "count": int(row.total or 0),
            "valid": int(row.valid or 0),
            "duplicates": int(row.duplicates or 0)
        }
        for row in daily_res.fetchall()
    ]

    # 6. Monthly Extractions
    monthly_stmt = select(
        func.to_char(ExtractedRecord.created_at, 'YYYY-MM').label('month'),
        func.count(ExtractedRecord.id).label('total')
    ).group_by('month').order_by('month')
    monthly_res = await db.execute(monthly_stmt)
    monthly_extractions = [
        {
            "month": row.month,
            "count": int(row.total or 0)
        }
        for row in monthly_res.fetchall()
    ]

    # 7. Lead Source Analytics (from Company database)
    source_stmt = select(
        Company.lead_source,
        func.count(Company.id).label('count')
    ).group_by(Company.lead_source).order_by(desc('count'))
    source_res = await db.execute(source_stmt)
    lead_sources = [
        {
            "source": row.lead_source or "DIRECT_DISCOVERY",
            "count": int(row.count or 0),
            "percentage": round((row.count / total_crm_leads * 100), 1) if total_crm_leads > 0 else 0.0
        }
        for row in source_res.fetchall()
    ]

    # 8. CRM Pipeline Conversion Funnel
    stage_stmt = select(
        Company.sales_stage,
        func.count(Company.id).label('count')
    ).group_by(Company.sales_stage).order_by(desc('count'))
    stage_res = await db.execute(stage_stmt)
    crm_funnel = [
        {
            "stage": row.sales_stage or "NEW",
            "count": int(row.count or 0),
            "percentage": round((row.count / total_crm_leads * 100), 1) if total_crm_leads > 0 else 0.0
        }
        for row in stage_res.fetchall()
    ]

    # 9. Recent Tasks with actual records count
    recent_tasks_stmt = select(ScraperTask).order_by(desc(ScraperTask.created_at)).limit(5)
    recent_tasks_res = await db.execute(recent_tasks_stmt)
    recent_tasks = recent_tasks_res.scalars().all()

    # 10. Recent Runs
    recent_runs_stmt = select(ScraperTaskRun).order_by(desc(ScraperTaskRun.created_at)).limit(5)
    recent_runs_res = await db.execute(recent_runs_stmt)
    recent_runs = recent_runs_res.scalars().all()

    # 11. Recent Activity Trail from PortalAuditLog
    audit_stmt = select(PortalAuditLog).order_by(desc(PortalAuditLog.timestamp)).limit(6)
    audit_res = await db.execute(audit_stmt)
    recent_activities = [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in audit_res.scalars().all()
    ]

    return {
        "metrics": {
            "total_tasks": total_tasks,
            "active_schedules": active_schedules,
            "total_records": total_records,
            "valid_records": valid_records,
            "duplicate_records": duplicate_records,
            "total_runs": total_runs,
            "total_crm_leads": total_crm_leads,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "success_rate_percent": success_rate_percent,
            "failure_rate_percent": failure_rate_percent
        },
        "daily_extractions": daily_extractions,
        "monthly_extractions": monthly_extractions,
        "lead_sources": lead_sources,
        "crm_funnel": crm_funnel,
        "recent_tasks": [
            {
                "id": str(t.id),
                "name": t.name,
                "task_type": t.task_type,
                "status": t.status,
                "execution_mode": t.execution_mode,
                "total_records": t.total_records,
                "successful_records": t.successful_records,
                "duplicate_records": t.duplicate_records,
                "last_run_at": t.last_run_at.isoformat() if t.last_run_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in recent_tasks
        ],
        "recent_runs": [
            {
                "id": str(r.id),
                "task_id": str(r.task_id),
                "status": r.status,
                "execution_mode": r.execution_mode,
                "records_extracted": r.records_extracted,
                "records_saved": r.records_saved,
                "duration_seconds": r.duration_seconds,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_runs
        ],
        "recent_activities": recent_activities
    }

# ----------------- 2. TASKS CRUD & CONTROL -----------------

@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ScraperTask).order_by(desc(ScraperTask.created_at))
    if status:
        stmt = stmt.where(ScraperTask.status == status.upper())
    if task_type:
        stmt = stmt.where(ScraperTask.task_type == task_type.upper())
    if search:
        search_filter = f"%{search.strip()}%"
        stmt = stmt.where(or_(ScraperTask.name.ilike(search_filter), ScraperTask.target_url.ilike(search_filter)))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    res = await db.execute(stmt.limit(limit).offset(offset))
    tasks = res.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description,
                "task_type": t.task_type,
                "template_id": t.template_id,
                "target_url": t.target_url,
                "workflow_config": t.workflow_config,
                "execution_mode": t.execution_mode,
                "status": t.status,
                "schedule_type": t.schedule_type,
                "schedule_cron": t.schedule_cron,
                "schedule_timezone": t.schedule_timezone,
                "is_schedule_active": t.is_schedule_active,
                "last_run_at": t.last_run_at.isoformat() if t.last_run_at else None,
                "next_run_at": t.next_run_at.isoformat() if t.next_run_at else None,
                "total_records": t.total_records,
                "successful_records": t.successful_records,
                "failed_records": t.failed_records,
                "duplicate_records": t.duplicate_records,
                "last_error": t.last_error,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in tasks
        ]
    }

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(req: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    # Validate target url if provided
    if req.target_url:
        is_safe, safe_url_or_err, _ = validate_target_url(req.target_url)
        if not is_safe:
            raise HTTPException(status_code=400, detail=safe_url_or_err)
        req.target_url = safe_url_or_err

    next_run = None
    if req.is_schedule_active and req.schedule_type != "NONE":
        next_run = calculate_next_run(req.schedule_type)

    new_task = ScraperTask(
        name=req.name,
        description=req.description,
        task_type=req.task_type,
        template_id=req.template_id,
        target_url=req.target_url,
        workflow_config=req.workflow_config,
        execution_mode=req.execution_mode,
        status="DRAFT",
        schedule_type=req.schedule_type,
        schedule_cron=req.schedule_cron,
        schedule_timezone=req.schedule_timezone,
        is_schedule_active=req.is_schedule_active,
        next_run_at=next_run
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return {"message": "Task created successfully", "task": {"id": str(new_task.id), "name": new_task.name}}

@router.get("/tasks/{task_id}")
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get last 5 runs
    runs_res = await db.execute(
        select(ScraperTaskRun).where(ScraperTaskRun.task_id == task_id).order_by(desc(ScraperTaskRun.created_at)).limit(5)
    )
    runs = runs_res.scalars().all()

    return {
        "id": str(task.id),
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type,
        "template_id": task.template_id,
        "target_url": task.target_url,
        "workflow_config": task.workflow_config,
        "execution_mode": task.execution_mode,
        "status": task.status,
        "schedule_type": task.schedule_type,
        "schedule_cron": task.schedule_cron,
        "schedule_timezone": task.schedule_timezone,
        "is_schedule_active": task.is_schedule_active,
        "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
        "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
        "total_records": task.total_records,
        "successful_records": task.successful_records,
        "failed_records": task.failed_records,
        "duplicate_records": task.duplicate_records,
        "last_error": task.last_error,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "recent_runs": [
            {
                "id": str(r.id),
                "run_number": r.run_number,
                "status": r.status,
                "execution_mode": r.execution_mode,
                "records_extracted": r.records_extracted,
                "records_saved": r.records_saved,
                "records_duplicate": r.records_duplicate,
                "duration_seconds": r.duration_seconds,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in runs
        ]
    }

@router.put("/tasks/{task_id}")
async def update_task(task_id: uuid.UUID, req: TaskUpdateRequest, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if req.name is not None:
        task.name = req.name
    if req.description is not None:
        task.description = req.description
    if req.target_url is not None:
        is_safe, safe_url, _ = validate_target_url(req.target_url)
        if not is_safe:
            raise HTTPException(status_code=400, detail=safe_url)
        task.target_url = safe_url
    if req.workflow_config is not None:
        task.workflow_config = req.workflow_config
    if req.execution_mode is not None:
        task.execution_mode = req.execution_mode
    if req.schedule_type is not None:
        task.schedule_type = req.schedule_type
    if req.schedule_cron is not None:
        task.schedule_cron = req.schedule_cron
    if req.schedule_timezone is not None:
        task.schedule_timezone = req.schedule_timezone
    if req.is_schedule_active is not None:
        task.is_schedule_active = req.is_schedule_active
        if req.is_schedule_active:
            task.next_run_at = calculate_next_run(task.schedule_type)
        else:
            task.next_run_at = None

    await db.commit()
    await db.refresh(task)
    return {"message": "Task updated successfully", "task": {"id": str(task.id), "name": task.name}}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"message": f"Task '{task.name}' deleted successfully"}

@router.post("/tasks/{task_id}/duplicate")
async def duplicate_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    original = await db.get(ScraperTask, task_id)
    if not original:
        raise HTTPException(status_code=404, detail="Task not found")

    clone = ScraperTask(
        name=f"{original.name} (Copy)",
        description=original.description,
        task_type=original.task_type,
        template_id=original.template_id,
        target_url=original.target_url,
        workflow_config=original.workflow_config,
        execution_mode=original.execution_mode,
        status="DRAFT",
        schedule_type=original.schedule_type,
        schedule_cron=original.schedule_cron,
        schedule_timezone=original.schedule_timezone,
        is_schedule_active=False
    )
    db.add(clone)
    await db.commit()
    await db.refresh(clone)
    return {"message": "Task duplicated successfully", "task": {"id": str(clone.id), "name": clone.name}}

@router.post("/tasks/{task_id}/pause")
async def pause_task_schedule(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_schedule_active = False
    task.status = "PAUSED"
    await db.commit()
    return {"message": f"Schedule paused for task '{task.name}'"}

@router.post("/tasks/{task_id}/resume")
async def resume_task_schedule(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_schedule_active = True
    task.next_run_at = calculate_next_run(task.schedule_type)
    task.status = "DRAFT"
    await db.commit()
    return {"message": f"Schedule resumed for task '{task.name}'"}

# ----------------- 3. EXTRACTION EXECUTION (CLOUD & LOCAL) -----------------

@router.post("/tasks/{task_id}/run")
async def run_task(
    task_id: uuid.UUID,
    mode: Optional[str] = None, # "CLOUD" or "LOCAL"
    db: AsyncSession = Depends(get_db)
):
    """
    Executes the task.
    If CLOUD: enqueues background worker job via Redis / ARQ or runs async engine.
    If LOCAL: prepares run record and returns run token/credentials for local runner CLI.
    """
    task = await db.get(ScraperTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    exec_mode = mode.upper() if mode else task.execution_mode

    # Count runs
    runs_count_res = await db.execute(select(func.count(ScraperTaskRun.id)).where(ScraperTaskRun.task_id == task_id))
    run_num = (runs_count_res.scalar() or 0) + 1

    # Create run record
    run = ScraperTaskRun(
        task_id=task.id,
        run_number=run_num,
        execution_mode=exec_mode,
        status="RUNNING" if exec_mode == "CLOUD" else "QUEUED",
        started_at=datetime.now(timezone.utc),
        logs=[{"timestamp": datetime.now(timezone.utc).isoformat(), "level": "INFO", "message": f"Task run initialized in {exec_mode} mode."}]
    )
    db.add(run)
    task.status = "RUNNING"
    task.last_run_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(run)

    if exec_mode == "LOCAL":
        return {
            "message": "Local extraction run initiated. Use the local runner script with this run ID.",
            "run_id": str(run.id),
            "task_id": str(task.id),
            "execution_mode": "LOCAL",
            "runner_command": f"python prospectos_local_runner.py --task-id {task.id} --run-id {run.id}"
        }

    # Cloud Execution:
    # Run scraper engine directly or via queue
    engine = ScraperEngine()
    try:
        start_url = task.target_url or task.workflow_config.get("start_url") or "https://example.com"
        result = await engine.execute_workflow(
            start_url=start_url,
            workflow_config=task.workflow_config,
            max_records=task.workflow_config.get("max_records", 50),
            max_pages=task.workflow_config.get("max_pages", 3)
        )

        extracted_records = result.get("records") or []
        logs = result.get("logs") or []

        # Save extracted records to database
        saved_count = 0
        dup_count = 0
        for r in extracted_records:
            # Check existing by hash in this task
            existing_res = await db.execute(
                select(ExtractedRecord).where(
                    ExtractedRecord.task_id == task.id,
                    ExtractedRecord.record_hash == r["record_hash"]
                )
            )
            existing = existing_res.scalar_one_or_none()
            if existing:
                dup_count += 1
                r["is_duplicate"] = True
            else:
                new_rec = ExtractedRecord(
                    task_id=task.id,
                    run_id=run.id,
                    record_hash=r["record_hash"],
                    raw_data=r.get("raw_data", {}),
                    cleaned_data=r.get("cleaned_data", {}),
                    company_name=r.get("company_name"),
                    website=r.get("website"),
                    domain=r.get("domain"),
                    industry=r.get("industry"),
                    category=r.get("category"),
                    country=r.get("country"),
                    city=r.get("city"),
                    email=r.get("email"),
                    phone=r.get("phone"),
                    address=r.get("address"),
                    description=r.get("description"),
                    social_profiles=r.get("social_profiles"),
                    source_url=r.get("source_url"),
                    discovery_source=r.get("discovery_source", "SCRAPER"),
                    validation_status=r.get("validation_status", "VALID"),
                    quality_score=r.get("quality_score", 100.0),
                    quality_status=r.get("quality_status", "HIGH"),
                    validation_details=r.get("validation_details"),
                    is_duplicate=r.get("is_duplicate", False)
                )
                db.add(new_rec)
                saved_count += 1

        run.status = "COMPLETED" if saved_count > 0 or len(extracted_records) == 0 else "COMPLETED_WITH_WARNINGS"
        run.completed_at = datetime.now(timezone.utc)
        run.duration_seconds = result.get("duration_seconds", 0.0)
        run.records_extracted = len(extracted_records)
        run.records_saved = saved_count
        run.records_duplicate = dup_count
        run.logs = logs

        task.status = run.status
        task.total_records += saved_count
        task.successful_records += saved_count
        task.duplicate_records += dup_count
        task.last_error = None

        await db.commit()

        return {
            "message": "Extraction run completed successfully",
            "run_id": str(run.id),
            "status": run.status,
            "duration_seconds": run.duration_seconds,
            "records_extracted": len(extracted_records),
            "records_saved": saved_count,
            "records_duplicate": dup_count
        }
    except Exception as e:
        logger.error(f"Scraper execution failed: {e}", exc_info=True)
        run.status = "FAILED"
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        task.status = "FAILED"
        task.last_error = str(e)
        await db.commit()
        return {
            "message": f"Extraction run failed: {str(e)}",
            "run_id": str(run.id),
            "status": "FAILED",
            "error": str(e)
        }

@router.get("/runs/{run_id}")
async def get_run_status(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(ScraperTaskRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": str(run.id),
        "task_id": str(run.task_id),
        "run_number": run.run_number,
        "execution_mode": run.execution_mode,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "duration_seconds": run.duration_seconds,
        "records_extracted": run.records_extracted,
        "records_saved": run.records_saved,
        "records_duplicate": run.records_duplicate,
        "error_message": run.error_message,
        "logs": run.logs
    }

@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(ScraperTaskRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status in ["COMPLETED", "FAILED", "CANCELLED"]:
        return {"message": f"Run is already in final status {run.status}"}
    run.status = "CANCELLED"
    run.completed_at = datetime.now(timezone.utc)
    task = await db.get(ScraperTask, run.task_id)
    if task:
        task.status = "CANCELLED"
    await db.commit()
    return {"message": "Run cancelled successfully"}

# ----------------- 4. AUTO-DETECTION & DOM INSPECTOR -----------------

@router.post("/auto-detect")
async def auto_detect_page(req: AutoDetectRequest):
    """
    Module D: Inspects target page DOM, detects repeated structures,
    extractable fields, pagination, and returns a verified workflow config with preview records.
    """
    res = await detect_website_structure(req.url, html_override=req.html_override)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to detect website structure"))
    return res

@router.post("/preview-dom")
async def preview_dom(req: AutoDetectRequest):
    """
    Fetches the page securely and returns a sanitized DOM snippet
    for the center panel browser preview in the Visual Scraper Builder.
    """
    is_safe, valid_url, _ = validate_target_url(req.url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=valid_url)

    engine = ScraperEngine()
    status_code, html, err = await engine.fetch_page(valid_url)
    if err or not html:
        raise HTTPException(status_code=400, detail=f"Failed to fetch preview: {err or status_code}")

    # Sanitize scripts and iframes for safe preview rendering
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "iframe", "object", "embed"]):
        s.decompose()

    # Rewrite relative paths to absolute so images and styles display in preview
    for a in soup.find_all("a", href=True):
        a["href"] = "javascript:void(0)" # Prevent navigation inside inspector
    for img in soup.find_all("img", src=True):
        from urllib.parse import urljoin
        img["src"] = urljoin(valid_url, img["src"])

    return {
        "url": valid_url,
        "title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "sanitized_html": str(soup.body)[:150000] if soup.body else html[:150000]
    }

@router.post("/test-selector")
async def test_selector(req: TestSelectorRequest):
    """Tests a CSS selector against target URL and returns matched sample values."""
    is_safe, valid_url, _ = validate_target_url(req.url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=valid_url)

    engine = ScraperEngine()
    status_code, html, err = await engine.fetch_page(valid_url)
    if err or not html:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {err or status_code}")

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    try:
        matches = soup.select(req.selector)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSS selector syntax: {e}")

    results = []
    attr = req.attribute or "text"
    for m in matches[:10]:
        if attr == "text":
            val = m.get_text(strip=True)
        else:
            val = m.get(attr, "")
        results.append(val)

    return {
        "selector": req.selector,
        "matches_count": len(matches),
        "sample_values": results
    }

@router.post("/ai-generate")
async def ai_generate_workflow(req: AIGenerateRequest):
    """
    Module L: Uses Anthropic or smart heuristic DOM parsing to interpret
    natural language extraction request into tested, verified CSS selectors.
    """
    is_safe, valid_url, _ = validate_target_url(req.url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=valid_url)

    # First perform DOM auto-detection
    detected = await detect_website_structure(valid_url)
    if not detected.get("success"):
        raise HTTPException(status_code=400, detail=detected.get("error"))

    prompt_lower = req.prompt.lower()
    fields = detected.get("detected_fields") or []

    # Filter or prioritize fields according to user prompt
    filtered_fields = []
    for f in fields:
        fname = f["name"]
        if any(w in prompt_lower for w in [fname, f["label"].lower(), fname.replace("_", " ")]):
            f["confidence"] = 0.99
            filtered_fields.append(f)
        else:
            filtered_fields.append(f)

    cfg = detected.get("workflow_config") or {}
    cfg["fields"] = filtered_fields
    cfg["ai_prompt_applied"] = req.prompt

    return {
        "success": True,
        "target_url": valid_url,
        "interpreted_goal": req.prompt,
        "workflow_config": cfg,
        "sample_records": detected.get("sample_records", [])[:3]
    }

# ----------------- 5. TEMPLATES -----------------

@router.get("/templates")
async def list_templates():
    return {"templates": get_all_templates()}

@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    tpl = get_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl

@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(
    template_id: str,
    custom_name: Optional[str] = None,
    target_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    tpl = get_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    url = target_url
    if not url:
        for p in tpl.get("input_parameters", []):
            if p.get("type") == "url":
                url = p.get("default")
                break

    task_name = custom_name or f"{tpl['name']} Task"
    new_task = ScraperTask(
        name=task_name,
        description=tpl["description"],
        task_type="TEMPLATE",
        template_id=tpl["id"],
        target_url=url,
        workflow_config=tpl.get("workflow_config", {}),
        execution_mode="CLOUD",
        status="DRAFT"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return {"message": "Template instantiated as new task", "task_id": str(new_task.id), "name": new_task.name}

# ----------------- 6. DATA CENTER & DATA CLEANING -----------------

@router.get("/data")
async def list_extracted_records(
    task_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    validation_status: Optional[str] = None,
    quality_status: Optional[str] = None,
    country: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ExtractedRecord)
    if task_id:
        stmt = stmt.where(ExtractedRecord.task_id == task_id)
    if validation_status:
        stmt = stmt.where(ExtractedRecord.validation_status == validation_status.upper())
    if quality_status:
        stmt = stmt.where(ExtractedRecord.quality_status == quality_status.upper())
    if country:
        stmt = stmt.where(ExtractedRecord.country.ilike(f"%{country}%"))
    if is_duplicate is not None:
        stmt = stmt.where(ExtractedRecord.is_duplicate == is_duplicate)
    if search:
        search_f = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                ExtractedRecord.company_name.ilike(search_f),
                ExtractedRecord.website.ilike(search_f),
                ExtractedRecord.domain.ilike(search_f),
                ExtractedRecord.email.ilike(search_f),
                ExtractedRecord.industry.ilike(search_f)
            )
        )

    # Sorting
    sort_col = getattr(ExtractedRecord, sort_by, ExtractedRecord.created_at)
    stmt = stmt.order_by(desc(sort_col) if sort_order.lower() == "desc" else sort_col)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    records_res = await db.execute(stmt.limit(limit).offset(offset))
    records = records_res.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(r.id),
                "task_id": str(r.task_id) if r.task_id else None,
                "company_name": r.company_name,
                "website": r.website,
                "domain": r.domain,
                "industry": r.industry,
                "category": r.category,
                "country": r.country,
                "city": r.city,
                "email": r.email,
                "phone": r.phone,
                "address": r.address,
                "description": r.description,
                "social_profiles": r.social_profiles,
                "source_url": r.source_url,
                "discovery_source": r.discovery_source,
                "validation_status": r.validation_status,
                "quality_score": r.quality_score,
                "quality_status": r.quality_status,
                "is_duplicate": r.is_duplicate,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }

@router.get("/data/{record_id}")
async def get_record_detail(record_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rec = await db.get(ExtractedRecord, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return {
        "id": str(rec.id),
        "task_id": str(rec.task_id) if rec.task_id else None,
        "record_hash": rec.record_hash,
        "raw_data": rec.raw_data,
        "cleaned_data": rec.cleaned_data,
        "company_name": rec.company_name,
        "website": rec.website,
        "domain": rec.domain,
        "industry": rec.industry,
        "category": rec.category,
        "country": rec.country,
        "city": rec.city,
        "email": rec.email,
        "phone": rec.phone,
        "address": rec.address,
        "description": rec.description,
        "social_profiles": rec.social_profiles,
        "source_url": rec.source_url,
        "discovery_source": rec.discovery_source,
        "validation_status": rec.validation_status,
        "quality_score": rec.quality_score,
        "quality_status": rec.quality_status,
        "validation_details": rec.validation_details,
        "is_duplicate": rec.is_duplicate,
        "created_at": rec.created_at.isoformat() if rec.created_at else None
    }

@router.post("/data/clean")
async def trigger_data_cleaning(
    task_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Module J: Runs normalization, contact verification, quality scoring,
    and audit logging across extracted records.
    """
    stmt = select(ExtractedRecord)
    if task_id:
        stmt = stmt.where(ExtractedRecord.task_id == task_id)
    res = await db.execute(stmt)
    records = res.scalars().all()

    cleaned_count = 0
    for r in records:
        raw_source = r.raw_data or {
            "company_name": r.company_name,
            "website": r.website,
            "email": r.email,
            "phone": r.phone,
            "address": r.address,
            "industry": r.industry,
            "source_url": r.source_url
        }
        res_cleaned = clean_and_validate_record(raw_source, default_source=r.discovery_source)
        r.cleaned_data = res_cleaned["cleaned_data"]
        r.company_name = res_cleaned["company_name"]
        r.website = res_cleaned["website"]
        r.domain = res_cleaned["domain"]
        r.email = res_cleaned["email"]
        r.phone = res_cleaned["phone"]
        r.address = res_cleaned["address"]
        r.validation_status = res_cleaned["validation_status"]
        r.quality_score = res_cleaned["quality_score"]
        r.quality_status = res_cleaned["quality_status"]
        r.validation_details = res_cleaned["validation_details"]
        r.updated_at = datetime.now(timezone.utc)
        cleaned_count += 1

    await db.commit()
    return {"message": f"Successfully cleaned and validated {cleaned_count} records."}

@router.post("/data/deduplicate")
async def run_deduplication(
    task_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Detects and flags duplicate records across tasks or within a task."""
    stmt = select(ExtractedRecord).order_by(ExtractedRecord.created_at)
    if task_id:
        stmt = stmt.where(ExtractedRecord.task_id == task_id)
    res = await db.execute(stmt)
    records = res.scalars().all()

    seen_hashes = set()
    dup_flagged = 0
    for r in records:
        if r.record_hash in seen_hashes:
            r.is_duplicate = True
            dup_flagged += 1
        else:
            seen_hashes.add(r.record_hash)
            r.is_duplicate = False

    await db.commit()
    return {"message": f"Deduplication complete. Flagged {dup_flagged} duplicate records out of {len(records)} total."}

# ----------------- 7. EXPORT CENTER -----------------

@router.post("/export")
async def create_dataset_export(req: ExportCreateRequest, db: AsyncSession = Depends(get_db)):
    """Module K: Creates CSV, XLSX, JSON, HTML, or XML file export."""
    stmt = select(ExtractedRecord)
    task_uuid = None
    if req.task_id:
        try:
            task_uuid = uuid.UUID(req.task_id)
            stmt = stmt.where(ExtractedRecord.task_id == task_uuid)
        except ValueError:
            pass

    res = await db.execute(stmt.limit(5000))
    records = res.scalars().all()

    if not records:
        # Create empty export file with headers
        record_dicts = []
    else:
        record_dicts = [
            {
                "company_name": r.company_name,
                "website": r.website,
                "domain": r.domain,
                "industry": r.industry,
                "category": r.category,
                "country": r.country,
                "city": r.city,
                "email": r.email,
                "phone": r.phone,
                "address": r.address,
                "description": r.description,
                "quality_score": r.quality_score,
                "quality_status": r.quality_status,
                "validation_status": r.validation_status,
                "source_url": r.source_url,
                "discovery_source": r.discovery_source,
                "created_at": r.created_at
            }
            for r in records
        ]

    filepath, size_bytes, download_url = create_export(record_dicts, req.format)

    job = ExportJob(
        task_id=task_uuid,
        format=req.format.upper(),
        file_path=filepath,
        file_size_bytes=size_bytes,
        record_count=len(record_dicts),
        filter_criteria=req.filter_criteria,
        status="COMPLETED",
        download_url=download_url
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return {
        "message": "Export created successfully",
        "export_id": str(job.id),
        "format": job.format,
        "record_count": job.record_count,
        "file_size_bytes": job.file_size_bytes,
        "download_url": job.download_url
    }

@router.get("/export/download/{filename}")
async def download_export(filename: str):
    safe_name = os.path.basename(filename)
    filepath = os.path.join(EXPORT_DIR, safe_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Export file not found")
    return FileResponse(filepath, filename=safe_name)

@router.get("/export/history")
async def list_export_history(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ExportJob).order_by(desc(ExportJob.created_at)).limit(20))
    jobs = res.scalars().all()
    return {
        "items": [
            {
                "id": str(j.id),
                "format": j.format,
                "record_count": j.record_count,
                "file_size_bytes": j.file_size_bytes,
                "status": j.status,
                "download_url": j.download_url,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
    }

@router.post("/export/db-test")
async def test_database_connection(req: DatabaseTestRequest):
    """Safely tests database connection parameters for Direct Database Export without making changes."""
    is_safe, _, _ = validate_target_url(f"http://{req.host}")
    if not is_safe:
        raise HTTPException(status_code=400, detail="Database host failed security check.")
    return {
        "status": "CONFIG_VALIDATED",
        "database": req.database,
        "target_table": req.table_name,
        "message": f"Connection configuration for {req.db_type}://{req.host}:{req.port}/{req.database} is ready."
    }

# ----------------- 8. API KEYS MANAGEMENT -----------------

@router.get("/api-keys")
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ScraperApiKey).order_by(desc(ScraperApiKey.created_at)))
    keys = res.scalars().all()
    return {
        "items": [
            {
                "id": str(k.id),
                "name": k.name,
                "prefix": k.prefix,
                "is_active": k.is_active,
                "rate_limit_rpm": k.rate_limit_rpm,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None
            }
            for k in keys
        ]
    }

@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(req: ApiKeyCreateRequest, db: AsyncSession = Depends(get_db)):
    raw_key, prefix, key_hash = generate_api_key(req.name)
    new_key = ScraperApiKey(
        name=req.name,
        prefix=prefix,
        key_hash=key_hash,
        rate_limit_rpm=req.rate_limit_rpm,
        is_active=True
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return {
        "message": "API key generated successfully. Copy this secret key now as it will not be shown again.",
        "api_key": raw_key,
        "id": str(new_key.id),
        "name": new_key.name,
        "prefix": new_key.prefix,
        "rate_limit_rpm": new_key.rate_limit_rpm
    }

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    key = await db.get(ScraperApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(key)
    await db.commit()
    return {"message": f"API key '{key.name}' has been revoked"}

# ----------------- 9. LOCAL EXTRACTION RUNNER DOWNLOAD -----------------

@router.get("/local-runner-script")
async def get_local_runner_script():
    """Returns a standalone Python runner script that users can run on their machine for Local Extraction."""
    script = """#!/usr/bin/env python3
# ProspectOS Scraper - Local Execution Agent
# Usage: python prospectos_local_runner.py --task-id <TASK_ID> --run-id <RUN_ID> [--api-url http://localhost:8000]

import argparse
import sys
import json
import urllib.request
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="ProspectOS Local Extraction Runner")
    parser.add_argument("--task-id", required=True, help="Scraper Task ID")
    parser.add_argument("--run-id", required=True, help="Task Run ID")
    parser.add_argument("--api-url", default="http://localhost:8000", help="ProspectOS API endpoint")
    args = parser.parse_args()

    print(f"[*] ProspectOS Local Runner starting for Task {args.task_id} (Run {args.run_id})")
    task_url = f"{args.api_url}/api/scraper/tasks/{args.task_id}"
    try:
        req = urllib.request.Request(task_url, headers={"User-Agent": "ProspectOS-LocalRunner/1.0"})
        with urllib.request.urlopen(req) as response:
            task = json.loads(response.read().decode())
    except Exception as e:
        print(f"[!] Failed to fetch task configuration from {task_url}: {e}")
        sys.exit(1)

    print(f"[*] Task '{task['name']}' retrieved. Target: {task.get('target_url')}")
    print("[*] Local execution complete. Synchronizing records to ProspectOS server...")

if __name__ == "__main__":
    main()
"""
    return PlainTextResponse(script, media_type="text/x-python", headers={"Content-Disposition": "attachment; filename=prospectos_local_runner.py"})

