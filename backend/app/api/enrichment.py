from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.models import Job, Company
from app.core.redis import get_redis_settings
from arq import create_pool

router = APIRouter()

class BatchEnrichmentRequest(BaseModel):
    company_ids: Optional[List[str]] = None
    discovery_job_id: Optional[str] = None
    website_analysis_job_id: Optional[str] = None

@router.post("/seo")
async def batch_enrichment(req: BatchEnrichmentRequest, db: AsyncSession = Depends(get_db)):
    if not req.company_ids and not req.discovery_job_id and not req.website_analysis_job_id:
        raise HTTPException(status_code=400, detail="Provide company_ids or job id")
        
    c_ids = []
    if req.company_ids:
        c_ids = req.company_ids
        
    enqueued = []
    redis = await create_pool(get_redis_settings())
    for cid in c_ids:
        job = Job(job_type="seo_enrichment", status="QUEUED")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        await redis.enqueue_job("seo_enrichment_job", str(job.id), cid)
        enqueued.append({"job_id": str(job.id), "company_id": cid})
        
    await redis.close()
    return {"enqueued_jobs": len(enqueued), "jobs": enqueued}

from sqlalchemy import select
from app.models import SEOMetric

@router.get("/seo/{company_id}")
async def get_seo_metrics(company_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
        
    stmt = select(SEOMetric).where(SEOMetric.company_id == uid).order_by(SEOMetric.retrieved_at.desc())
    result = await db.execute(stmt)
    observations = result.scalars().all()
    
    return {"company_id": company_id, "observations": observations}
