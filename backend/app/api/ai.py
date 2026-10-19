from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import uuid
from sqlalchemy import select

from app.db.session import get_db
from app.models import Job, Company, AIObservation, AIContradiction
from app.core.redis import get_redis_settings
from arq import create_pool

router = APIRouter()

class BatchAIExtractionRequest(BaseModel):
    company_ids: List[str]

@router.post("/extraction/batch")
async def batch_extraction(req: BatchAIExtractionRequest, db: AsyncSession = Depends(get_db)):
    if not req.company_ids:
        raise HTTPException(status_code=400, detail="Provide company_ids")
        
    enqueued = []
    redis = await create_pool(get_redis_settings())
    for cid in req.company_ids:
        job = Job(job_type="ai_extraction", status="QUEUED")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        await redis.enqueue_job("ai_extraction_job", str(job.id), cid)
        enqueued.append({"job_id": str(job.id), "company_id": cid})
        
    await redis.close()
    return {"enqueued_jobs": len(enqueued), "jobs": enqueued}

@router.get("/extraction/{company_id}/history")
async def extraction_history(company_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AIObservation).where(AIObservation.company_id == uuid.UUID(company_id)).order_by(AIObservation.created_at.desc())
    result = await db.execute(stmt)
    observations = result.scalars().all()
    return {"company_id": company_id, "observations": observations}

@router.get("/extraction/{company_id}/contradictions")
async def extraction_contradictions(company_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AIContradiction).where(AIContradiction.company_id == uuid.UUID(company_id)).order_by(AIContradiction.created_at.desc())
    result = await db.execute(stmt)
    contradictions = result.scalars().all()
    return {"company_id": company_id, "contradictions": contradictions}

class OverrideRequest(BaseModel):
    company_id: str
    attribute: str
    value: str
    reason: str

@router.post("/extraction/override")
async def manual_override(req: OverrideRequest, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(req.company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID")
        
    obs = AIObservation(
        company_id=uid,
        job_id=None,
        attribute_name=req.attribute,
        attribute_value=req.value,
        confidence=1.0,
        evidence_text=f"MANUAL OVERRIDE: {req.reason}",
        verification_status="VERIFIED"
    )
    db.add(obs)
    await db.commit()
    return {"status": "success"}
