import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.intelligence.sales_intelligence import SalesIntelligenceService
from app.schemas.sales_intelligence import (
    SalesIntelligenceScoreResponse,
    OpportunityItemResponse,
    SalesBriefResponse,
    SalesBriefUpdateRequest,
    ScoreOverrideRequest,
    ReviewStatusUpdateRequest,
    PrioritizedQueueResponse,
    ProspectComparisonResponse,
    BatchEvaluationRequest
)

router = APIRouter(prefix="/sales-intelligence", tags=["Sales Intelligence & Lead Prioritization"])


# =========================================================================
# 1. Prioritized Sales Queue
# =========================================================================

@router.get("/queue", response_model=PrioritizedQueueResponse)
async def get_prioritized_sales_queue(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    primary_service: Optional[str] = Query(None, description="Filter by recommended GrokxSEO service"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum priority score"),
    review_status: Optional[str] = Query(None, description="UNREVIEWED, IN_REVIEW, QUALIFIED, REJECTED"),
    sales_stage: Optional[str] = Query(None, description="Filter by CRM sales stage"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the prioritized sales queue ordered by explainable priority score descending.
    """
    service = SalesIntelligenceService(db)
    total, items = await service.get_prioritized_queue(
        industry=industry,
        primary_service=primary_service,
        min_score=min_score,
        review_status=review_status,
        sales_stage=sales_stage,
        limit=limit,
        offset=offset
    )
    return PrioritizedQueueResponse(total=total, limit=limit, offset=offset, items=items)


# =========================================================================
# 2. Prospect Evaluation & Score
# =========================================================================

@router.get("/prospects/{company_id}/score", response_model=SalesIntelligenceScoreResponse)
async def get_prospect_sales_score(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns the explainable priority score, weights, positive indicators, and limitations.
    Calculates score if not yet evaluated.
    """
    service = SalesIntelligenceService(db)
    try:
        score = await service.calculate_priority_score(company_id)
        return SalesIntelligenceScoreResponse.model_validate(score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/prospects/{company_id}/evaluate", response_model=SalesIntelligenceScoreResponse)
async def evaluate_prospect(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Forces full re-evaluation of SEO opportunities, service fits, and priority score.
    """
    service = SalesIntelligenceService(db)
    try:
        score = await service.calculate_priority_score(company_id)
        return SalesIntelligenceScoreResponse.model_validate(score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 3. Granular SEO Opportunities
# =========================================================================

@router.get("/prospects/{company_id}/opportunities", response_model=List[OpportunityItemResponse])
async def get_prospect_opportunities(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns granular SEO opportunities classified by category, severity, and supporting evidence.
    """
    service = SalesIntelligenceService(db)
    try:
        opps = await service.detect_opportunities(company_id)
        return [OpportunityItemResponse.model_validate(o) for o in opps]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 4. Sales Intelligence Briefs
# =========================================================================

@router.get("/prospects/{company_id}/brief", response_model=SalesBriefResponse)
async def get_sales_brief(
    company_id: uuid.UUID,
    force_regenerate: bool = Query(False, description="Regenerate brief ignoring custom edits"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the structured Sales Intelligence Brief including company overview,
    top opportunities, service fits, discovery questions, and full Markdown text.
    """
    service = SalesIntelligenceService(db)
    try:
        brief = await service.generate_or_get_brief(company_id, force_regenerate=force_regenerate)
        return SalesBriefResponse.model_validate(brief)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/prospects/{company_id}/brief", response_model=SalesBriefResponse)
async def update_sales_brief(
    company_id: uuid.UUID,
    req: SalesBriefUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Saves reviewer revisions and custom edits to the Sales Intelligence Brief.
    """
    service = SalesIntelligenceService(db)
    try:
        brief = await service.generate_or_get_brief(company_id)
        brief.full_brief_markdown = req.full_brief_markdown
        if req.title:
            brief.title = req.title
        brief.is_customized = True
        brief.last_edited_by = req.editor or "human_reviewer"
        brief.last_edited_at = service._get_utc_now()
        brief.updated_at = service._get_utc_now()
        await db.commit()
        await db.refresh(brief)
        return SalesBriefResponse.model_validate(brief)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prospects/{company_id}/brief/export")
async def export_sales_brief_markdown(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Exports the Sales Intelligence Brief as a downloadable plain text/Markdown document.
    """
    service = SalesIntelligenceService(db)
    try:
        brief = await service.generate_or_get_brief(company_id)
        filename = f"sales_brief_{company_id}.md"
        return PlainTextResponse(
            content=brief.full_brief_markdown,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 5. Human Overrides & Review Status
# =========================================================================

@router.post("/prospects/{company_id}/override", response_model=SalesIntelligenceScoreResponse)
async def override_prospect_score(
    company_id: uuid.UUID,
    req: ScoreOverrideRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Records a human override for priority score with mandatory reason and CRM activity audit log.
    """
    service = SalesIntelligenceService(db)
    try:
        updated_score = await service.override_score(
            company_id=company_id,
            score=req.score,
            reason=req.reason,
            actor=req.actor or "human_reviewer"
        )
        return SalesIntelligenceScoreResponse.model_validate(updated_score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/prospects/{company_id}/review-status", response_model=SalesIntelligenceScoreResponse)
async def update_lead_review_status(
    company_id: uuid.UUID,
    req: ReviewStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the lead review status (UNREVIEWED, IN_REVIEW, QUALIFIED, REJECTED) with CRM activity logging.
    """
    service = SalesIntelligenceService(db)
    try:
        updated_score = await service.update_review_status(
            company_id=company_id,
            status=req.review_status,
            notes=req.notes,
            actor=req.actor or "human_reviewer"
        )
        return SalesIntelligenceScoreResponse.model_validate(updated_score)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 6. Side-by-Side Prospect Comparison
# =========================================================================

@router.post("/compare", response_model=ProspectComparisonResponse)
async def compare_prospects(
    company_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db)
):
    """
    Compares 2 to 5 prospects side-by-side on opportunities, GrokxSEO service fits,
    priority scores, and matched publishers.
    """
    if len(company_ids) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 company IDs for comparison")
    if len(company_ids) > 5:
        raise HTTPException(status_code=400, detail="Cannot compare more than 5 prospects simultaneously")

    service = SalesIntelligenceService(db)
    return await service.compare_prospects(company_ids)


# =========================================================================
# 7. Batch Evaluation
# =========================================================================

@router.post("/batch/evaluate")
async def evaluate_batch_prospects(
    req: BatchEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Runs sales intelligence evaluation on a batch of prospects.
    """
    service = SalesIntelligenceService(db)
    evaluated_count = 0

    if req.company_ids:
        target_ids = req.company_ids
    else:
        # Evaluate top 20 prospects by default
        from app.models import Company
        from sqlalchemy import select
        res = await db.execute(select(Company.id).limit(20))
        target_ids = res.scalars().all()

    for cid in target_ids:
        try:
            await service.calculate_priority_score(cid)
            evaluated_count += 1
        except Exception as e:
            continue

    return {
        "status": "COMPLETED",
        "evaluated_count": evaluated_count,
        "total_requested": len(target_ids)
    }
