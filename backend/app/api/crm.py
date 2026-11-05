import uuid
import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_

from app.db.session import get_db
from app.models import (
    Company,
    CRMDeal,
    CRMTask,
    CRMNote,
    CRMActivity,
    OpportunityProfile
)
from app.models.crm import (
    CRMLeadSegment,
    CRMSegmentMember,
    CRMUserPreference,
    CRMFeedbackLog,
    CRMAIResearch,
    CRMCustomField
)
from app.schemas.crm import (
    VALID_SALES_STAGES,
    StageUpdateRequest,
    DealCreate,
    DealUpdate,
    DealResponse,
    TaskCreate,
    TaskUpdate,
    TaskCompleteRequest,
    TaskResponse,
    NoteCreate,
    NoteResponse,
    ActivityResponse,
    UnifiedProspectSummary,
    UnifiedProspectDetail,
    PipelineColumn,
    CRMReportMetrics,
    ScraperImportRequest,
    ScraperImportResponse,
    LeadCreate,
    LeadUpdate,
    LeadBulkUpdateRequest,
    LeadBulkDeleteRequest,
    CRMLeadSegmentCreate,
    CRMLeadSegmentUpdate,
    CRMLeadSegmentResponse,
    CRMAIResearchResponse,
    AIAssistantQueryRequest,
    AIAssistantQueryResponse
)
from app.services.crm.service import CRMService
from app.services.crm.bridge import ScraperCRMBridge, extract_canonical_domain, compute_lead_score
from app.services.crm.learning import AdaptiveLearningService
from app.services.crm.assistant import CRMAssistantService

router = APIRouter(prefix="/crm", tags=["crm"])


# =========================================================================
# 1. Scraper-to-CRM Bridge
# =========================================================================

