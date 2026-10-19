import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.services.publishers.quality_service import PublisherQualityService
from app.schemas.publisher_quality import (
    PublisherQualitySummaryResponse,
    PublisherQualityFindingResponse,
    PublisherDetailedQualityResponse,
    PublisherQualityScoreResponse,
    QualityFindingResolveRequest,
    ManualCorrectionRequest,
    PublisherRefreshRequest,
    PublisherRefreshLogResponse,
    BatchAuditRequest,
    PublisherObservationTimelineItem
)
from app.models import PublisherQualityFinding, PublisherRefreshLog

router = APIRouter(prefix="/publishers", tags=["Publisher Intelligence & Data Quality Monitoring"])


# =========================================================================
# 1. Quality Summary & Dashboard Overview
# =========================================================================

@router.get("/quality/summary", response_model=PublisherQualitySummaryResponse)
async def get_publisher_quality_summary(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated publisher data quality metrics, issue counts, and severity breakdowns.
    """
    service = PublisherQualityService(db)
    return await service.get_quality_summary()


# =========================================================================
# 2. Quality Findings Management
# =========================================================================

@router.get("/quality/findings", response_model=List[PublisherQualityFindingResponse])
async def list_quality_findings(
    publisher_id: Optional[uuid.UUID] = Query(None, description="Filter by publisher ID"),
    issue_type: Optional[str] = Query(None, description="MISSING_FIELD, STALE_DATA, INVALID_DATA, DUPLICATE_RECORD, CONFLICTING_DATA"),
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW, INFO"),
    status: Optional[str] = Query("OPEN", description="OPEN, RESOLVED, DISMISSED, IN_REVIEW, ALL"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns reviewable publisher data quality findings with traceable severity and evidence.
    """
    stmt = select(PublisherQualityFinding)
    if publisher_id:
        stmt = stmt.where(PublisherQualityFinding.publisher_id == publisher_id)
    if issue_type:
        stmt = stmt.where(PublisherQualityFinding.issue_type == issue_type.upper())
    if severity:
        stmt = stmt.where(PublisherQualityFinding.severity == severity.upper())
    if status and status.upper() != "ALL":
        stmt = stmt.where(PublisherQualityFinding.status == status.upper())

    stmt = stmt.order_by(
        desc(PublisherQualityFinding.severity == "CRITICAL"),
        desc(PublisherQualityFinding.severity == "HIGH"),
        desc(PublisherQualityFinding.created_at)
    ).offset(offset).limit(limit)

    findings = (await db.execute(stmt)).scalars().all()
    return [PublisherQualityFindingResponse.model_validate(f) for f in findings]


@router.post("/quality/findings/{finding_id}/resolve", response_model=PublisherQualityFindingResponse)
async def resolve_quality_finding(
    finding_id: uuid.UUID,
    request: QualityFindingResolveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resolves or dismisses a quality finding with attributable human justification.
    """
    service = PublisherQualityService(db)
    try:
        finding = await service.resolve_finding(
            finding_id=finding_id,
            action=request.resolution_action,
            notes=request.resolution_notes,
            actor=request.actor
        )
        return PublisherQualityFindingResponse.model_validate(finding)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 3. Batch Quality Audit
# =========================================================================

@router.post("/quality/audit")
async def run_batch_quality_audit(
    request: BatchAuditRequest = BatchAuditRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers quality audit across all or specified publishers.
    """
    service = PublisherQualityService(db)
    return await service.audit_all_publishers(limit=request.limit or 100, publisher_ids=request.publisher_ids)


# =========================================================================
# 4. Single Publisher Detailed Quality Dossier
# =========================================================================

@router.get("/{publisher_id}/quality", response_model=PublisherDetailedQualityResponse)
async def get_publisher_quality_dossier(
    publisher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns complete quality score, field-level freshness meters, observation history,
    and open/resolved findings for an individual publisher.
    """
    service = PublisherQualityService(db)
    try:
        return await service.get_detailed_publisher_quality(publisher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{publisher_id}/audit", response_model=PublisherQualityScoreResponse)
async def audit_single_publisher(
    publisher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Runs an on-demand data quality audit for a single publisher.
    """
    service = PublisherQualityService(db)
    try:
        score, _ = await service.audit_publisher(publisher_id)
        return PublisherQualityScoreResponse.model_validate(score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# 5. Refresh Data Through Approved Sources Only
# =========================================================================

@router.post("/{publisher_id}/refresh")
async def refresh_publisher_data(
    publisher_id: uuid.UUID,
    request: PublisherRefreshRequest = PublisherRefreshRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes metrics or website health strictly through approved, configured providers.
    If providers are unconfigured, records PROVIDER_NOT_CONFIGURED and preserves existing data.
    """
    service = PublisherQualityService(db)
    try:
        return await service.refresh_publisher(
            publisher_id=publisher_id,
            target_fields=request.target_fields,
            actor=request.actor
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{publisher_id}/refresh-logs", response_model=List[PublisherRefreshLogResponse])
async def get_publisher_refresh_logs(
    publisher_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns audit history of provider refresh attempts and outcomes.
    """
    stmt = (
        select(PublisherRefreshLog)
        .where(PublisherRefreshLog.publisher_id == publisher_id)
        .order_by(desc(PublisherRefreshLog.created_at))
        .limit(limit)
    )
    logs = (await db.execute(stmt)).scalars().all()
    return [PublisherRefreshLogResponse.model_validate(l) for l in logs]


# =========================================================================
# 6. Attributable Manual Corrections
# =========================================================================

@router.post("/{publisher_id}/correction", response_model=PublisherObservationTimelineItem)
async def apply_manual_publisher_correction(
    publisher_id: uuid.UUID,
    request: ManualCorrectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Records an attributable human correction to publisher rates or metrics.
    Inserts a new observation while preserving previous observations.
    """
    service = PublisherQualityService(db)
    try:
        obs = await service.apply_manual_correction(
            publisher_id=publisher_id,
            price=request.price,
            currency=request.currency,
            metric_da=request.metric_da,
            metric_dr=request.metric_dr,
            metric_traffic=request.metric_traffic,
            pricing_model=request.pricing_model,
            notes=request.notes,
            actor=request.actor
        )
        return PublisherObservationTimelineItem.model_validate(obs)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
