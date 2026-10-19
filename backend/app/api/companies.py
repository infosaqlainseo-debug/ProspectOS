import uuid
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from pydantic import BaseModel
from arq import create_pool

from app.db.session import get_db
from app.models import Company, WebsiteScan, Evidence, Source, Discovery, CRMActivity, Job
from app.utils.url import normalize_url, extract_canonical_domain
from app.core.redis import get_redis_settings

logger = logging.getLogger(__name__)

router = APIRouter()


class CompanyImportRequest(BaseModel):
    domain: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    sales_stage: Optional[str] = "NEW"
    trigger_analysis: bool = False


def format_company(comp: Company) -> Dict[str, Any]:
    return {
        "id": str(comp.id),
        "company_name": comp.company_name,
        "name": comp.company_name or comp.canonical_domain,
        "canonical_domain": comp.canonical_domain,
        "normalized_domain": comp.canonical_domain,
        "website_url": comp.website_url or (f"https://{comp.canonical_domain}" if comp.canonical_domain else None),
        "industry": comp.industry,
        "sales_stage": comp.sales_stage,
        "target_market": comp.target_market,
        "country": comp.country,
        "city": comp.city,
        "created_at": comp.created_at.isoformat() if comp.created_at else None,
        "updated_at": comp.updated_at.isoformat() if comp.updated_at else None,
        "first_discovered_at": comp.first_discovered_at.isoformat() if comp.first_discovered_at else None,
    }


@router.get("/")
async def list_companies(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    industry: Optional[str] = None,
    sales_stage: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|company_name|canonical_domain|sales_stage)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists companies with multi-field search, filtering, sorting, and pagination.
    """
    stmt = select(Company)

    if q:
        search_filter = f"%{q.strip()}%"
        stmt = stmt.where(
            Company.company_name.ilike(search_filter) |
            Company.canonical_domain.ilike(search_filter)
        )

    if industry and industry.upper() != "ALL":
        stmt = stmt.where(Company.industry.ilike(f"%{industry.strip()}%"))

    if sales_stage and sales_stage.upper() != "ALL":
        stmt = stmt.where(Company.sales_stage == sales_stage.strip())

    # Count total matching
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sorting
    sort_col = getattr(Company, sort_by, Company.created_at)
    if sort_order == "desc":
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(asc(sort_col))

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    companies = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [format_company(c) for c in companies]
    }


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_company(
    req: CompanyImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Directly intakes and normalizes a real prospect domain into ProspectOS catalog.
    Enforces deduplication: returns existing company if domain is already present.
    """
    domain_input = req.domain.strip()
    if not domain_input:
        raise HTTPException(status_code=400, detail="Domain string is required")

    canonical = extract_canonical_domain(normalize_url(domain_input))
    if not canonical:
        raise HTTPException(status_code=400, detail="Invalid domain or URL format")

    # Check deduplication
    existing_stmt = select(Company).where(Company.canonical_domain == canonical)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if existing:
        return {
            "status": "EXISTS",
            "is_duplicate": True,
            "message": f"Company with domain '{canonical}' is already in ProspectOS intelligence catalog.",
            "company": format_company(existing)
        }

    # Generate title/name if omitted
    display_name = req.company_name.strip() if req.company_name else canonical.split(".")[0].replace("-", " ").title()

    comp = Company(
        company_name=display_name,
        canonical_domain=canonical,
        website_url=f"https://{canonical}",
        industry=req.industry.strip() if req.industry else None,
        sales_stage=req.sales_stage or "NEW"
    )
    db.add(comp)
    await db.flush()

    # Link to Source & Discovery
    src_stmt = select(Source).where(Source.name == "Direct Intake / Catalog Import")
    src = (await db.execute(src_stmt)).scalar_one_or_none()
    if not src:
        src = Source(
            name="Direct Intake / Catalog Import",
            source_type="DIRECT_IMPORT",
            description="Manual UI or API prospect intake with domain normalization"
        )
        db.add(src)
        await db.flush()

    discovery = Discovery(
        company_id=comp.id,
        source_id=src.id,
        discovery_method="direct_import",
        query=domain_input,
        confidence=1.0
    )
    db.add(discovery)

    # Record CRM activity audit trail
    act = CRMActivity(
        company_id=comp.id,
        activity_type="PROSPECT_CREATED",
        title=f"Prospect Ingested: {display_name}",
        details={"domain": canonical, "industry": req.industry or "Unspecified"},
        actor="operator"
    )
    db.add(act)

    await db.commit()
    await db.refresh(comp)

    # Optional background analysis trigger
    job_id = None
    if req.trigger_analysis:
        try:
            job = Job(job_type="website_analysis", status="QUEUED")
            db.add(job)
            await db.commit()
            await db.refresh(job)
            job_id = str(job.id)

            redis = await create_pool(get_redis_settings())
            await redis.enqueue_job("website_analysis_job", job_id, str(comp.id))
            if hasattr(redis, "aclose"):
                await redis.aclose()
            else:
                await redis.close()
        except Exception as e:
            logger.warning(f"Could not enqueue website analysis job: {e}")

    return {
        "status": "CREATED",
        "is_duplicate": False,
        "message": f"Successfully imported prospect '{display_name}' ({canonical}).",
        "company": format_company(comp),
        "analysis_job_id": job_id
    }


@router.get("/{company_id}")
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full company details by ID.
    """
    try:
        uid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")

    company = await db.get(Company, uid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return format_company(company)


@router.get("/{company_id}/evidence")
async def get_company_evidence(company_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns verified evidence items and provenance for a prospect company.
    """
    try:
        uid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")

    stmt = select(Evidence).where(Evidence.company_id == uid).order_by(Evidence.created_at.desc())
    result = await db.execute(stmt)
    evidence_list = result.scalars().all()

    return {"company_id": company_id, "evidence": evidence_list}