@router.post("/import-from-scraper", response_model=ScraperImportResponse)
async def import_from_scraper(
    req: ScraperImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Seamlessly imports extracted leads from ProspectOS Scraper into the central CRM database.
    Performs canonical domain deduplication, conflict resolution, tag merging, and audit activity logging.
    """
    bridge = ScraperCRMBridge(db)
    return await bridge.import_extracted_records(req)


# =========================================================================
# 2. Leads Management & Directory
# =========================================================================

@router.get("/leads")
async def list_crm_leads(
    q: Optional[str] = Query(None, description="Search term for company name, domain, email, city"),
    stage: Optional[str] = Query(None, description="Filter by sales stage"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    country: Optional[str] = Query(None, description="Filter by country"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)"),
    min_score: Optional[float] = Query(None, description="Minimum lead score (0-100)"),
    max_score: Optional[float] = Query(None, description="Maximum lead score (0-100)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    lead_source: Optional[str] = Query(None, description="Filter by lead source (SCRAPER, MANUAL, CSV_IMPORT)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|company_name|lead_score|stage_updated_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    High-density, filterable, and paginated CRM leads directory.
    Provides complete company intelligence, contact details, tags, and transparent lead scores.
    """
    stmt = select(Company)

    if stage:
        stmt = stmt.where(Company.sales_stage == stage.upper())
    if industry:
        stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
    if country:
        stmt = stmt.where(Company.country.ilike(f"%{country}%"))
    if priority:
        stmt = stmt.where(Company.lead_priority == priority.upper())
    if lead_source:
        stmt = stmt.where(Company.lead_source == lead_source.upper())
    if min_score is not None:
        stmt = stmt.where(Company.lead_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Company.lead_score <= max_score)
    if tag:
        # Check tag in JSONB array
        stmt = stmt.where(Company.tags.contains([tag.lower()]))

    if q:
        search_pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Company.company_name.ilike(search_pattern),
                Company.canonical_domain.ilike(search_pattern),
                Company.public_email.ilike(search_pattern),
                Company.city.ilike(search_pattern),
                Company.contact_person.ilike(search_pattern)
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sorting
    sort_col = getattr(Company, sort_by)
    if sort_dir == "desc":
        stmt = stmt.order_by(desc(sort_col).nulls_last())
    else:
        stmt = stmt.order_by(sort_col.nulls_first())

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    companies = (await db.execute(stmt)).scalars().all()

    items = []
    for c in companies:
        items.append({
            "id": str(c.id),
            "company_name": c.company_name or c.canonical_domain or "Unnamed Prospect",
            "canonical_domain": c.canonical_domain,
            "website_url": c.website_url,
            "industry": c.industry,
            "sub_industry": c.sub_industry,
            "country": c.country,
            "city": c.city,
            "state": c.state,
            "description": c.description,
            "company_size": c.company_size,
            "sales_stage": c.sales_stage or "NEW",
            "lead_priority": c.lead_priority or "MEDIUM",
            "lead_score": c.lead_score,
            "lead_score_components": c.lead_score_components,
            "lead_source": c.lead_source or "SCRAPER",
            "tags": c.tags or [],
            "custom_fields": c.custom_fields or {},
            "contact_person": c.contact_person,
            "contact_title": c.contact_title,
            "public_email": c.public_email,
            "phone_number": c.phone_number,
            "linkedin_url": c.linkedin_url,
            "facebook_url": c.facebook_url,
            "instagram_url": c.instagram_url,
            "whatsapp_number": c.whatsapp_number,
            "domain_rating": c.domain_rating,
            "organic_traffic": c.organic_traffic,
            "website_status": c.website_status or "ACTIVE",
            "lead_owner": c.lead_owner,
            "stage_updated_at": c.stage_updated_at.isoformat() if c.stage_updated_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.post("/leads")
async def create_crm_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new lead manually in the CRM with automatic scoring and deduplication check."""
    canonical = extract_canonical_domain(data.canonical_domain or data.website_url)

    if canonical:
        existing = (await db.execute(select(Company).where(Company.canonical_domain == canonical))).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail=f"A lead with domain '{canonical}' already exists in CRM.")

    score_data = {
        "company_name": data.company_name,
        "canonical_domain": canonical,
        "website_url": data.website_url,
        "industry": data.industry,
        "country": data.country,
        "city": data.city,
        "description": data.description,
        "public_email": data.public_email,
        "phone_number": data.phone_number,
        "linkedin_url": data.linkedin_url,
    }
    score, breakdown = compute_lead_score(score_data)

    new_comp = Company(
        company_name=data.company_name,
        canonical_domain=canonical,
        website_url=data.website_url,
        industry=data.industry,
        country=data.country,
        city=data.city,
        description=data.description,
        company_size=data.company_size,
        contact_person=data.contact_person,
        contact_title=data.contact_title,
        public_email=data.public_email,
        phone_number=data.phone_number,
        linkedin_url=data.linkedin_url,
        sales_stage=data.sales_stage.upper(),
        lead_priority=data.lead_priority.upper(),
        lead_score=score,
        lead_score_components=breakdown,
        lead_source=data.lead_source,
        tags=data.tags or [],
        custom_fields=data.custom_fields or {}
    )
    db.add(new_comp)
    await db.flush()

    # Activity log
    activity = CRMActivity(
        company_id=new_comp.id,
        activity_type="LEAD_CREATED",
        actor="human_reviewer",
        title="New Lead Created Manually",
        details={"company_name": new_comp.company_name, "score": score}
    )
    db.add(activity)

    await db.commit()
    await db.refresh(new_comp)

    return {"success": True, "lead_id": str(new_comp.id), "company_name": new_comp.company_name}


@router.get("/leads/{company_id}")
async def get_crm_lead_detail(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Comprehensive lead profile: company details, contact info, SEO metrics, AI research, notes, tasks, and activity timeline."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Fetch latest AI research if available
    research_stmt = select(CRMAIResearch).where(CRMAIResearch.company_id == company_id).order_by(desc(CRMAIResearch.analyzed_at))
    ai_research = (await db.execute(research_stmt)).scalars().first()

    # Fetch notes
    notes_stmt = select(CRMNote).where(CRMNote.company_id == company_id).order_by(desc(CRMNote.created_at))
    notes = (await db.execute(notes_stmt)).scalars().all()

    # Fetch activities
    activities_stmt = select(CRMActivity).where(CRMActivity.company_id == company_id).order_by(desc(CRMActivity.created_at)).limit(50)
    activities = (await db.execute(activities_stmt)).scalars().all()

    # Fetch tasks
    tasks_stmt = select(CRMTask).where(CRMTask.company_id == company_id).order_by(desc(CRMTask.created_at))
    tasks = (await db.execute(tasks_stmt)).scalars().all()

    # Fetch deals
    deals_stmt = select(CRMDeal).where(CRMDeal.company_id == company_id).order_by(desc(CRMDeal.created_at))
    deals = (await db.execute(deals_stmt)).scalars().all()

    return {
        "company": {
            "id": str(company.id),
            "company_name": company.company_name or company.canonical_domain or "Unnamed Prospect",
            "canonical_domain": company.canonical_domain,
            "website_url": company.website_url,
            "industry": company.industry,
            "sub_industry": company.sub_industry,
            "country": company.country,
            "city": company.city,
            "state": company.state,
            "description": company.description,
            "company_size": company.company_size,
            "sales_stage": company.sales_stage or "NEW",
            "lead_priority": company.lead_priority or "MEDIUM",
            "lead_score": company.lead_score,
            "lead_score_components": company.lead_score_components,
            "lead_source": company.lead_source or "SCRAPER",
            "tags": company.tags or [],
            "custom_fields": company.custom_fields or {},
            "contact_person": company.contact_person,
            "contact_title": company.contact_title,
            "public_email": company.public_email,
            "phone_number": company.phone_number,
            "linkedin_url": company.linkedin_url,
            "facebook_url": company.facebook_url,
            "instagram_url": company.instagram_url,
            "whatsapp_number": company.whatsapp_number,
            "domain_rating": company.domain_rating,
            "organic_traffic": company.organic_traffic,
            "website_status": company.website_status or "ACTIVE",
            "technology_stack": company.technology_stack or [],
            "data_verification_status": company.data_verification_status or "VERIFIED",
            "lead_owner": company.lead_owner,
            "qualification_notes": company.qualification_notes,
            "stage_updated_at": company.stage_updated_at.isoformat() if company.stage_updated_at else None,
            "created_at": company.created_at.isoformat() if company.created_at else None,
            "updated_at": company.updated_at.isoformat() if company.updated_at else None
        },
        "ai_research": {
            "id": str(ai_research.id),
            "executive_summary": ai_research.executive_summary,
            "target_market": ai_research.target_market,
            "value_proposition": ai_research.value_proposition,
            "seo_weaknesses": ai_research.seo_weaknesses,
            "backlink_opportunities": ai_research.backlink_opportunities,
            "recommended_services": ai_research.recommended_services,
            "growth_opportunities": ai_research.growth_opportunities,
            "tech_stack_detected": ai_research.tech_stack_detected,
            "confidence_score": ai_research.confidence_score,
            "model_used": ai_research.model_used,
            "analyzed_at": ai_research.analyzed_at.isoformat()
        } if ai_research else None,
        "notes": [
            {
                "id": str(n.id),
                "author": n.author,
                "content": n.content,
                "created_at": n.created_at.isoformat()
            }
            for n in notes
        ],
        "activities": [
            {
                "id": str(a.id),
                "activity_type": a.activity_type,
                "actor": a.actor,
                "title": a.title,
                "details": a.details,
                "created_at": a.created_at.isoformat()
            }
            for a in activities
        ],
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "task_type": t.task_type,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat()
            }
            for t in tasks
        ],
        "deals": [
            {
                "id": str(d.id),
                "deal_name": d.deal_name,
                "service_category": d.service_category,
                "stage": d.stage,
                "estimated_value": d.estimated_value,
                "created_at": d.created_at.isoformat()
            }
            for d in deals
        ]
    }


@router.put("/leads/{company_id}")
async def update_crm_lead(company_id: uuid.UUID, data: LeadUpdate, db: AsyncSession = Depends(get_db)):
    """Updates lead attributes, tags, custom fields, or contact info."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Lead not found")

    if data.company_name is not None:
        company.company_name = data.company_name
    if data.website_url is not None:
        company.website_url = data.website_url
    if data.canonical_domain is not None:
        company.canonical_domain = extract_canonical_domain(data.canonical_domain)
    if data.industry is not None:
        company.industry = data.industry
    if data.country is not None:
        company.country = data.country
    if data.city is not None:
        company.city = data.city
    if data.description is not None:
        company.description = data.description
    if data.company_size is not None:
        company.company_size = data.company_size
    if data.contact_person is not None:
        company.contact_person = data.contact_person
    if data.contact_title is not None:
        company.contact_title = data.contact_title
    if data.public_email is not None:
        company.public_email = data.public_email
    if data.phone_number is not None:
        company.phone_number = data.phone_number
    if data.linkedin_url is not None:
        company.linkedin_url = data.linkedin_url
    if data.lead_priority is not None:
        company.lead_priority = data.lead_priority.upper()
    if data.lead_score is not None:
        company.lead_score = data.lead_score
    if data.lead_owner is not None:
        company.lead_owner = data.lead_owner
    if data.tags is not None:
        company.tags = data.tags
    if data.custom_fields is not None:
        company.custom_fields = data.custom_fields
    if data.qualification_notes is not None:
        company.qualification_notes = data.qualification_notes

    company.updated_at = datetime.now(timezone.utc)

    # Activity log
    activity = CRMActivity(
        company_id=company.id,
        activity_type="LEAD_UPDATED",
        actor="human_reviewer",
        title="Lead Record Updated",
        details={"updated_at": company.updated_at.isoformat()}
    )
    db.add(activity)

    await db.commit()
    await db.refresh(company)

    return {"success": True, "lead_id": str(company.id), "company_name": company.company_name}


@router.delete("/leads/{company_id}")
async def delete_crm_lead(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Deletes a lead and cascading associations from the CRM."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.delete(company)
    await db.commit()

    return {"success": True, "deleted_lead_id": str(company_id)}


@router.post("/leads/bulk-update")
async def bulk_update_crm_leads(req: LeadBulkUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Performs bulk stage transitions, bulk tagging, and owner assignment across selected leads."""
    if not req.lead_ids:
        raise HTTPException(status_code=400, detail="No lead IDs provided")

    stmt = select(Company).where(Company.id.in_(req.lead_ids))
    companies = (await db.execute(stmt)).scalars().all()

    learning_svc = AdaptiveLearningService(db)

    for comp in companies:
        if req.sales_stage:
            old_stage = comp.sales_stage
            comp.sales_stage = req.sales_stage.upper()
            comp.stage_updated_at = datetime.now(timezone.utc)
            # Log feedback
            await learning_svc.log_user_feedback(
                company_id=comp.id,
                action_taken=f"BULK_STAGE_{req.sales_stage.upper()}",
                previous_stage=old_stage,
                new_stage=req.sales_stage.upper(),
                actor=req.actor or "human_reviewer"
            )
        if req.lead_priority:
            comp.lead_priority = req.lead_priority.upper()
        if req.lead_owner:
            comp.lead_owner = req.lead_owner
        if req.add_tags:
            cur = comp.tags or []
            comp.tags = list(set(cur + [t.lower() for t in req.add_tags]))
        if req.remove_tags:
            cur = comp.tags or []
            remove_set = set([t.lower() for t in req.remove_tags])
            comp.tags = [t for t in cur if t not in remove_set]

        comp.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return {"success": True, "updated_count": len(companies)}


@router.post("/leads/bulk-delete")
async def bulk_delete_crm_leads(req: LeadBulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    """Deletes multiple selected leads with confirmation."""
    if not req.lead_ids:
        raise HTTPException(status_code=400, detail="No lead IDs provided")

    stmt = select(Company).where(Company.id.in_(req.lead_ids))
    companies = (await db.execute(stmt)).scalars().all()

    for comp in companies:
        await db.delete(comp)

    await db.commit()
    return {"success": True, "deleted_count": len(companies)}


@router.put("/leads/{company_id}/stage")
async def update_lead_stage(
    company_id: uuid.UUID,
    req: StageUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Moves lead stage, creates activity, and logs adaptive learning feedback."""
    service = CRMService(db)
    learning_svc = AdaptiveLearningService(db)

    try:
        updated = await service.update_prospect_stage(
            company_id=company_id,
            new_stage=req.new_stage,
            reason=req.reason,
            notes=req.notes,
            actor=req.actor or "human_reviewer"
        )
        # Log to adaptive learning system
        feedback_action = "STAGE_CHANGE"
        if req.new_stage.upper() in ["QUALIFIED", "WON"]:
            feedback_action = "QUALIFIED"
        elif req.new_stage.upper() in ["LOST", "NOT_A_FIT", "NOT_RELEVANT"]:
            feedback_action = "REJECTED"

        await learning_svc.log_user_feedback(
            company_id=company_id,
            action_taken=feedback_action,
            new_stage=req.new_stage.upper(),
            feedback_reason=req.reason or req.notes,
            actor=req.actor or "human_reviewer"
        )

        return {
            "success": True,
            "company_id": str(updated.id),
            "new_stage": updated.sales_stage,
            "stage_updated_at": updated.stage_updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 3. AI Research ("Analyze with AI")
# =========================================================================

@router.post("/leads/{company_id}/analyze-ai", response_model=CRMAIResearchResponse)
async def analyze_lead_with_ai(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Executes deep AI lead research: extracts value proposition, target market,
    SEO weaknesses, backlink opportunities, and high-impact service recommendations.
    """
    assistant_svc = CRMAssistantService(db)
    try:
        research = await assistant_svc.analyze_lead_with_ai(company_id)
        return research
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/leads/{company_id}/research", response_model=Optional[CRMAIResearchResponse])
async def get_lead_ai_research(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves existing AI research for a lead if already generated."""
    stmt = select(CRMAIResearch).where(CRMAIResearch.company_id == company_id).order_by(desc(CRMAIResearch.analyzed_at))
    research = (await db.execute(stmt)).scalars().first()
    return research


# =========================================================================
# 4. Lead Lists & Segmentation
# =========================================================================

@router.get("/segments", response_model=List[CRMLeadSegmentResponse])
async def list_segments(db: AsyncSession = Depends(get_db)):
    """Lists dynamic and static lead lists/segments with real-time matching member counts."""
    stmt = select(CRMLeadSegment).order_by(desc(CRMLeadSegment.created_at))
    segments = (await db.execute(stmt)).scalars().all()

    # Dynamically update member count for dynamic segments
    for seg in segments:
        if seg.is_dynamic:
            crit = seg.filter_criteria or {}
            c_stmt = select(func.count(Company.id))
            if crit.get("country"):
                c_stmt = c_stmt.where(Company.country.ilike(f"%{crit['country']}%"))
            if crit.get("industry"):
                c_stmt = c_stmt.where(Company.industry.ilike(f"%{crit['industry']}%"))
            if crit.get("min_score"):
                c_stmt = c_stmt.where(Company.lead_score >= float(crit["min_score"]))
            if crit.get("stage"):
                c_stmt = c_stmt.where(Company.sales_stage == crit["stage"].upper())
            if crit.get("tag"):
                c_stmt = c_stmt.where(Company.tags.contains([crit["tag"].lower()]))
            seg.member_count = (await db.execute(c_stmt)).scalar() or 0
        else:
            # Static list: count associations
            s_stmt = select(func.count(CRMSegmentMember.id)).where(CRMSegmentMember.segment_id == seg.id)
            seg.member_count = (await db.execute(s_stmt)).scalar() or 0

    return segments


@router.post("/segments", response_model=CRMLeadSegmentResponse)
async def create_segment(req: CRMLeadSegmentCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new dynamic or static lead segment with rule configuration."""
    seg = CRMLeadSegment(
        name=req.name,
        description=req.description,
        is_dynamic=req.is_dynamic,
        filter_criteria=req.filter_criteria,
        color=req.color,
        icon=req.icon or "folder"
    )
    db.add(seg)
    await db.commit()
    await db.refresh(seg)
    return seg


@router.delete("/segments/{segment_id}")
async def delete_segment(segment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Deletes a lead segment."""
    seg = await db.get(CRMLeadSegment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    await db.delete(seg)
    await db.commit()
    return {"success": True, "deleted_segment_id": str(segment_id)}


@router.get("/segments/{segment_id}/leads")
async def get_segment_leads(
    segment_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all qualifying leads belonging to a specific segment."""
    seg = await db.get(CRMLeadSegment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    if seg.is_dynamic:
        crit = seg.filter_criteria or {}
        stmt = select(Company)
        if crit.get("country"):
            stmt = stmt.where(Company.country.ilike(f"%{crit['country']}%"))
        if crit.get("industry"):
            stmt = stmt.where(Company.industry.ilike(f"%{crit['industry']}%"))
        if crit.get("min_score"):
            stmt = stmt.where(Company.lead_score >= float(crit["min_score"]))
        if crit.get("stage"):
            stmt = stmt.where(Company.sales_stage == crit["stage"].upper())
        if crit.get("tag"):
            stmt = stmt.where(Company.tags.contains([crit["tag"].lower()]))
    else:
        stmt = select(Company).join(CRMSegmentMember, CRMSegmentMember.company_id == Company.id).where(CRMSegmentMember.segment_id == segment_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(desc(Company.lead_score), desc(Company.created_at)).offset(offset).limit(page_size)
    leads = (await db.execute(stmt)).scalars().all()

    return {
        "segment_id": str(seg.id),
        "segment_name": seg.name,
        "is_dynamic": seg.is_dynamic,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(c.id),
                "company_name": c.company_name or c.canonical_domain,
                "canonical_domain": c.canonical_domain,
                "industry": c.industry,
                "country": c.country,
                "sales_stage": c.sales_stage,
                "lead_score": c.lead_score,
                "lead_priority": c.lead_priority,
                "public_email": c.public_email,
                "phone_number": c.phone_number
            }
            for c in leads
        ]
    }


# =========================================================================
# 5. AI Intelligence Assistant ("ProspectOS Intelligence")
# =========================================================================

@router.post("/assistant/chat", response_model=AIAssistantQueryResponse)
async def query_assistant(req: AIAssistantQueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Answers natural language queries about the user's CRM leads.
    Queries the actual database, surfaces real matching prospects, and provides actionable insights.
    """
    svc = CRMAssistantService(db)
    return await svc.query_intelligence(req)


# =========================================================================
# 6. Adaptive AI Learning & Preferences
# =========================================================================

@router.get("/learning/insights")
async def get_adaptive_learning_insights(db: AsyncSession = Depends(get_db)):
    """Returns explainable insights into learned reviewer preferences, weight shifts, and recent feedback."""
    svc = AdaptiveLearningService(db)
    return await svc.get_adaptive_insights()


@router.post("/learning/reset")
async def reset_adaptive_learning(db: AsyncSession = Depends(get_db)):
    """Resets learned scoring weights and user preferences back to default balanced settings."""
    svc = AdaptiveLearningService(db)
    pref = await svc.reset_preferences()
    return {"success": True, "message": "Learned scoring weights reset to factory defaults."}


# =========================================================================
# 7. CRM Analytics Dashboard
# =========================================================================

@router.get("/analytics/dashboard")
async def get_crm_analytics(db: AsyncSession = Depends(get_db)):
    """
    Real-time database aggregated CRM analytics:
    Stage distributions, priority distribution, top countries, top industries, score buckets.
    """
    # Total prospects
    total_leads = (await db.execute(select(func.count(Company.id)))).scalar() or 0

    # Leads by stage
    stage_stmt = select(Company.sales_stage, func.count(Company.id)).group_by(Company.sales_stage)
    stage_rows = (await db.execute(stage_stmt)).all()
    stage_counts = {r[0]: r[1] for r in stage_rows}

    # Leads by priority
    priority_stmt = select(Company.lead_priority, func.count(Company.id)).group_by(Company.lead_priority)
    priority_rows = (await db.execute(priority_stmt)).all()
    priority_counts = {r[0]: r[1] for r in priority_rows}

    # Top countries
    country_stmt = select(Company.country, func.count(Company.id)).where(Company.country != None).group_by(Company.country).order_by(desc(func.count(Company.id))).limit(6)
    country_rows = (await db.execute(country_stmt)).all()
    top_countries = [{"country": r[0], "count": r[1]} for r in country_rows]

    # Top industries
    ind_stmt = select(Company.industry, func.count(Company.id)).where(Company.industry != None).group_by(Company.industry).order_by(desc(func.count(Company.id))).limit(6)
    ind_rows = (await db.execute(ind_stmt)).all()
    top_industries = [{"industry": r[0], "count": r[1]} for r in ind_rows]

    # Score distribution buckets (0-20, 21-40, 41-60, 61-80, 81-100)
    score_buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    scores_stmt = select(Company.lead_score).where(Company.lead_score != None)
    scores = (await db.execute(scores_stmt)).scalars().all()
    for s in scores:
        if s <= 20:
            score_buckets["0-20"] += 1
        elif s <= 40:
            score_buckets["21-40"] += 1
        elif s <= 60:
            score_buckets["41-60"] += 1
        elif s <= 80:
            score_buckets["61-80"] += 1
        else:
            score_buckets["81-100"] += 1

    # Quality indicators
    with_email = (await db.execute(select(func.count(Company.id)).where(Company.public_email != None, Company.public_email != ""))).scalar() or 0
    with_phone = (await db.execute(select(func.count(Company.id)).where(Company.phone_number != None, Company.phone_number != ""))).scalar() or 0
    with_website = (await db.execute(select(func.count(Company.id)).where(Company.website_url != None, Company.website_url != ""))).scalar() or 0

    return {
        "total_leads": total_leads,
        "stage_distribution": stage_counts,
        "priority_distribution": priority_counts,
        "top_countries": top_countries,
        "top_industries": top_industries,
        "score_distribution": score_buckets,
        "data_completeness": {
            "with_email": with_email,
            "with_phone": with_phone,
            "with_website": with_website,
            "email_coverage_percent": round((with_email / max(1, total_leads)) * 100, 1),
            "phone_coverage_percent": round((with_phone / max(1, total_leads)) * 100, 1)
        }
    }


# =========================================================================
# 8. Import & Export Center
# =========================================================================

@router.post("/import-batch")
async def import_leads_batch(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Imports custom batch of leads from mapped CSV or JSON data with deduplication.
    """
    leads_data = payload.get("leads", [])
    if not isinstance(leads_data, list) or not leads_data:
        raise HTTPException(status_code=400, detail="Payload must contain a non-empty 'leads' array")

    added = 0
    updated = 0
    skipped = 0

    for item in leads_data:
        canonical = extract_canonical_domain(item.get("canonical_domain") or item.get("website_url") or item.get("domain"))
        comp_name = item.get("company_name") or item.get("name") or canonical or "Imported Lead"

        existing = None
        if canonical:
            existing = (await db.execute(select(Company).where(Company.canonical_domain == canonical))).scalars().first()

        score_data = {
            "company_name": comp_name,
            "canonical_domain": canonical,
            "website_url": item.get("website_url"),
            "industry": item.get("industry"),
            "country": item.get("country"),
            "city": item.get("city"),
            "description": item.get("description"),
            "public_email": item.get("public_email") or item.get("email"),
            "phone_number": item.get("phone_number") or item.get("phone"),
            "linkedin_url": item.get("linkedin_url"),
        }
        score, breakdown = compute_lead_score(score_data)

        if existing:
            # Update missing
            if not existing.public_email and item.get("email"):
                existing.public_email = item.get("email")
            if not existing.phone_number and item.get("phone"):
                existing.phone_number = item.get("phone")
            existing.last_seen_at = datetime.now(timezone.utc)
            updated += 1
        else:
            new_comp = Company(
                company_name=comp_name,
                canonical_domain=canonical,
                website_url=item.get("website_url"),
                industry=item.get("industry"),
                country=item.get("country"),
                city=item.get("city"),
                description=item.get("description"),
                public_email=item.get("public_email") or item.get("email"),
                phone_number=item.get("phone_number") or item.get("phone"),
                linkedin_url=item.get("linkedin_url"),
                sales_stage="NEW",
                lead_priority="MEDIUM",
                lead_score=score,
                lead_score_components=breakdown,
                lead_source="CSV_IMPORT",
                tags=item.get("tags") or ["csv-import"]
            )
            db.add(new_comp)
            added += 1

    await db.commit()
    return {"success": True, "added": added, "updated": updated, "skipped": skipped}


@router.get("/export-leads")
async def export_crm_leads(
    format: str = Query("csv", pattern="^(csv|json)$"),
    stage: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Exports filtered CRM leads to CSV or JSON format."""
    stmt = select(Company)
    if stage:
        stmt = stmt.where(Company.sales_stage == stage.upper())
    if industry:
        stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
    if country:
        stmt = stmt.where(Company.country.ilike(f"%{country}%"))
    if tag:
        stmt = stmt.where(Company.tags.contains([tag.lower()]))

    stmt = stmt.order_by(desc(Company.lead_score), desc(Company.created_at))
    companies = (await db.execute(stmt)).scalars().all()

    if format == "json":
        data = [
            {
                "id": str(c.id),
                "company_name": c.company_name,
                "canonical_domain": c.canonical_domain,
                "website_url": c.website_url,
                "industry": c.industry,
                "country": c.country,
                "city": c.city,
                "sales_stage": c.sales_stage,
                "lead_score": c.lead_score,
                "lead_priority": c.lead_priority,
                "public_email": c.public_email,
                "phone_number": c.phone_number,
                "linkedin_url": c.linkedin_url,
                "tags": c.tags or [],
                "created_at": c.created_at.isoformat()
            }
            for c in companies
        ]
        return Response(content=json.dumps(data, indent=2), media_type="application/json")

    # CSV Format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Company Name", "Domain", "Website", "Industry", "Country", "City",
        "Stage", "Score", "Priority", "Email", "Phone", "LinkedIn", "Tags"
    ])
    for c in companies:
        writer.writerow([
            str(c.id),
            c.company_name or "",
            c.canonical_domain or "",
            c.website_url or "",
            c.industry or "",
            c.country or "",
            c.city or "",
            c.sales_stage or "",
            c.lead_score or "",
            c.lead_priority or "",
            c.public_email or "",
            c.phone_number or "",
            c.linkedin_url or "",
            ", ".join(c.tags or [])
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=prospectos_crm_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


# =========================================================================
# 9. Legacy / Existing Pipeline Compatibility
# =========================================================================

@router.get("/pipeline/board", response_model=List[PipelineColumn])
async def get_pipeline_board(db: AsyncSession = Depends(get_db)):
    """Returns the complete 11-stage Kanban pipeline board with summary metrics."""
    service = CRMService(db)
    return await service.get_pipeline_board()


@router.get("/prospects")
async def list_crm_prospects(
    stage: Optional[str] = Query(None, description="Filter by sales stage"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    q: Optional[str] = Query(None, description="Search term for company name or domain"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|company_name|stage_updated_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Paginated, searchable, and filterable CRM prospect directory."""
    stmt = select(Company)

    if stage:
        stmt = stmt.where(Company.sales_stage == stage.upper())
    if industry:
        stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
    if q:
        stmt = stmt.where(
            or_(
                Company.company_name.ilike(f"%{q}%"),
                Company.canonical_domain.ilike(f"%{q}%")
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    sort_col = getattr(Company, sort_by)
    if sort_dir == "desc":
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    companies = (await db.execute(stmt)).scalars().all()

    items = []
    for c in companies:
        stmt_opp = select(OpportunityProfile.opportunity_score, OpportunityProfile.recommended_service).where(
            OpportunityProfile.company_id == c.id
        ).order_by(desc(OpportunityProfile.created_at)).limit(1)
        opp_row = (await db.execute(stmt_opp)).first()

        stmt_d = select(func.count(CRMDeal.id), func.coalesce(func.sum(CRMDeal.estimated_value), 0.0)).where(
            CRMDeal.company_id == c.id,
            CRMDeal.stage.notin_(["WON", "LOST"])
        )
        d_row = (await db.execute(stmt_d)).first()

        items.append(
            UnifiedProspectSummary(
                id=c.id,
                company_name=c.company_name or c.canonical_domain or "Unnamed Prospect",
                canonical_domain=c.canonical_domain,
                website_url=c.website_url,
                industry=c.industry,
                target_market=c.target_market,
                sales_stage=c.sales_stage or "NEW",
                stage_updated_at=c.stage_updated_at or c.created_at,
                stage_reason=c.stage_reason,
                opportunity_score=c.lead_score or (opp_row[0] if opp_row else None),
                recommended_service=(c.recommended_services[0] if c.recommended_services else None) or (opp_row[1] if opp_row else None),
                total_deals=d_row[0] if d_row else 0,
                open_deal_value=float(d_row[1]) if d_row else 0.0,
                created_at=c.created_at,
                country=c.country,
                city=c.city,
                public_email=c.public_email,
                phone_number=c.phone_number,
                facebook_url=c.facebook_url,
                instagram_url=c.instagram_url,
                whatsapp_number=c.whatsapp_number,
                whatsapp_click_url=c.whatsapp_click_url,
                gdrive_file_id=c.gdrive_file_id,
                gdrive_file_url=c.gdrive_file_url,
                gdrive_sync_status=c.gdrive_sync_status or "NOT_SYNCED",
                lead_priority=c.lead_priority or "MEDIUM",
                lead_score=c.lead_score,
                lead_score_components=c.lead_score_components,
                recommended_services=c.recommended_services,
                seo_summary_findings=c.seo_summary_findings,
                lead_owner=c.lead_owner
            )
        )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/prospects/{company_id}", response_model=UnifiedProspectDetail)
async def get_prospect_detail(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Unified prospect record linking intelligence, contacts, outreach, deals, tasks, notes, and activity timeline."""
    service = CRMService(db)
    try:
        return await service.get_unified_prospect_detail(company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/prospects/{company_id}/stage")
async def update_prospect_stage(
    company_id: uuid.UUID,
    req: StageUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Moves a prospect between sales pipeline stages with audit logging and adaptive learning update."""
    service = CRMService(db)
    learning_svc = AdaptiveLearningService(db)
    try:
        updated = await service.update_prospect_stage(
            company_id=company_id,
            new_stage=req.new_stage,
            reason=req.reason,
            notes=req.notes,
            actor=req.actor or "human_reviewer"
        )
        # Log to adaptive learning system
        feedback_action = "STAGE_CHANGE"
        if req.new_stage.upper() in ["QUALIFIED", "WON"]:
            feedback_action = "QUALIFIED"
        elif req.new_stage.upper() in ["LOST", "NOT_A_FIT", "NOT_RELEVANT"]:
            feedback_action = "REJECTED"

        await learning_svc.log_user_feedback(
            company_id=company_id,
            action_taken=feedback_action,
            new_stage=req.new_stage.upper(),
            feedback_reason=req.reason or req.notes,
            actor=req.actor or "human_reviewer"
        )

        return {
            "success": True,
            "company_id": str(updated.id),
            "new_stage": updated.sales_stage,
            "stage_updated_at": updated.stage_updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deals", response_model=List[DealResponse])
async def list_deals(
    company_id: Optional[uuid.UUID] = None,
    stage: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMDeal)
    if company_id:
        stmt = stmt.where(CRMDeal.company_id == company_id)
    if stage:
        stmt = stmt.where(CRMDeal.stage == stage.upper())
    stmt = stmt.order_by(desc(CRMDeal.created_at))
    deals = (await db.execute(stmt)).scalars().all()
    return deals


@router.post("/deals", response_model=DealResponse)
async def create_deal(
    data: DealCreate,
    actor: str = Query("human_reviewer"),
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.create_deal(data, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    deal = await db.get(CRMDeal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.put("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.update_deal(deal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    company_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    overdue_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMTask)
    if company_id:
        stmt = stmt.where(CRMTask.company_id == company_id)
    if status:
        stmt = stmt.where(CRMTask.status == status.upper())
    if priority:
        stmt = stmt.where(CRMTask.priority == priority.upper())
    if task_type:
        stmt = stmt.where(CRMTask.task_type == task_type.upper())
    if overdue_only:
        stmt = stmt.where(
            CRMTask.status.in_(["PENDING", "IN_PROGRESS"]),
            CRMTask.due_date < func.now()
        )
    stmt = stmt.order_by(CRMTask.due_date.asc().nulls_last(), desc(CRMTask.created_at))
    tasks = (await db.execute(stmt)).scalars().all()
    return tasks


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    actor: str = Query("human_reviewer"),
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.create_task(data, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: uuid.UUID,
    req: TaskCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.complete_task(task_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/prospects/{company_id}/notes", response_model=NoteResponse)
async def add_prospect_note(
    company_id: uuid.UUID,
    req: NoteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = CRMService(db)
    try:
        return await service.add_note(company_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prospects/{company_id}/activities", response_model=List[ActivityResponse])
async def list_prospect_activities(
    company_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CRMActivity).where(CRMActivity.company_id == company_id).order_by(desc(CRMActivity.created_at)).limit(limit)
    activities = (await db.execute(stmt)).scalars().all()
    return activities


@router.get("/reports/metrics", response_model=CRMReportMetrics)
async def get_crm_report_metrics(db: AsyncSession = Depends(get_db)):
    """Aggregates sales pipeline metrics, revenue, conversion rates, and audit data."""
    service = CRMService(db)
    return await service.get_crm_metrics()
