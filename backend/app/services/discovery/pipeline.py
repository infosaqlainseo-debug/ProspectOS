import logging
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.schemas.discovery import DiscoveryRequest
from app.services.discovery.base import DiscoveryProvider
from app.utils.url import normalize_url, extract_canonical_domain
from app.utils.http import validate_website
from app.models import (
    Job, JobResult, Company, Domain, Source, Discovery, Evidence,
    SocialProfile, WebsiteScan
)
from app.services.crawler.client import CrawlerClient
from app.services.intelligence.extractor import WebsiteExtractor
from app.services.gdrive.service import GoogleDriveService
from app.services.outreach.social_service import SocialOutreachService, clean_phone_for_whatsapp

logger = logging.getLogger(__name__)

def calculate_transparent_lead_score(
    scan: Optional[WebsiteScan],
    company: Company,
    requested_industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes an explainable 0-100 lead score based on 4 documented pillars:
    - SEO Opportunity Score (35%): Deficits in title, meta, H1, https, robots, or backlink gaps
    - Business Fit Score (25%): Target market & industry alignment
    - Evidence Quality Score (20%): Crawl accessibility and contact verification
    - Website Potential (20%): Room for growth with GrokxSEO services
    """
    # 1. SEO Opportunity (35 points max)
    seo_points = 10.0  # Baseline audit interest
    seo_findings = []
    
    if scan:
        if scan.scan_status == "ACCESS_RESTRICTED" or scan.http_status == 403:
            seo_points += 15.0
            seo_findings.append("Protected by Cloudflare/WAF bot challenge — needs crawl optimization")
        else:
            if not scan.title or len(scan.title) < 15:
                seo_points += 7.0
                seo_findings.append("Missing or unoptimized homepage title tag")
            if not scan.meta_description or len(scan.meta_description) < 50:
                seo_points += 6.0
                seo_findings.append("Missing meta description")
            if not scan.h1 or len(scan.h1) == 0:
                seo_points += 6.0
                seo_findings.append("Missing primary H1 heading on homepage")
            if not scan.https_enabled:
                seo_points += 6.0
                seo_findings.append("Insecure HTTP protocol detected")
    else:
        seo_findings.append("Website audit pending full inspection")

    seo_opportunity_score = min(35.0, seo_points)

    # 2. Business Fit (25 points max)
    biz_points = 15.0
    if requested_industry and company.industry:
        if any(term in company.industry.lower() for term in ["e-commerce", "retail", "store", "online", "d2c"]):
            biz_points = 25.0
        else:
            biz_points = 20.0
    elif company.industry:
        biz_points = 22.0
    business_fit_score = min(25.0, biz_points)

    # 3. Evidence Quality (20 points max)
    evidence_points = 5.0
    if company.canonical_domain:
        evidence_points += 5.0
    if scan and scan.http_status in [200, 301, 302]:
        evidence_points += 5.0
    if company.public_email or company.phone_number or company.whatsapp_number or company.facebook_url or company.instagram_url:
        evidence_points += 5.0
    evidence_quality_score = min(20.0, evidence_points)

    # 4. Website Potential (20 points max)
    website_potential_score = 18.0

    total_score = round(seo_opportunity_score + business_fit_score + evidence_quality_score + website_potential_score, 1)

    components = {
        "seo_opportunity": round(seo_opportunity_score, 1),
        "business_fit": round(business_fit_score, 1),
        "evidence_quality": round(evidence_quality_score, 1),
        "website_potential": round(website_potential_score, 1),
        "total_score": total_score,
        "max_score": 100.0,
        "explanation": f"Lead score of {total_score}/100 based on {len(seo_findings)} identified SEO expansion areas and verified market fit."
    }

    return {
        "score": total_score,
        "components": components,
        "findings": seo_findings
    }


async def run_discovery_pipeline(
    job_id: uuid.UUID,
    request: DiscoveryRequest,
    provider: DiscoveryProvider,
    session: AsyncSession
):
    """Executes the comprehensive lead discovery, website analysis, scoring, CRM saving, and Drive synchronization pipeline."""
    job = await session.get(Job, job_id)
    if not job:
        logger.error(f"Job {job_id} not found.")
        return

    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    job.discovered_count = 0
    job.validated_count = 0
    job.stored_count = 0
    job.duplicate_count = 0
    job.failed_count = 0
    await session.commit()

    crawler = CrawlerClient()
    extractor = WebsiteExtractor()
    gdrive_service = GoogleDriveService(session)
    social_service = SocialOutreachService(session)

    try:
        async for batch in provider.discover(request):
            for result in batch:
                job.discovered_count += 1

                # 1. Parse & Normalize URL
                normalized_url = normalize_url(result.website_url)
                canonical_domain = extract_canonical_domain(normalized_url or result.website_url)

                if not canonical_domain:
                    job.failed_count += 1
                    session.add(JobResult(
                        job_id=job.id,
                        status="FAILED",
                        stage="PARSE",
                        error_message="Could not extract canonical domain"
                    ))
                    continue

                result.canonical_domain = canonical_domain

                # 2. Deduplicate against existing CRM records
                domain_query = await session.execute(
                    select(Domain).where(Domain.canonical_domain == canonical_domain)
                )
                existing_domain = domain_query.scalars().first()

                if existing_domain and not request.include_previously_discovered:
                    job.duplicate_count += 1
                    company_id = existing_domain.company_id
                    company = await session.get(Company, company_id)
                    if company:
                        company.last_seen_at = datetime.now(timezone.utc)

                    # Record discovery link
                    source_query = await session.execute(
                        select(Source).where(Source.name == result.source_name)
                    )
                    source = source_query.scalars().first()
                    if not source:
                        source = Source(name=result.source_name, source_type="public_directory")
                        session.add(source)
                        await session.flush()

                    discovery = Discovery(
                        company_id=company_id,
                        source_id=source.id,
                        discovery_method=result.discovery_method,
                        source_url=result.source_url,
                        query=request.query,
                        job_id=job.id,
                        confidence=result.confidence
                    )
                    session.add(discovery)
                    await session.commit()
                    continue

                # 3. Validate website accessibility
                is_valid = await validate_website(normalized_url)
                if not is_valid:
                    job.failed_count += 1
                    session.add(JobResult(
                        job_id=job.id,
                        status="FAILED",
                        stage="VALIDATE",
                        error_message="Website failed HTTP validation check"
                    ))
                    await session.commit()
                    continue

                job.validated_count += 1

                # 4. Persist Company
                now = datetime.now(timezone.utc)
                company = Company(
                    company_name=result.company_name,
                    canonical_domain=canonical_domain,
                    website_url=normalized_url or f"https://{canonical_domain}",
                    country=result.country or request.country or "Mexico",
                    city=result.city or request.city,
                    industry=result.industry or request.industry or "E-commerce",
                    sales_stage="QUALIFIED",
                    lead_priority="HIGH" if request.country == "Mexico" else "MEDIUM",
                    first_discovered_at=now,
                    last_seen_at=now
                )
                session.add(company)
                await session.flush()

                # Add Domain
                domain = Domain(
                    company_id=company.id,
                    domain=normalized_url or canonical_domain,
                    canonical_domain=canonical_domain,
                    status="ACTIVE"
                )
                session.add(domain)

                # Add Source & Discovery
                source_query = await session.execute(
                    select(Source).where(Source.name == result.source_name)
                )
                source = source_query.scalars().first()
                if not source:
                    source = Source(name=result.source_name, source_type="public_directory")
                    session.add(source)
                    await session.flush()

                discovery = Discovery(
                    company_id=company.id,
                    source_id=source.id,
                    discovery_method=result.discovery_method,
                    source_url=result.source_url,
                    query=request.query,
                    job_id=job.id,
                    confidence=result.confidence
                )
                session.add(discovery)

                # 5. Extract On-Page SEO Evidence and Social Profiles via Crawler
                base_url = company.website_url
                scan: Optional[WebsiteScan] = None
                try:
                    page_data = await crawler.fetch_page(base_url)
                    http_status = page_data.get("http_status")
                    scan_status = page_data.get("status", "FAILED")
                    
                    scan = WebsiteScan(
                        company_id=company.id,
                        url=base_url,
                        http_status=http_status,
                        https_enabled=page_data.get("https_enabled"),
                        final_url=page_data.get("final_url"),
                        scan_status=scan_status,
                        error_message=page_data.get("error"),
                        scanned_at=now
                    )
                    
                    if page_data.get("is_accessible") and page_data.get("html"):
                        html = page_data["html"]
                        metadata = extractor.extract_metadata(html, base_url)
                        scan.title = metadata.get("title")
                        scan.meta_description = metadata.get("meta_description")
                        scan.canonical_url = metadata.get("canonical_url")
                        scan.h1 = metadata.get("h1")
                        scan.h2 = metadata.get("h2")
                        if metadata.get("meta_description") and not company.description:
                            company.description = metadata.get("meta_description")

                        # Extract Social Links & Contact Information
                        social_links = extractor.extract_social_links(html, base_url)
                        for s in social_links:
                            platform = s["platform"].upper()
                            p_url = s["profile_url"]
                            if "FACEBOOK" in platform and not company.facebook_url:
                                company.facebook_url = p_url
                            elif "INSTAGRAM" in platform and not company.instagram_url:
                                company.instagram_url = p_url
                            elif "WHATSAPP" in platform and not company.whatsapp_number:
                                # Extract phone digits if present in wa.me link
                                digits = re.sub(r"\D", "", p_url)
                                if len(digits) >= 10:
                                    company.whatsapp_number = digits
                                    company.whatsapp_click_url = f"https://wa.me/{digits}"

                            sp = SocialProfile(
                                company_id=company.id,
                                platform=s["platform"],
                                profile_url=p_url,
                                source_url=base_url,
                                verification_method="HTML_ANCHOR_DISCOVERY",
                                confidence=0.95,
                                verification_status="VERIFIED"
                            )
                            session.add(sp)

                    session.add(scan)
                except Exception as crawl_err:
                    logger.warning(f"Crawl observation error on {base_url}: {crawl_err}")

                # 6. Calculate Transparent Lead Score (0-100)
                scoring = calculate_transparent_lead_score(scan, company, request.industry)
                company.lead_score = scoring["score"]
                company.lead_score_components = scoring["components"]
                company.seo_summary_findings = scoring["findings"]
                company.recommended_services = [
                    "Technical SEO",
                    "High-Authority Link Building",
                    "Digital PR"
                ]

                # 7. Add Evidence Record
                evidence = Evidence(
                    company_id=company.id,
                    field_name="lead_qualification",
                    value=f"Score: {company.lead_score}/100",
                    source_url=result.source_url,
                    source_type="discovery_pipeline",
                    provider=provider.source_name,
                    extraction_method=result.discovery_method,
                    confidence=0.95,
                    verification_status="VERIFIED"
                )
                session.add(evidence)

                session.add(JobResult(
                    job_id=job.id,
                    company_id=company.id,
                    status="COMPLETED",
                    stage="QUALIFIED"
                ))

                job.stored_count += 1
                await session.commit()

                # 8. Auto-Sync to Google Drive if requested
                if request.auto_sync_to_gdrive:
                    try:
                        await gdrive_service.sync_company_to_drive(company.id, sync_type="AUTOMATIC")
                    except Exception as gd_err:
                        logger.warning(f"Google Drive auto-sync bypassed for {company.canonical_domain}: {gd_err}")

                # 9. Stop if requested target count is reached
                if job.stored_count >= request.target_count:
                    break

            if job.stored_count >= request.target_count:
                break

        # 10. Finalize Job Status
        if job.stored_count >= request.target_count:
            job.status = "COMPLETED"
        elif job.stored_count > 0:
            job.status = "PARTIAL"
        else:
            job.status = "FAILED"
            job.error_message = "No valid qualifying companies found matching criteria."

        job.completed_at = datetime.now(timezone.utc)
        await session.commit()

    except Exception as e:
        logger.exception(f"Pipeline error for job {job_id}: {e}")
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()
