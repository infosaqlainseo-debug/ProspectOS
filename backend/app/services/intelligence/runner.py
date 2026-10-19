from typing import Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, desc
from app.db.session import async_session_maker
from app.models import Company, WebsiteScan, SocialProfile, Evidence, PublisherRecord
from app.services.crawler.client import CrawlerClient
from app.services.intelligence.extractor import WebsiteExtractor

logger = logging.getLogger(__name__)

class WebsiteIntelligenceRunner:
    def __init__(self):
        self.crawler = CrawlerClient()
        self.extractor = WebsiteExtractor()

    async def analyze_company(self, company_id: uuid.UUID) -> str:
        async with async_session_maker() as session:
            company = await session.get(Company, company_id)
            if not company:
                logger.error(f"Company {company_id} not found.")
                return "FAILED"
                
            if not company.website_url:
                if company.canonical_domain:
                    company.website_url = f"https://{company.canonical_domain}"
                    await session.commit()
                else:
                    logger.error(f"Company {company_id} has no website_url or canonical_domain.")
                    return "FAILED"

            base_url = company.website_url
            if not base_url.startswith("http"):
                base_url = "https://" + base_url

            now_utc = datetime.now(timezone.utc)

            # 1. Fetch robots.txt with policy enforcement
            robots_status, robots_content, allowed = await self.crawler.fetch_robots_txt(base_url)
            if not allowed:
                scan = WebsiteScan(
                    company_id=company.id,
                    url=base_url,
                    http_status=None,
                    robots_txt_status="DISALLOWED",
                    scan_status="BLOCKED_BY_ROBOTS_TXT",
                    error_message="Robots.txt disallows crawling by ProspectOS-Crawler",
                    scanned_at=now_utc
                )
                session.add(scan)
                await session.commit()
                logger.warning(f"Crawling disallowed by robots.txt for {base_url}")
                return scan.scan_status
            
            # 2. Fetch homepage
            page_data = await self.crawler.fetch_page(base_url)
            is_accessible = page_data.get("is_accessible", False)
            http_status = page_data.get("http_status")
            status = page_data.get("status", "FAILED")
            failure_reason = page_data.get("failure_reason")
            
            # Create a WebsiteScan
            scan = WebsiteScan(
                company_id=company.id,
                url=base_url,
                http_status=http_status,
                https_enabled=page_data.get("https_enabled"),
                final_url=page_data.get("final_url"),
                redirect_chain=page_data.get("redirect_chain"),
                robots_txt_status=robots_status,
                scan_status=status,
                error_message=page_data.get("error"),
                scanned_at=now_utc
            )
            
            if is_accessible and page_data.get("html"):
                html = page_data["html"]
                headers = page_data.get("headers", {})
                
                # Extract deterministic metadata from valid HTTP 200 HTML
                metadata = self.extractor.extract_metadata(html, base_url)
                
                scan.title = metadata.get("title")
                scan.meta_description = metadata.get("meta_description")
                scan.canonical_url = metadata.get("canonical_url")
                scan.robots_meta = metadata.get("robots_meta")
                scan.viewport = metadata.get("viewport")
                scan.language = metadata.get("language")
                scan.charset = metadata.get("charset")
                scan.h1 = metadata.get("h1")
                scan.h2 = metadata.get("h2")
                scan.open_graph = metadata.get("open_graph")
                scan.twitter_card = metadata.get("twitter_card")
                scan.schema_detected = metadata.get("schema_detected")
                scan.technology_signals = self.extractor.detect_technologies(html, headers)
                
                # Social Links
                social_links = self.extractor.extract_social_links(html, base_url)
                if not company.description and scan.meta_description:
                    company.description = scan.meta_description
                    
                # Save Social Profiles & Evidence
                for s in social_links:
                    existing = (await session.execute(
                        select(SocialProfile)
                        .where(SocialProfile.company_id == company.id)
                        .where(SocialProfile.profile_url == s["profile_url"])
                    )).scalars().first()
                    
                    if not existing:
                        sp = SocialProfile(
                            company_id=company.id,
                            platform=s["platform"],
                            profile_url=s["profile_url"],
                            source_url=s["source_url"],
                            verification_method=s["verification_method"],
                            confidence=s["confidence"],
                            verification_status="VERIFIED"
                        )
                        session.add(sp)
                        
                        ev = Evidence(
                            company_id=company.id,
                            source_type="HTML_LINK",
                            field_name="profile_url",
                            value=s["profile_url"],
                            provider="website_intelligence",
                            extraction_method="HTML_LINK_EXTRACTION",
                            source_url=s["source_url"],
                            confidence=s["confidence"],
                            verification_status="VERIFIED",
                            retrieved_at=now_utc
                        )
                        session.add(ev)
            else:
                # Crawl Inaccessible / Restricted: Never extract or fabricate from block pages
                scan.title = None
                scan.meta_description = None
                scan.canonical_url = None
                scan.robots_meta = None
                scan.h1 = None
                scan.h2 = None
                scan.schema_detected = None
                scan.technology_signals = {
                    "is_accessible": False,
                    "failure_reason": failure_reason,
                    "status_code": http_status,
                    "server": page_data.get("headers", {}).get("server")
                }
                
                # -------------------------------------------------------------
                # Permitted Evidence Fallback Execution
                # -------------------------------------------------------------
                # Fallback A: Fresh historical website evidence (< 30 days)
                stmt_hist = select(WebsiteScan).where(
                    WebsiteScan.company_id == company.id,
                    WebsiteScan.http_status == 200,
                    WebsiteScan.scan_status == "COMPLETED",
                    WebsiteScan.scanned_at >= (now_utc - timedelta(days=30))
                ).order_by(desc(WebsiteScan.scanned_at)).limit(1)
                hist_scan = (await session.execute(stmt_hist)).scalar_one_or_none()
                
                if hist_scan and hist_scan.title:
                    ev_hist_title = Evidence(
                        company_id=company.id,
                        source_type="HISTORICAL_WEBSITE_SCAN",
                        field_name="historical_page_title",
                        value=hist_scan.title,
                        provider="website_intelligence_archive",
                        source_url=hist_scan.url,
                        confidence=0.75,
                        verification_status="VERIFIED_HISTORICAL",
                        raw_reference={
                            "prior_scan_id": str(hist_scan.id),
                            "original_scanned_at": hist_scan.scanned_at.isoformat() if hist_scan.scanned_at else None,
                            "fallback_applied": True
                        },
                        retrieved_at=now_utc
                    )
                    session.add(ev_hist_title)
                
                # Fallback B: Authorized Company and Publisher Catalog Records
                if company.company_name:
                    ev_identity = Evidence(
                        company_id=company.id,
                        source_type="AUTHORIZED_CATALOG_FEED",
                        field_name="company_identity",
                        value=company.company_name,
                        provider="authorized_catalog_inventory",
                        source_url=base_url,
                        confidence=0.90,
                        verification_status="VERIFIED",
                        raw_reference={"source": "authorized_inventory_import"},
                        retrieved_at=now_utc
                    )
                    session.add(ev_identity)
                    
                stmt_pub = select(PublisherRecord).where(PublisherRecord.company_id == company.id).limit(1)
                pub = (await session.execute(stmt_pub)).scalar_one_or_none()
                if pub and pub.audience_focus:
                    ev_audience = Evidence(
                        company_id=company.id,
                        source_type="AUTHORIZED_CATALOG_FEED",
                        field_name="audience_focus",
                        value=pub.audience_focus,
                        provider="authorized_catalog_inventory",
                        source_url=base_url,
                        confidence=0.85,
                        verification_status="VERIFIED",
                        raw_reference={"publisher_record_id": str(pub.id)},
                        retrieved_at=now_utc
                    )
                    session.add(ev_audience)
                    
                # Fallback C: Explicitly record on-page content as UNAVAILABLE / UNVERIFIED
                ev_unavail = Evidence(
                    company_id=company.id,
                    source_type="RESTRICTED_CRAWL",
                    field_name="on_page_seo_content",
                    value="UNAVAILABLE",
                    provider="prospectos_crawler",
                    source_url=base_url,
                    confidence=0.0,
                    verification_status="UNVERIFIED",
                    raw_reference={
                        "http_status": http_status,
                        "failure_reason": failure_reason,
                        "explanation": "Target website challenged automated crawler; on-page content cannot be verified without manual or permitted browser inspection."
                    },
                    retrieved_at=now_utc
                )
                session.add(ev_unavail)

            session.add(scan)
            await session.commit()
            return scan.scan_status
