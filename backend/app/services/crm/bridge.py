import uuid
import re
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from app.models import Company, CRMActivity
from app.models.scraper import ExtractedRecord, ScraperTask
from app.schemas.crm import ScraperImportRequest, ScraperImportResponse

logger = logging.getLogger(__name__)


def extract_canonical_domain(url_or_domain: str | None) -> str | None:
    if not url_or_domain:
        return None
    raw = url_or_domain.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        domain = parsed.netloc or parsed.path
        domain = domain.split(":")[0]  # strip port
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.strip() if domain else None
    except Exception:
        clean = re.sub(r"^https?://(www\.)?", "", raw).split("/")[0].split(":")[0]
        return clean if clean else None


def compute_lead_score(data: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
    """
    Computes a transparent 0-100 lead score based on four pillars:
    1. Contact Reachability (0-30 pts)
    2. Data Completeness & Business Profile (0-25 pts)
    3. Website Viability & Digital Presence (0-25 pts)
    4. SEO Growth Opportunity (0-20 pts)
    """
    score = 0.0
    breakdown = {}

    # Pillar 1: Contact Reachability
    reachability = 0.0
    has_email = bool(data.get("public_email") or data.get("email"))
    has_phone = bool(data.get("phone_number") or data.get("phone"))
    has_linkedin = bool(data.get("linkedin_url") or data.get("linkedin"))
    has_contact_page = bool(data.get("contact_page_url"))
    if has_email:
        reachability += 15.0
    if has_phone:
        reachability += 8.0
    if has_linkedin:
        reachability += 5.0
    if has_contact_page:
        reachability += 2.0
    score += reachability
    breakdown["contact_reachability"] = {
        "score": round(reachability, 1),
        "max": 30.0,
        "signals": {
            "has_email": has_email,
            "has_phone": has_phone,
            "has_linkedin": has_linkedin,
            "has_contact_page": has_contact_page,
        }
    }

    # Pillar 2: Data Completeness & Business Profile
    profile = 0.0
    has_name = bool(data.get("company_name"))
    has_industry = bool(data.get("industry"))
    has_country = bool(data.get("country"))
    has_desc = bool(data.get("description") and len(str(data.get("description", ""))) > 20)
    has_city = bool(data.get("city"))
    if has_name:
        profile += 7.0
    if has_industry:
        profile += 6.0
    if has_country:
        profile += 5.0
    if has_desc:
        profile += 4.0
    if has_city:
        profile += 3.0
    score += profile
    breakdown["profile_completeness"] = {
        "score": round(profile, 1),
        "max": 25.0,
        "signals": {
            "has_name": has_name,
            "has_industry": has_industry,
            "has_country": has_country,
            "has_description": has_desc,
            "has_city": has_city,
        }
    }

    # Pillar 3: Website Viability
    website = 0.0
    has_website = bool(data.get("website_url") or data.get("canonical_domain"))
    if has_website:
        website += 15.0
    # Social presence
    socials = sum([
        bool(data.get("facebook_url")),
        bool(data.get("instagram_url")),
        bool(data.get("whatsapp_number"))
    ])
    website += min(10.0, socials * 4.0)
    score += website
    breakdown["website_viability"] = {
        "score": round(website, 1),
        "max": 25.0,
        "signals": {
            "has_website": has_website,
            "social_channels_count": socials
        }
    }

    # Pillar 4: SEO Growth Opportunity
    seo = 0.0
    # If domain exists and company is an SMB without massive enterprise saturation, high opportunity
    if has_website:
        seo += 15.0
    # If technology stack or category detected
    if data.get("industry"):
        seo += 5.0
    score += seo
    breakdown["seo_opportunity"] = {
        "score": round(seo, 1),
        "max": 20.0,
        "signals": {
            "seo_audit_eligible": has_website,
            "target_niche_identified": bool(data.get("industry"))
        }
    }

    total_score = min(100.0, max(0.0, round(score, 1)))
    return total_score, breakdown


class ScraperCRMBridge:
    """Bridge service connecting ProspectOS Scraper extractions to the persistent CRM Lead Database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def import_extracted_records(self, req: ScraperImportRequest) -> ScraperImportResponse:
        query = select(ExtractedRecord)

        if req.extracted_record_ids:
            query = query.where(ExtractedRecord.id.in_(req.extracted_record_ids))
        elif req.task_id:
            query = query.where(ExtractedRecord.task_id == req.task_id)
        else:
            # Fallback: latest 100 valid records
            query = query.order_by(desc(ExtractedRecord.created_at)).limit(100)

        if req.auto_save_valid_only:
            query = query.where(ExtractedRecord.validation_status.in_(["VALID", "WARNING", "VALIDATED", "CLEANED"]))

        records = (await self.session.execute(query)).scalars().all()

        added = 0
        updated = 0
        skipped = 0
        flagged = 0
        imported_ids: List[str] = []
        seen_domains_in_batch = set()

        # Task reference name if task_id provided
        task_name = "Scraper Task"
        if req.task_id:
            t = await self.session.get(ScraperTask, req.task_id)
            if t:
                task_name = t.name

        for rec in records:
            data = rec.cleaned_data or rec.raw_data or {}
            canonical = (
                extract_canonical_domain(rec.domain)
                or extract_canonical_domain(rec.website)
                or extract_canonical_domain(data.get("website_url"))
                or extract_canonical_domain(data.get("website"))
                or extract_canonical_domain(data.get("domain"))
                or extract_canonical_domain(rec.source_url)
            )

            # Fallback identifier if no domain
            comp_name = (
                rec.company_name
                or data.get("company_name")
                or data.get("name")
                or data.get("title")
                or canonical
                or "Unknown Prospect"
            ).strip()

            if not canonical and not comp_name:
                skipped += 1
                continue

            # Batch deduplication
            batch_key = canonical or comp_name.lower()
            if batch_key in seen_domains_in_batch:
                skipped += 1
                continue
            seen_domains_in_batch.add(batch_key)

            # Query existing company in CRM
            existing_company = None
            if canonical:
                stmt = select(Company).where(
                    or_(
                        Company.canonical_domain == canonical,
                        Company.website_url.ilike(f"%{canonical}%")
                    )
                ).limit(1)
                existing_company = (await self.session.execute(stmt)).scalars().first()
            
            if not existing_company and comp_name:
                stmt_name = select(Company).where(Company.company_name.ilike(comp_name)).limit(1)
                existing_company = (await self.session.execute(stmt_name)).scalars().first()

            # Prepare fields
            website_url = rec.website or data.get("website_url") or data.get("website") or (f"https://{canonical}" if canonical else None)
            industry = rec.industry or data.get("industry") or data.get("category")
            country = rec.country or data.get("country") or data.get("location_country")
            city = rec.city or data.get("city") or data.get("location_city")
            state = data.get("state")
            description = rec.description or data.get("description") or data.get("summary") or data.get("about")
            company_size = data.get("company_size") or data.get("size") or data.get("employees")
            contact_person = data.get("contact_person") or data.get("name") or data.get("author")
            contact_title = data.get("contact_title") or data.get("title")
            public_email = rec.email or data.get("public_email") or data.get("email")
            phone_number = rec.phone or data.get("phone_number") or data.get("phone")
            linkedin_url = data.get("linkedin_url") or data.get("linkedin")
            facebook_url = data.get("facebook_url")
            instagram_url = data.get("instagram_url")
            whatsapp_number = data.get("whatsapp_number") or data.get("whatsapp")

            # Merge tags
            combined_tags = list(set(req.tags + (data.get("flags") or [])))
            if industry and industry not in combined_tags:
                combined_tags.append(industry.lower())

            # Calculate score
            score_data = {
                "company_name": comp_name,
                "canonical_domain": canonical,
                "website_url": website_url,
                "industry": industry,
                "country": country,
                "city": city,
                "description": description,
                "public_email": public_email,
                "phone_number": phone_number,
                "linkedin_url": linkedin_url,
                "facebook_url": facebook_url,
                "instagram_url": instagram_url,
                "whatsapp_number": whatsapp_number,
                "contact_page_url": data.get("contact_page_url")
            }
            lead_score, score_components = compute_lead_score(score_data)

            if existing_company:
                # Deduplication & Merge
                if req.conflict_resolution == "SKIP":
                    skipped += 1
                    continue

                # Merge missing data
                if not existing_company.company_name and comp_name:
                    existing_company.company_name = comp_name
                if not existing_company.website_url and website_url:
                    existing_company.website_url = website_url
                if not existing_company.public_email and public_email:
                    existing_company.public_email = public_email
                if not existing_company.phone_number and phone_number:
                    existing_company.phone_number = phone_number
                if not existing_company.linkedin_url and linkedin_url:
                    existing_company.linkedin_url = linkedin_url
                if not existing_company.industry and industry:
                    existing_company.industry = industry
                if not existing_company.country and country:
                    existing_company.country = country
                if not existing_company.city and city:
                    existing_company.city = city
                if not existing_company.description and description:
                    existing_company.description = description
                if not existing_company.company_size and company_size:
                    existing_company.company_size = company_size
                if not existing_company.contact_person and contact_person:
                    existing_company.contact_person = contact_person
                if not existing_company.contact_title and contact_title:
                    existing_company.contact_title = contact_title

                # Append tags
                cur_tags = existing_company.tags or []
                existing_company.tags = list(set(cur_tags + combined_tags))
                existing_company.last_seen_at = datetime.now(timezone.utc)

                # Re-score if higher
                if (existing_company.lead_score or 0) < lead_score:
                    existing_company.lead_score = lead_score
                    existing_company.lead_score_components = score_components

                # Activity log
                activity = CRMActivity(
                    company_id=existing_company.id,
                    activity_type="SCRAPER_MERGED",
                    actor="scraper_bridge",
                    title="Lead Enriched from Scraper Task",
                    details={
                        "task_id": str(rec.task_id) if rec.task_id else None,
                        "task_name": task_name,
                        "record_id": str(rec.id),
                        "source_url": rec.source_url,
                        "conflict_resolution": req.conflict_resolution,
                        "updated_fields": ["last_seen_at", "tags"]
                    }
                )
                self.session.add(activity)
                updated += 1
                imported_ids.append(str(existing_company.id))

            else:
                # Create New CRM Lead
                priority = "MEDIUM"
                if lead_score >= 75.0:
                    priority = "HIGH"
                elif lead_score >= 90.0:
                    priority = "CRITICAL"
                elif lead_score < 40.0:
                    priority = "LOW"

                new_company = Company(
                    company_name=comp_name,
                    canonical_domain=canonical,
                    website_url=website_url,
                    country=country,
                    city=city,
                    state=state,
                    industry=industry,
                    description=description,
                    company_size=company_size,
                    contact_person=contact_person,
                    contact_title=contact_title,
                    public_email=public_email,
                    phone_number=phone_number,
                    linkedin_url=linkedin_url,
                    facebook_url=facebook_url,
                    instagram_url=instagram_url,
                    whatsapp_number=whatsapp_number,
                    sales_stage=req.default_stage.upper(),
                    lead_priority=priority,
                    lead_score=lead_score,
                    lead_score_components=score_components,
                    lead_source=req.lead_source,
                    source_task_id=rec.task_id,
                    tags=combined_tags,
                    custom_fields=data.get("flags") and {"flags": data.get("flags")} or {},
                    data_verification_status="VERIFIED" if rec.validation_status in ["VALID", "CLEANED"] else "UNVERIFIED",
                    first_discovered_at=rec.created_at or datetime.now(timezone.utc),
                    last_seen_at=datetime.now(timezone.utc)
                )
                self.session.add(new_company)
                await self.session.flush()

                # Activity log
                activity = CRMActivity(
                    company_id=new_company.id,
                    activity_type="LEAD_IMPORTED_FROM_SCRAPER",
                    actor="scraper_bridge",
                    title=f"Imported into CRM from {task_name}",
                    details={
                        "task_id": str(rec.task_id) if rec.task_id else None,
                        "task_name": task_name,
                        "record_id": str(rec.id),
                        "source_url": rec.source_url,
                        "initial_score": lead_score,
                        "priority": priority
                    }
                )
                self.session.add(activity)
                added += 1
                imported_ids.append(str(new_company.id))

        await self.session.commit()

        msg = f"Successfully processed {len(records)} records: {added} new leads created, {updated} existing leads merged, {skipped} skipped."
        return ScraperImportResponse(
            success=True,
            total_processed=len(records),
            added=added,
            updated=updated,
            skipped=skipped,
            flagged=flagged,
            imported_ids=imported_ids,
            message=msg
        )
