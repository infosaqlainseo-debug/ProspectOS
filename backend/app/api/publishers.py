import uuid
import csv
from io import StringIO
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc

from app.db.session import get_db
from app.schemas.publishers import (
    ImportPreviewRequest, PublisherMapping, ImportCommitRequest, 
    PublisherRecordResponse, ImportBatchResponse
)
from app.services.publishers.import_service import PublisherImportService
from app.models import (
    PublisherRecord, ImportBatch, Company, 
    PublisherObservation, PublisherQualityScore
)

router = APIRouter(prefix="/publishers", tags=["Publishers"])

@router.post("/import/preview")
async def preview_import(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported currently")
    
    content = await file.read()
    text = content.decode("utf-8")
    
    reader = csv.DictReader(StringIO(text))
    rows = []
    try:
        for i, row in enumerate(reader):
            if i >= 5: # Just preview first 5 rows
                break
            rows.append(dict(row))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
        
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file appears empty or has no headers")

    return {
        "file_name": file.filename,
        "headers": reader.fieldnames,
        "preview_rows": rows
    }

@router.post("/import/commit", response_model=ImportBatchResponse)
async def commit_import(request: ImportCommitRequest, db: AsyncSession = Depends(get_db)):
    service = PublisherImportService(db)
    
    try:
        batch = await service.create_import_batch(f"batch_{request.batch_id}.csv", len(request.rows))
        batch = await service.process_import_batch(batch.id, request.mapping, request.rows, dry_run=request.dry_run)
        return batch
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PublisherRecordResponse])
async def list_publishers(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    quality_verdict: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            PublisherRecord,
            Company.canonical_domain,
            PublisherQualityScore
        )
        .outerjoin(Company, Company.id == PublisherRecord.company_id)
        .outerjoin(PublisherQualityScore, PublisherQualityScore.publisher_id == PublisherRecord.id)
    )
    if search:
        search_filter = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                PublisherRecord.publisher_name.ilike(search_filter),
                PublisherRecord.original_submitted_url.ilike(search_filter),
                Company.canonical_domain.ilike(search_filter)
            )
        )
    if quality_verdict:
        if quality_verdict == "NOT_AUDITED":
            stmt = stmt.where(PublisherQualityScore.id.is_(None))
        else:
            stmt = stmt.where(PublisherQualityScore.verdict == quality_verdict)

    stmt = stmt.order_by(desc(PublisherRecord.created_at)).offset(skip).limit(limit)
    rows = (await db.execute(stmt)).all()

    pub_ids = [r[0].id for r in rows]
    latest_obs_map = {}
    if pub_ids:
        stmt_obs = (
            select(PublisherObservation)
            .where(PublisherObservation.publisher_id.in_(pub_ids))
            .order_by(PublisherObservation.publisher_id, desc(PublisherObservation.observation_timestamp))
        )
        obs_res = (await db.execute(stmt_obs)).scalars().all()
        for obs in obs_res:
            if obs.publisher_id not in latest_obs_map:
                latest_obs_map[obs.publisher_id] = obs

    items = []
    for pub, canonical_domain, quality_score in rows:
        latest_obs = latest_obs_map.get(pub.id)
        item = PublisherRecordResponse(
            id=pub.id,
            company_id=pub.company_id,
            original_submitted_url=pub.original_submitted_url,
            publisher_name=pub.publisher_name,
            audience_focus=pub.audience_focus,
            status=pub.status,
            created_at=pub.created_at,
            canonical_domain=canonical_domain,
            price=latest_obs.price if latest_obs else None,
            currency=latest_obs.currency if latest_obs else None,
            metric_da=latest_obs.metric_da if latest_obs else None,
            metric_dr=latest_obs.metric_dr if latest_obs else None,
            metric_traffic=latest_obs.metric_traffic if latest_obs else None,
            quality_overall_score=quality_score.overall_quality_score if quality_score else None,
            quality_verdict=quality_score.verdict if quality_score else None,
            has_duplicates=quality_score.has_duplicates if quality_score else None,
            is_stale=quality_score.is_stale if quality_score else None
        )
        items.append(item)
    return items
