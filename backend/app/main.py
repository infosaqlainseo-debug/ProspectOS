from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from arq import create_pool
from arq.connections import RedisSettings
from urllib.parse import urlparse
import uuid

from app.core.config import settings
from app.db.session import get_db
from app.models import Job
from fastapi.middleware.cors import CORSMiddleware
from app.core.redis import get_redis_settings
from app.api import discovery, analysis, enrichment, ai, companies, opportunity, workflows, publishers, matching, media_plan, outreach, crm, sales_intelligence, publisher_quality, analytics, competitive, portal, system
app = FastAPI(title="ProspectOS API", version="1.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(enrichment.router, prefix="/enrichment", tags=["enrichment"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(opportunity.router, prefix="/opportunity", tags=["opportunity"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(publishers.router, tags=["publishers"])
app.include_router(publisher_quality.router)
app.include_router(matching.router)
app.include_router(media_plan.router)
app.include_router(outreach.router)
app.include_router(crm.router)
app.include_router(sales_intelligence.router)
app.include_router(analytics.router)
app.include_router(competitive.router)
app.include_router(portal.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/health/database")
async def health_database(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/health/queue")
async def health_queue():
    try:
        redis = await create_pool(get_redis_settings())
        info = await redis.info()
        if hasattr(redis, "aclose"):
            await redis.aclose()
        else:
            await redis.close()
        return {"status": "ok", "queue": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/health/version")
async def health_version():
    return {"version": app.version}

class JobCreate(BaseModel):
    job_type: str

@app.post("/jobs")
async def create_job(job_in: JobCreate, db: AsyncSession = Depends(get_db)):
    new_job = Job(job_type=job_in.job_type, status="QUEUED")
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    try:
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job("health_check_job", str(new_job.id))
        if hasattr(redis, "aclose"):
            await redis.aclose()
        else:
            await redis.close()
    except Exception as e:
        new_job.status = "FAILED"
        new_job.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=503, detail="Failed to enqueue job")
        
    return {"job_id": str(new_job.id), "status": new_job.status}

@app.get("/jobs")
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
    count_stmt = select(func.count()).select_from(Job)
    
    total = (await db.execute(count_stmt)).scalar()
    jobs = (await db.execute(stmt)).scalars().all()
    
    return {"total": total, "items": jobs}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
        
    job = await db.get(Job, uid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": str(job.id), "status": job.status, "job_type": job.job_type}
