import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Company, CompanyCompetitor, CompetitiveAnalysisRun
from app.services.intelligence.competitive_service import CompetitiveIntelligenceService
from app.schemas.competitive import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorCandidate,
    ContentGapItem,
    TechnicalGapItem,
    InternalLinkingGapItem,
    BacklinkGapSummary,
    PublisherPROpportunityItem,
    CompetitiveRecommendation,
    RunAnalysisRequest,
    CompetitiveAnalysisRunResponse,
    CompetitiveOverviewResponse
)

router = APIRouter(prefix="/competitive", tags=["Advanced Competitive SEO Intelligence"])


async def _format_run_response(session: AsyncSession, run: CompetitiveAnalysisRun) -> CompetitiveAnalysisRunResponse:
    """Helper to convert a CompetitiveAnalysisRun ORM model into a validated Pydantic response."""
    prospect = await session.get(Company, run.company_id)
    competitor = await session.get(CompanyCompetitor, run.competitor_id)

    p_name = prospect.company_name if prospect else "Prospect"
    p_dom = prospect.canonical_domain if prospect else ""
    c_name = competitor.competitor_name if competitor else "Competitor"
    c_dom = competitor.competitor_domain if competitor else "domain.com"

    return CompetitiveAnalysisRunResponse(
        id=run.id,
        company_id=run.company_id,
        company_name=p_name,
        competitor_id=run.competitor_id,
        competitor_name=c_name,
        competitor_domain=c_dom,
        status=run.status,
        prospect_scan_available=run.prospect_scan_id is not None,
        competitor_scan_available=run.competitor_scan_id is not None,
        summary_findings=run.summary_findings or {},
        content_gaps=[ContentGapItem(**g) for g in (run.content_gaps or [])],
        technical_gaps=[TechnicalGapItem(**g) for g in (run.technical_gaps or [])],
        internal_linking_gaps=[InternalLinkingGapItem(**g) for g in (run.internal_linking_gaps or [])],
        backlink_gaps=BacklinkGapSummary(**(run.backlink_gaps or {
            "prospect_domain": p_dom,
            "competitor_domain": c_dom,
            "provider_source": "None",
            "is_provider_configured": False
        })),
        publisher_opportunities=[PublisherPROpportunityItem(**p) for p in (run.publisher_opportunities or [])],
        prioritized_recommendations=[CompetitiveRecommendation(**r) for r in (run.prioritized_recommendations or [])],
        data_limitations=run.data_limitations or [],
        analyzed_at=run.analyzed_at,
        created_at=run.created_at
    )


# =========================================================================
# 1. Competitor Discovery & Management Endpoints
# =========================================================================

@router.post("/companies/{company_id}/discover", response_model=List[CompetitorCandidate])
async def discover_competitors(
    company_id: uuid.UUID,
    max_results: int = Query(5, ge=1, le=20),
    persist: bool = Query(False, description="Persist discovered candidates as UNVERIFIED competitors"),
    db: AsyncSession = Depends(get_db)
):
    """
    Discovers relevant competitors from actual database records based on
    industry alignment, sub-industry categorization, and keyword token overlap.
    Zero fabricated competitor identities or arbitrary metrics.
    """
    service = CompetitiveIntelligenceService(db)
    try:
        candidates = await service.discover_competitors(
            company_id=company_id,
            max_results=max_results,
            persist_discovered=persist
        )
        return candidates
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/companies/{company_id}/competitors", response_model=List[CompetitorResponse])
async def list_company_competitors(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all actively tracked competitor relationships for the prospect company.
    """
    service = CompetitiveIntelligenceService(db)
    competitors = await service.get_competitors(company_id)
    return [CompetitorResponse.model_validate(c) for c in competitors]


@router.post("/companies/{company_id}/competitors", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def add_company_competitor(
    company_id: uuid.UUID,
    data: CompetitorCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Adds a new tracked competitor for a prospect company.
    """
    service = CompetitiveIntelligenceService(db)
    try:
        competitor = await service.add_competitor(company_id=company_id, data=data)
        return CompetitorResponse.model_validate(competitor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def update_company_competitor(
    competitor_id: uuid.UUID,
    data: CompetitorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates a competitor relationship (relevance score, tier, validation status, notes).
    """
    service = CompetitiveIntelligenceService(db)
    try:
        competitor = await service.update_competitor(competitor_id=competitor_id, data=data)
        return CompetitorResponse.model_validate(competitor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# 2. Competitive Intelligence Analysis Run Endpoints
# =========================================================================

@router.post("/companies/{company_id}/analyze", response_model=CompetitiveAnalysisRunResponse)
async def run_competitive_analysis(
    company_id: uuid.UUID,
    req: RunAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes an on-demand, multi-dimensional competitive SEO intelligence analysis
    against a tracked competitor or newly specified competitor domain.
    """
    service = CompetitiveIntelligenceService(db)
    competitor_id = req.competitor_id

    # If domain provided instead of competitor_id, resolve or create competitor
    if not competitor_id:
        if not req.competitor_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either competitor_id or competitor_domain must be provided"
            )
        create_data = CompetitorCreate(
            company_id=company_id,
            competitor_name=req.competitor_domain.split(".")[0].capitalize(),
            competitor_domain=req.competitor_domain,
            relevance_tier="DIRECT",
            discovery_method="MANUAL"
        )
        try:
            comp_rec = await service.add_competitor(company_id=company_id, data=create_data)
            competitor_id = comp_rec.id
        except Exception as e:
            # If exists, find it
            existing = await service.get_competitors(company_id)
            match = next((c for c in existing if c.competitor_domain.lower() == req.competitor_domain.lower()), None)
            if match:
                competitor_id = match.id
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        run = await service.run_competitive_analysis(
            company_id=company_id,
            competitor_id=competitor_id,
            sync_to_sales_opportunities=req.sync_to_sales_opportunities
        )
        return await _format_run_response(db, run)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {str(e)}")


@router.get("/companies/{company_id}/runs", response_model=List[CompetitiveAnalysisRunResponse])
async def list_competitive_analysis_runs(
    company_id: uuid.UUID,
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists historical competitive analysis runs for a prospect company.
    """
    service = CompetitiveIntelligenceService(db)
    runs = await service.list_analysis_runs(company_id=company_id, limit=limit)
    res = []
    for r in runs:
        res.append(await _format_run_response(db, r))
    return res


@router.get("/companies/{company_id}/runs/latest", response_model=CompetitiveAnalysisRunResponse)
async def get_latest_competitive_analysis_run(
    company_id: uuid.UUID,
    competitor_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the latest competitive analysis run for a company.
    """
    service = CompetitiveIntelligenceService(db)
    run = await service.get_latest_analysis_run(company_id=company_id, competitor_id=competitor_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No competitive analysis runs found")
    return await _format_run_response(db, run)


@router.get("/runs/{run_id}", response_model=CompetitiveAnalysisRunResponse)
async def get_competitive_analysis_run_by_id(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a specific competitive analysis run by ID.
    """
    run = await db.get(CompetitiveAnalysisRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis run {run_id} not found")
    return await _format_run_response(db, run)


@router.get("/companies/{company_id}/overview", response_model=CompetitiveOverviewResponse)
async def get_company_competitive_overview(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns an executive competitive SEO intelligence overview for a prospect company.
    """
    service = CompetitiveIntelligenceService(db)
    try:
        overview = await service.get_competitive_overview(company_id=company_id)
        return overview
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
