import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.analytics import (
    RevenueFilterParams,
    RevenueSummary,
    ServiceRevenueBreakdown,
    ClientRevenueBreakdown,
    CampaignROIBreakdown,
    FunnelAnalysis,
    RevenueTrendItem,
    SnapshotCreateRequest,
    SnapshotResponse
)
from app.services.analytics.revenue_service import RevenueAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_filter_params(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO8601)"),
    service_category: Optional[str] = Query(None, description="Filter by service category"),
    campaign_id: Optional[uuid.UUID] = Query(None, description="Filter by outreach campaign ID"),
    company_id: Optional[uuid.UUID] = Query(None, description="Filter by client company ID"),
    currency: Optional[str] = Query(None, description="Filter by native currency code (e.g. USD, EUR)")
) -> RevenueFilterParams:
    return RevenueFilterParams(
        start_date=start_date,
        end_date=end_date,
        service_category=service_category,
        campaign_id=campaign_id,
        company_id=company_id,
        currency=currency
    )


@router.get("/revenue", response_model=RevenueSummary)
async def get_revenue_summary(
    filters: RevenueFilterParams = Depends(get_filter_params),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns executive revenue summary:
    - Realized closed-won revenue (gross and net after discounts/taxes/refunds)
    - Open pipeline value (strictly separated from realized revenue)
    - Weighted pipeline value
    - Verified cost amounts, gross profit, and margins (never fabricated)
    - Invoiced vs collected amounts
    - Deal counts, win rate, average deal size, sales cycle duration
    - Native currency breakdowns and data limitations
    """
    service = RevenueAnalyticsService(db)
    return await service.get_revenue_summary(filters)


@router.get("/services", response_model=List[ServiceRevenueBreakdown])
async def get_revenue_by_service(
    filters: RevenueFilterParams = Depends(get_filter_params),
    db: AsyncSession = Depends(get_db)
):
    """Returns revenue, deal count, and pipeline metrics segmented by service category."""
    service = RevenueAnalyticsService(db)
    return await service.get_revenue_by_service(filters)


@router.get("/clients", response_model=List[ClientRevenueBreakdown])
async def get_revenue_by_client(
    filters: RevenueFilterParams = Depends(get_filter_params),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns revenue leaderboard by client company with active pipeline volume."""
    service = RevenueAnalyticsService(db)
    return await service.get_revenue_by_client(filters, limit=limit)


@router.get("/campaigns", response_model=List[CampaignROIBreakdown])
async def get_campaign_roi(
    filters: RevenueFilterParams = Depends(get_filter_params),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns campaign-attributed revenue, fulfillment costs, and calculated ROI.
    Discloses sample sizes and correlation-based attribution caveats.
    """
    service = RevenueAnalyticsService(db)
    return await service.get_campaign_roi(filters)


@router.get("/funnel", response_model=FunnelAnalysis)
async def get_sales_funnel(
    filters: RevenueFilterParams = Depends(get_filter_params),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns stage-by-stage sales funnel metrics, progression rates, drop-offs,
    and automated pipeline bottleneck diagnosis.
    """
    service = RevenueAnalyticsService(db)
    return await service.get_funnel_analysis(filters)


@router.get("/trends", response_model=List[RevenueTrendItem])
async def get_revenue_trends(
    filters: RevenueFilterParams = Depends(get_filter_params),
    interval: str = Query("monthly", pattern="^(monthly|daily)$"),
    db: AsyncSession = Depends(get_db)
):
    """Returns historical time-series of realized revenue and new pipeline created."""
    service = RevenueAnalyticsService(db)
    return await service.get_revenue_trends(filters, interval=interval)


@router.get("/drilldown/deals")
async def get_deals_drilldown(
    filters: RevenueFilterParams = Depends(get_filter_params),
    stage: Optional[str] = Query(None, description="Filter by deal stage"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (WON, LOST, IN_PROGRESS)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Returns paginated underlying deal records with calculation provenance."""
    service = RevenueAnalyticsService(db)
    return await service.get_deals_drilldown(
        filters=filters,
        stage=stage,
        outcome=outcome,
        page=page,
        page_size=page_size
    )


@router.post("/snapshots", response_model=SnapshotResponse)
async def create_analytics_snapshot(
    request: SnapshotCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generates and persists an audited historical analytics snapshot to database."""
    service = RevenueAnalyticsService(db)
    snapshot = await service.create_snapshot(request)
    return snapshot


@router.get("/snapshots", response_model=List[SnapshotResponse])
async def list_analytics_snapshots(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists persistent historical revenue analytics snapshots."""
    service = RevenueAnalyticsService(db)
    return await service.list_snapshots(limit=limit)
