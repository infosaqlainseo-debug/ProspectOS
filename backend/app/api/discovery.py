import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from arq import create_pool
from arq.connections import RedisSettings

from app.db.session import get_db
from app.models import Job
from app.schemas.discovery import DiscoveryRequest
from app.core.config import settings

router = APIRouter()

async def get_redis_pool():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

@router.post("/jobs")
async def create_discovery_job(
    request: DiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis_pool)
):
    # Create the job in DB
    job = Job(
        job_type="company_discovery",
        status="QUEUED",
        requested_count=request.target_count,
        parameters=request.model_dump()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Enqueue to ARQ
    await redis.enqueue_job(
        "company_discovery_job",
        str(job.id),
        request.model_dump()
    )
    
    await redis.close()
    
    return {
        "job_id": job.id,
        "status": job.status
    }

@router.get("/jobs/{job_id}")
async def get_discovery_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.id,
        "status": job.status,
        "job_type": job.job_type,
        "requested_count": job.requested_count,
        "discovered_count": job.discovered_count,
        "validated_count": job.validated_count,
        "stored_count": job.stored_count,
        "duplicate_count": job.duplicate_count,
        "failed_count": job.failed_count,
        "error_message": job.error_message
    }
