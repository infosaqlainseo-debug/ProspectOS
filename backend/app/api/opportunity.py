import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from arq import create_pool
from arq.connections import RedisSettings

from app.db.session import get_db
from app.core.config import settings
from app.models import Company, Job, OpportunityProfile
from app.schemas.opportunity import OpportunityProfile as OpportunityProfileSchema

router = APIRouter()

@router.post("/evaluate/{company_id}", status_code=202)
async def trigger_opportunity_evaluation(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    # Verify company exists
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    job_id = str(uuid.uuid4())
    job = Job(id=uuid.UUID(job_id), job_type="opportunity_evaluation", status="QUEUED")
    db.add(job)
    await db.commit()
    
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    pool = await create_pool(redis_settings)
    await pool.enqueue_job("opportunity_evaluation_job", job_id, str(company_id))
    
    return {"message": "Opportunity evaluation job queued", "job_id": job_id}

@router.get("/{company_id}", response_model=List[OpportunityProfileSchema])
async def get_opportunity_profiles(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OpportunityProfile).where(OpportunityProfile.company_id == company_id).order_by(OpportunityProfile.created_at.desc())
    profiles = (await db.execute(stmt)).scalars().all()
    return profiles
