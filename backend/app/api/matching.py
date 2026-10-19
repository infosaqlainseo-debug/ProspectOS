import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models import CampaignProfile, MatchingRun, MatchResult, Shortlist, ShortlistItem
from app.schemas.matching import (
    CampaignProfileCreate, CampaignProfileResponse,
    MatchingRunResponse, MatchResultResponse,
    ShortlistCreate, ShortlistResponse
)
from app.services.matching.engine import MatchingEngine

router = APIRouter(prefix="/matching", tags=["matching"])

@router.get("/campaigns/prospect/{company_id}/profile", response_model=CampaignProfileResponse)
async def get_profile(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CampaignProfile).where(CampaignProfile.company_id == company_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Campaign profile not found")
    return profile

@router.put("/campaigns/prospect/{company_id}/profile", response_model=CampaignProfileResponse)
async def update_profile(company_id: uuid.UUID, profile_in: CampaignProfileCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CampaignProfile).where(CampaignProfile.company_id == company_id))
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = CampaignProfile(company_id=company_id, **profile_in.model_dump())
        db.add(profile)
    else:
        for k, v in profile_in.model_dump(exclude_unset=True).items():
            setattr(profile, k, v)
            
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/runs/{company_id}", response_model=MatchingRunResponse)
async def start_matching_run(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    engine = MatchingEngine(db)
    try:
        run = await engine.run_matching(company_id)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/runs/{run_id}/results", response_model=List[MatchResultResponse])
async def get_run_results(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchResult).where(MatchResult.matching_run_id == run_id).order_by(MatchResult.rank.asc()))
    return result.scalars().all()

@router.post("/shortlists/{company_id}", response_model=ShortlistResponse)
async def create_shortlist(company_id: uuid.UUID, data: ShortlistCreate, db: AsyncSession = Depends(get_db)):
    sl = Shortlist(company_id=company_id, name=data.name)
    db.add(sl)
    await db.commit()
    await db.refresh(sl)
    return sl
