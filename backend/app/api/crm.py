import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.db.session import get_db
from app.models import Company, CRMDeal, CRMTask, CRMNote, CRMActivity, OpportunityProfile
from app.schemas.crm import (
    VALID_SALES_STAGES,
    StageUpdateRequest,
    DealCreate,
    DealUpdate,
    DealResponse,
    TaskCreate,
    TaskUpdate,
    TaskCompleteRequest,
    TaskResponse,
    NoteCreate,
    NoteResponse,
    ActivityResponse,
    UnifiedProspectSummary,
    UnifiedProspectDetail,
    PipelineColumn,
    CRMReportMetrics
)
from app.services.crm.service import CRMService

router = APIRouter(prefix="/crm", tags=["crm"])


# =========================================================================
# 1. Pipeline & Prospect Views
# =========================================================================

@router.get("/pipeline/board", response_model=List[PipelineColumn])
async def get_pipeline_board(db: AsyncSession = Depends(get_db)):
    """Returns the complete 11-stage Kanban pipeline board with summary metrics."""
    service = CRMService(db)
    return await service.get_pipeline_board()


@router.get("/prospects")
async def list_crm_prospects(
    stage: Optional[str] = Query(None, description="Filter by sales stage"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    q: Optional[str] = Query(None, description="Search term for company name or domain"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|company_name|stage_updated_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Paginated, searchable, and filterable CRM prospect directory."""
    stmt = select(Company)

    if stage:
        stmt = stmt.where(Company.sales_stage == stage.upper())
    if industry:
        stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
    if q:
        stmt = stmt.where(
            or_(
                Company.company_name.ilike(f"%{q}%"),
                Company.canonical_domain.ilike(f"%{q}%")
            )
        )

    # Count total matching
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sorting
    sort_col = getattr(Company, sort_by)
    if sort_dir == "desc":
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    companies = (await db.execute(stmt)).scalars().all()

    items = []
    for c in companies:
        stmt_opp = select(OpportunityProfile.opportunity_score, OpportunityProfile.recommended_service).where(
            OpportunityProfile.company_id == c.id
        ).order_by(desc(OpportunityProfile.created_at)).limit(1)
        opp_row = (await db.execute(stmt_opp)).first()

        stmt_d = select(func.count(CRMDeal.id), func.coalesce(func.sum(CRMDeal.estimated_value), 0.0)).where(
            CRMDeal.company_id == c.id,
            CRMDeal.stage.notin_(["WON", "LOST"])
        )
        d_row = (await db.execute(stmt_d)).first()

        items.append(
            UnifiedProspectSummary(
                id=c.id,
                company_name=c.company_name or c.canonical_domain or "Unnamed Prospect",
                canonical_domain=c.canonical_domain,
                website_url=c.website_url,
                industry=c.industry,
                target_market=c.target_market,
                sales_stage=c.sales_stage or "NEW",
                stage_updated_at=c.stage_updated_at or c.created_at,
                stage_reason=c.stage_reason,
                opportunity_score=c.lead_score or (opp_row[0] if opp_row else None),
                recommended_service=(c.recommended_services[0] if c.recommended_services else None) or (opp_row[1] if opp_row else None),
                total_deals=d_row[0] if d_row else 0,
                open_deal_value=float(d_row[1]) if d_row else 0.0,
                created_at=c.created_at,
                country=c.country,
                city=c.city,
                public_email=c.public_email,
                phone_number=c.phone_number,
                facebook_url=c.facebook_url,
                instagram_url=c.instagram_url,
                whatsapp_number=c.whatsapp_number,
                whatsapp_click_url=c.whatsapp_click_url,
                gdrive_file_id=c.gdrive_file_id,
                gdrive_file_url=c.gdrive_file_url,
                gdrive_sync_status=c.gdrive_sync_status or "NOT_SYNCED",
                lead_priority=c.lead_priority or "MEDIUM",
                lead_score=c.lead_score,
                lead_score_components=c.lead_score_components,
                recommended_services=c.recommended_services,
                seo_summary_findings=c.seo_summary_findings,
                lead_owner=c.lead_owner
            )
        )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/prospects/{company_id}", response_model=UnifiedProspectDetail)
async def get_prospect_detail(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Unified prospect record linking intelligence, contacts, outreach, deals, tasks, notes, and activity timeline."""
    service = CRMService(db)
    try:
        return await service.get_unified_prospect_detail(company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/prospects/{company_id}/stage")
async def update_prospect_stage(
    company_id: uuid.UUID,
    req: StageUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Moves a prospect between sales pipeline stages with audit logging."""
    service = CRMService(db)
    try:
        updated = await service.update_prospect_stage(
            company_id=company_id,
            new_stage=req.new_stage,
            reason=req.reason,
            notes=req.notes,
            actor=req.actor or "human_reviewer"
        )
        return {
            "success": True,
            "company_id": str(updated.id),
            "new_stage": updated.sales_stage,
            "stage_updated_at": updated.stage_updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 2. Deals Management
# =========================================================================

@router.get("/deals", response_model=List[DealResponse])
async def list_deals(
    company_id: Optional[uuid.UUID] = None,
    stage: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMDeal)
    if company_id:
        stmt = stmt.where(CRMDeal.company_id == company_id)
    if stage:
        stmt = stmt.where(CRMDeal.stage == stage.upper())
    stmt = stmt.order_by(desc(CRMDeal.created_at))
    deals = (await db.execute(stmt)).scalars().all()
    return deals


@router.post("/deals", response_model=DealResponse)
async def create_deal(
    data: DealCreate,
    actor: str = Query("human_reviewer"),
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        deal = await service.create_deal(data, actor=actor)
        return deal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    deal = await db.get(CRMDeal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.put("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.update_deal(deal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 3. Tasks Management
# =========================================================================

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    company_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    overdue_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMTask)
    if company_id:
        stmt = stmt.where(CRMTask.company_id == company_id)
    if status:
        stmt = stmt.where(CRMTask.status == status.upper())
    if priority:
        stmt = stmt.where(CRMTask.priority == priority.upper())
    if task_type:
        stmt = stmt.where(CRMTask.task_type == task_type.upper())
    if overdue_only:
        stmt = stmt.where(
            CRMTask.status.in_(["PENDING", "IN_PROGRESS"]),
            CRMTask.due_date < func.now()
        )
    stmt = stmt.order_by(CRMTask.due_date.asc().nulls_last(), desc(CRMTask.created_at))
    tasks = (await db.execute(stmt)).scalars().all()
    return tasks


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    actor: str = Query("human_reviewer"),
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.create_task(data, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: uuid.UUID,
    req: TaskCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.complete_task(task_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 4. Notes & Activities
# =========================================================================

@router.post("/prospects/{company_id}/notes", response_model=NoteResponse)
async def add_prospect_note(
    company_id: uuid.UUID,
    req: NoteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.add_note(company_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prospects/{company_id}/activities", response_model=List[ActivityResponse])
async def list_prospect_activities(
    company_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMActivity).where(CRMActivity.company_id == company_id).order_by(desc(CRMActivity.created_at)).limit(limit)
    activities = (await db.execute(stmt)).scalars().all()
    return activities


# =========================================================================
# 5. Reporting & Analytics
# =========================================================================

@router.get("/reports/metrics", response_model=CRMReportMetrics)
async def get_crm_report_metrics(db: AsyncSession = Depends(get_db)):
    """Aggregates sales pipeline metrics, revenue, conversion rates, and audit data."""
    service = CRMService(db)
    return await service.get_crm_metrics()
