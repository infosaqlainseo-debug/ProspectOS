from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.models import Job, Company, WebsiteScan
from app.core.redis import get_redis_settings
from arq import create_pool

router = APIRouter()

class BatchAnalysisRequest(BaseModel):
    company_ids: Optional[List[str]] = None
    discovery_job_id: Optional[str] = None

@router.post("/website/{company_id}")
async def analyze_website(company_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
        
    company = await db.get(Company, uid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Create Job
    job = Job(job_type="website_analysis", status="QUEUED")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Enqueue
    try:
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job("website_analysis_job", str(job.id), company_id)
        await redis.close()
    except Exception as e:
        job.status = "FAILED"
        job.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=503, detail="Failed to enqueue website analysis job")
        
    return {"job_id": str(job.id), "status": job.status, "company_id": company_id}

@router.get("/website/{company_id}")
async def get_website_analysis(company_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
        
    # Get latest scan
    scan = (await db.execute(
        select(WebsiteScan)
        .where(WebsiteScan.company_id == uid)
        .order_by(WebsiteScan.scanned_at.desc())
        .limit(1)
    )).scalars().first()
    
    if not scan:
        return {"status": "NO_SCAN_FOUND"}
        
    return {
        "status": scan.scan_status,
        "http_status": scan.http_status,
        "scanned_at": scan.scanned_at,
        "title": scan.title,
        "error_message": scan.error_message
    }

@router.post("/batch")
async def batch_analyze(req: BatchAnalysisRequest, db: AsyncSession = Depends(get_db)):
    if not req.company_ids and not req.discovery_job_id:
        raise HTTPException(status_code=400, detail="Provide either company_ids or discovery_job_id")
        
    c_ids = []
    if req.company_ids:
        c_ids = req.company_ids
        
    # Handle discovery_job_id logic (future expansion: lookup companies from a discovery job)
    
    enqueued = []
    redis = await create_pool(get_redis_settings())
    for cid in c_ids:
        job = Job(job_type="website_analysis", status="QUEUED")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        await redis.enqueue_job("website_analysis_job", str(job.id), cid)
        enqueued.append({"job_id": str(job.id), "company_id": cid})
        
    await redis.close()
    return {"enqueued_jobs": len(enqueued), "jobs": enqueued}
