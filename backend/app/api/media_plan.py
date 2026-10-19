import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from io import BytesIO
import pandas as pd

from app.db.session import get_db
from app.models import MediaPlan, MediaPlanItem, Company, PublisherRecord, PublisherObservation
from app.schemas.media_plan import (
    MediaPlanCreate, MediaPlanUpdate, MediaPlanResponse,
    MediaPlanItemCreate, MediaPlanItemResponse
)

router = APIRouter(prefix="/media-plans", tags=["media-plans"])

async def get_plan_with_items_and_totals(plan_id: uuid.UUID, db: AsyncSession) -> MediaPlanResponse:
    # Fetch plan
    result = await db.execute(select(MediaPlan).where(MediaPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Media plan not found")
    
    # Fetch items with publisher records and latest observations
    items_result = await db.execute(
        select(MediaPlanItem, PublisherRecord, PublisherObservation, Company.canonical_domain)
        .join(PublisherRecord, PublisherRecord.id == MediaPlanItem.publisher_id)
        .join(Company, Company.id == PublisherRecord.company_id)
        .outerjoin(
            PublisherObservation, 
            and_(
                PublisherObservation.publisher_id == PublisherRecord.id,
                # In a real heavy system we might window function this, but for now we fetch and filter in memory or rely on correct join
                # Assuming latest observation per publisher is simple enough
            )
        )
        .where(MediaPlanItem.media_plan_id == plan_id)
        .order_by(PublisherObservation.observation_timestamp.desc().nulls_last())
    )
    
    # Process items to remove duplicate observations (keeping latest)
    seen_items = {}
    for item, pub, obs, domain in items_result:
        if item.id not in seen_items:
            # use proposed price if exists, otherwise fallback to observation
            actual_price = item.proposed_price if item.proposed_price is not None else (obs.price if obs else None)
            actual_currency = item.proposed_currency if item.proposed_currency is not None else (obs.currency if obs else None)
            
            seen_items[item.id] = {
                "item": item,
                "publisher_name": pub.publisher_name,
                "canonical_domain": domain,
                "metric_da": obs.metric_da if obs else None,
                "metric_dr": obs.metric_dr if obs else None,
                "metric_traffic": obs.metric_traffic if obs else None,
                "verification_status": obs.verification_status if obs else "UNVERIFIED",
                "price": actual_price,
                "currency": actual_currency
            }
            
    items_out = []
    total_price = 0.0
    currencies = set()
    can_calculate = True
    warning = None
    
    for v in seen_items.values():
        item = v["item"]
        resp = MediaPlanItemResponse.model_validate(item)
        resp.publisher_name = v["publisher_name"]
        resp.canonical_domain = v["canonical_domain"]
        resp.metric_da = v["metric_da"]
        resp.metric_dr = v["metric_dr"]
        resp.metric_traffic = v["metric_traffic"]
        resp.verification_status = v["verification_status"]
        
        # update proposed for response if empty
        if resp.proposed_price is None:
            resp.proposed_price = v["price"]
        if resp.proposed_currency is None:
            resp.proposed_currency = v["currency"]
            
        items_out.append(resp)
        
        # Calculation logic
        if v["price"] is None:
            can_calculate = False
            warning = "One or more publishers are missing price information."
        else:
            total_price += float(v["price"])
            if v["currency"]:
                currencies.add(v["currency"].upper())
                
    if can_calculate and len(currencies) > 1:
        can_calculate = False
        warning = f"Mixed currencies detected ({', '.join(currencies)}). Cannot calculate accurate total."
        
    final_currency = currencies.pop() if len(currencies) == 1 else None
    
    resp_plan = MediaPlanResponse.model_validate(plan)
    resp_plan.items = items_out
    resp_plan.can_calculate_totals = can_calculate
    resp_plan.total_price = total_price if can_calculate else None
    resp_plan.currency = final_currency if can_calculate else None
    resp_plan.calculation_warning = warning
    
    return resp_plan


@router.post("/company/{company_id}", response_model=MediaPlanResponse)
async def create_media_plan(company_id: uuid.UUID, plan_in: MediaPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = MediaPlan(company_id=company_id, **plan_in.model_dump())
    db.add(plan)
    await db.commit()
    return await get_plan_with_items_and_totals(plan.id, db)


@router.get("/company/{company_id}")
async def get_company_media_plans(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaPlan).where(MediaPlan.company_id == company_id).order_by(MediaPlan.created_at.desc()))
    plans = result.scalars().all()
    # Return light version without items
    return plans

@router.get("/{plan_id}", response_model=MediaPlanResponse)
async def get_media_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_plan_with_items_and_totals(plan_id, db)


@router.put("/{plan_id}", response_model=MediaPlanResponse)
async def update_media_plan(plan_id: uuid.UUID, plan_in: MediaPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaPlan).where(MediaPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Media plan not found")
        
    for k, v in plan_in.model_dump(exclude_unset=True).items():
        setattr(plan, k, v)
        
    await db.commit()
    return await get_plan_with_items_and_totals(plan.id, db)


@router.post("/{plan_id}/items", response_model=MediaPlanResponse)
async def add_item_to_plan(plan_id: uuid.UUID, item_in: MediaPlanItemCreate, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(MediaPlan).where(MediaPlan.id == plan_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Media plan not found")
        
    # Check if publisher already in plan
    existing = await db.execute(
        select(MediaPlanItem).where(
            MediaPlanItem.media_plan_id == plan_id,
            MediaPlanItem.publisher_id == item_in.publisher_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Publisher already in media plan")
        
    item = MediaPlanItem(media_plan_id=plan_id, **item_in.model_dump())
    db.add(item)
    await db.commit()
    return await get_plan_with_items_and_totals(plan_id, db)


@router.delete("/{plan_id}/items/{item_id}", response_model=MediaPlanResponse)
async def remove_item_from_plan(plan_id: uuid.UUID, item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MediaPlanItem).where(
            MediaPlanItem.id == item_id,
            MediaPlanItem.media_plan_id == plan_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in plan")
        
    await db.delete(item)
    await db.commit()
    return await get_plan_with_items_and_totals(plan_id, db)

@router.get("/{plan_id}/export/excel")
async def export_media_plan_excel(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    plan_data = await get_plan_with_items_and_totals(plan_id, db)
    
    # Build dataframe
    rows = []
    for item in plan_data.items:
        rows.append({
            "Publisher Name": item.publisher_name or item.canonical_domain,
            "Domain": item.canonical_domain,
            "Domain Authority (DA)": item.metric_da,
            "Domain Rating (DR)": item.metric_dr,
            "Organic Traffic": item.metric_traffic,
            "Verification Status": item.verification_status,
            "Price": item.proposed_price,
            "Currency": item.proposed_currency,
            "Notes": item.notes
        })
        
    df = pd.DataFrame(rows)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Header info could be added on top, but a simple dataframe is fine for now
        df.to_excel(writer, index=False, sheet_name="Media Plan")
        
    output.seek(0)
    
    filename = f"Media_Plan_{plan_data.name.replace(' ', '_')}_{plan_data.created_at.strftime('%Y%m%d')}.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
