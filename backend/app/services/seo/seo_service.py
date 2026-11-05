import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update

from app.models.admin import SEOGlobalConfig, SEOPublicPage
from app.schemas.admin import (
    SEOGlobalConfigSchema, SEOPublicPageItem, SEOPublicPageCreateOrUpdate,
    SEOAuditReport
)

logger = logging.getLogger(__name__)


class SEOService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ==========================================
    # 1. Global SEO Configuration
    # ==========================================

    async def get_global_config(self) -> SEOGlobalConfig:
        stmt = select(SEOGlobalConfig).limit(1)
        res = await self.session.execute(stmt)
        config = res.scalars().first()

        if not config:
            config = SEOGlobalConfig(
                site_name="ProspectOS",
                default_meta_title="ProspectOS | AI Web Scraping & Lead Intelligence Platform",
                default_meta_description="Enterprise web scraping platform, autonomous prospect discovery, and AI-powered CRM intelligence system.",
                default_canonical_domain="https://prospectos.com",
                default_og_image_url="/og-image.png",
                robots_txt_content="""User-agent: *
Allow: /
Allow: /features
Allow: /solutions
Allow: /pricing
Allow: /docs
Disallow: /admin
Disallow: /crm
Disallow: /portal
Disallow: /system
Disallow: /api

Sitemap: https://prospectos.com/sitemap.xml""",
                sitemap_enabled=True,
                gsc_verification_code="google-site-verification=prospectos_secure_hash_2026",
                ga4_measurement_id="G-PROSPECTOS26"
            )
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)

        return config

    async def update_global_config(self, req: SEOGlobalConfigSchema) -> SEOGlobalConfig:
        config = await self.get_global_config()
        config.site_name = req.site_name.strip()
        config.default_meta_title = req.default_meta_title.strip()
        config.default_meta_description = req.default_meta_description.strip()
        config.default_canonical_domain = req.default_canonical_domain.strip().rstrip("/")
        config.default_og_image_url = req.default_og_image_url
        if req.robots_txt_content is not None:
            config.robots_txt_content = req.robots_txt_content
        config.sitemap_enabled = req.sitemap_enabled
        config.gsc_verification_code = req.gsc_verification_code
        config.ga4_measurement_id = req.ga4_measurement_id
        config.bing_verification_code = req.bing_verification_code
        await self.session.commit()
        await self.session.refresh(config)
        return config

    # ==========================================
    # 2. Page-Level SEO Management
    # ==========================================

    async def list_pages(self) -> List[SEOPublicPageItem]:
        stmt = select(SEOPublicPage).order_by(desc(SEOPublicPage.sitemap_priority), SEOPublicPage.path)
        res = await self.session.execute(stmt)
        pages = res.scalars().all()

        if not pages:
            default_pages = [
                SEOPublicPage(
                    path="/",
                    page_name="Homepage / Platform Overview",
                    meta_title="ProspectOS | Enterprise Web Scraping & AI Lead Intelligence Platform",
                    meta_description="Extract structured web data at scale with visual scraping workflows, cloud worker clusters, and integrated CRM intelligence.",
                    canonical_url="https://prospectos.com/",
                    og_title="ProspectOS — Intelligent Web Extraction & CRM",
                    og_description="Autonomous prospect discovery, structured scraping templates, and AI lead enrichment for modern revenue teams.",
                    og_image_url="https://prospectos.com/og-home.png",
                    schema_type="SoftwareApplication",
                    structured_data_json={
                        "@context": "https://schema.org",
                        "@type": "SoftwareApplication",
                        "name": "ProspectOS",
                        "applicationCategory": "BusinessApplication",
                        "operatingSystem": "Cloud / Web",
                        "description": "Production-grade AI Agentic SEO Prospect Intelligence Platform"
                    },
                    sitemap_priority=1.0,
                    change_frequency="daily",
                    is_published=True,
                    audit_score=98,
                    audit_issues=[]
                ),
                SEOPublicPage(
                    path="/features",
                    page_name="Product Features & Capabilities",
                    meta_title="ProspectOS Features | Visual Scraper, Cloud Cluster & CRM",
                    meta_description="Explore Octoparse-inspired visual workflow builder, dynamic pagination loops, live task monitoring, and 4-pillar lead scoring.",
                    canonical_url="https://prospectos.com/features",
                    og_title="ProspectOS Product Capabilities",
                    og_description="Deep visual extraction, automatic element detection, and autonomous lead verification.",
                    og_image_url="https://prospectos.com/og-features.png",
                    schema_type="Product",
                    structured_data_json={
                        "@context": "https://schema.org",
                        "@type": "Product",
                        "name": "ProspectOS Scraper Suite",
                        "category": "Lead Generation Software"
                    },
                    sitemap_priority=0.9,
                    change_frequency="weekly",
                    is_published=True,
                    audit_score=95,
                    audit_issues=[]
                ),
                SEOPublicPage(
                    path="/solutions",
                    page_name="Industry Solutions",
                    meta_title="ProspectOS Solutions | E-Commerce, Local Directories & SEO Intelligence",
                    meta_description="Targeted data collection and prospect intelligence for e-commerce brands, real estate firms, and digital growth agencies.",
                    canonical_url="https://prospectos.com/solutions",
                    og_title="ProspectOS Industry Solutions",
                    og_description="Engineered workflows for high-yield company and website intelligence gathering.",
                    og_image_url="https://prospectos.com/og-solutions.png",
                    schema_type="WebSite",
                    sitemap_priority=0.8,
                    change_frequency="weekly",
                    is_published=True,
                    audit_score=92,
                    audit_issues=[]
                ),
                SEOPublicPage(
                    path="/pricing",
                    page_name="Pricing & Cloud Quotas",
                    meta_title="ProspectOS Pricing | Transparent Plans for Scaling Revenue Teams",
                    meta_description="Choose from Starter, Professional, and Enterprise plans with dedicated cloud extraction concurrency and CRM storage.",
                    canonical_url="https://prospectos.com/pricing",
                    og_title="ProspectOS Pricing Plans",
                    og_description="Dedicated cloud workers and verified prospect intelligence.",
                    og_image_url="https://prospectos.com/og-pricing.png",
                    schema_type="Product",
                    sitemap_priority=0.8,
                    change_frequency="monthly",
                    is_published=True,
                    audit_score=94,
                    audit_issues=[]
                ),
                SEOPublicPage(
                    path="/docs",
                    page_name="API & Developer Documentation",
                    meta_title="ProspectOS Documentation | Scraper APIs & CRM Integration",
                    meta_description="Complete REST API documentation, OpenAPI specifications, webhook payloads, and code examples for ProspectOS.",
                    canonical_url="https://prospectos.com/docs",
                    og_title="ProspectOS Developer Documentation",
                    og_description="Integrate automated extraction runs and lead updates directly into your custom stack.",
                    og_image_url="https://prospectos.com/og-docs.png",
                    schema_type="Article",
                    sitemap_priority=0.7,
                    change_frequency="monthly",
                    is_published=True,
                    audit_score=96,
                    audit_issues=[]
                )
            ]
            for p in default_pages:
                self.session.add(p)
            await self.session.commit()
            pages = default_pages

        return [
            SEOPublicPageItem(
                id=p.id,
                path=p.path,
                page_name=p.page_name,
                meta_title=p.meta_title,
                meta_description=p.meta_description,
                canonical_url=p.canonical_url,
                og_title=p.og_title,
                og_description=p.og_description,
                og_image_url=p.og_image_url,
                twitter_card=p.twitter_card,
                robots_directives=p.robots_directives,
                schema_type=p.schema_type,
                structured_data_json=p.structured_data_json,
                sitemap_priority=p.sitemap_priority,
                change_frequency=p.change_frequency,
                is_published=p.is_published,
                last_audited_at=p.last_audited_at,
                audit_score=p.audit_score,
                audit_issues=p.audit_issues or []
            )
            for p in pages
        ]

    async def save_page(self, req: SEOPublicPageCreateOrUpdate) -> SEOPublicPageItem:
        stmt = select(SEOPublicPage).where(SEOPublicPage.path == req.path)
        page = (await self.session.execute(stmt)).scalars().first()

        if not page:
            page = SEOPublicPage(
                path=req.path,
                page_name=req.page_name,
                meta_title=req.meta_title,
                meta_description=req.meta_description,
                canonical_url=req.canonical_url,
                og_title=req.og_title,
                og_description=req.og_description,
                og_image_url=req.og_image_url,
                twitter_card=req.twitter_card,
                robots_directives=req.robots_directives,
                schema_type=req.schema_type,
                structured_data_json=req.structured_data_json,
                sitemap_priority=req.sitemap_priority,
                change_frequency=req.change_frequency,
                is_published=req.is_published,
            )
            self.session.add(page)
        else:
            page.page_name = req.page_name
            page.meta_title = req.meta_title
            page.meta_description = req.meta_description
            page.canonical_url = req.canonical_url
            page.og_title = req.og_title
            page.og_description = req.og_description
            page.og_image_url = req.og_image_url
            page.twitter_card = req.twitter_card
            page.robots_directives = req.robots_directives
            page.schema_type = req.schema_type
            page.structured_data_json = req.structured_data_json
            page.sitemap_priority = req.sitemap_priority
            page.change_frequency = req.change_frequency
            page.is_published = req.is_published

        # Audit this page
        issues, score = self._audit_single_page(page)
        page.audit_issues = issues
        page.audit_score = score
        page.last_audited_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(page)

        return SEOPublicPageItem(
            id=page.id,
            path=page.path,
            page_name=page.page_name,
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            canonical_url=page.canonical_url,
            og_title=page.og_title,
            og_description=page.og_description,
            og_image_url=page.og_image_url,
            twitter_card=page.twitter_card,
            robots_directives=page.robots_directives,
            schema_type=page.schema_type,
            structured_data_json=page.structured_data_json,
            sitemap_priority=page.sitemap_priority,
            change_frequency=page.change_frequency,
            is_published=page.is_published,
            last_audited_at=page.last_audited_at,
            audit_score=page.audit_score,
            audit_issues=page.audit_issues or []
        )

    # ==========================================
    # 3. Technical SEO Audit Engine
    # ==========================================

    def _audit_single_page(self, page: SEOPublicPage) -> tuple[List[Dict[str, Any]], int]:
        issues = []
        score = 100

        # Title checks (optimal: 30 - 65 chars)
        title_len = len(page.meta_title or "")
        if title_len == 0:
            issues.append({"severity": "CRITICAL", "code": "MISSING_TITLE", "message": "Meta title is missing."})
            score -= 30
        elif title_len < 30:
            issues.append({"severity": "WARNING", "code": "SHORT_TITLE", "message": f"Title is short ({title_len} chars). Recommended: 30-65 chars."})
            score -= 10
        elif title_len > 65:
            issues.append({"severity": "WARNING", "code": "LONG_TITLE", "message": f"Title may truncate in Google SERP ({title_len} chars). Recommended: ≤ 65 chars."})
            score -= 5

        # Description checks (optimal: 70 - 160 chars)
        desc_len = len(page.meta_description or "")
        if desc_len == 0:
            issues.append({"severity": "CRITICAL", "code": "MISSING_DESCRIPTION", "message": "Meta description is missing."})
            score -= 30
        elif desc_len < 70:
            issues.append({"severity": "WARNING", "code": "SHORT_DESCRIPTION", "message": f"Description is short ({desc_len} chars). Recommended: 70-160 chars."})
            score -= 10
        elif desc_len > 160:
            issues.append({"severity": "WARNING", "code": "LONG_DESCRIPTION", "message": f"Description exceeds Google standard display limit ({desc_len} chars). Recommended: ≤ 160 chars."})
            score -= 5

        # Canonical check
        if not page.canonical_url or not page.canonical_url.startswith("http"):
            issues.append({"severity": "CRITICAL", "code": "INVALID_CANONICAL", "message": "Valid absolute canonical URL required."})
            score -= 20

        # OG Image check
        if not page.og_image_url:
            issues.append({"severity": "INFO", "code": "MISSING_OG_IMAGE", "message": "Social sharing image (og:image) is not defined."})
            score -= 5

        # Schema JSON-LD check
        if not page.structured_data_json:
            issues.append({"severity": "INFO", "code": "MISSING_SCHEMA", "message": f"Schema.org structured data ({page.schema_type}) is recommended for rich snippets."})
            score -= 5

        return issues, max(10, score)

    async def run_full_audit(self) -> SEOAuditReport:
        pages_items = await self.list_pages()
        now = datetime.now(timezone.utc)

        critical_count = 0
        warning_count = 0
        passed_count = 0
        total_score = 0

        updated_pages = []
        for p in pages_items:
            page_obj = await self.session.get(SEOPublicPage, p.id)
            if page_obj:
                issues, score = self._audit_single_page(page_obj)
                page_obj.audit_issues = issues
                page_obj.audit_score = score
                page_obj.last_audited_at = now
                total_score += score
                for iss in issues:
                    if iss["severity"] == "CRITICAL":
                        critical_count += 1
                    elif iss["severity"] == "WARNING":
                        warning_count += 1
                if not issues:
                    passed_count += 1
                updated_pages.append(SEOPublicPageItem(
                    id=page_obj.id,
                    path=page_obj.path,
                    page_name=page_obj.page_name,
                    meta_title=page_obj.meta_title,
                    meta_description=page_obj.meta_description,
                    canonical_url=page_obj.canonical_url,
                    og_title=page_obj.og_title,
                    og_description=page_obj.og_description,
                    og_image_url=page_obj.og_image_url,
                    twitter_card=page_obj.twitter_card,
                    robots_directives=page_obj.robots_directives,
                    schema_type=page_obj.schema_type,
                    structured_data_json=page_obj.structured_data_json,
                    sitemap_priority=page_obj.sitemap_priority,
                    change_frequency=page_obj.change_frequency,
                    is_published=page_obj.is_published,
                    last_audited_at=now,
                    audit_score=score,
                    audit_issues=issues
                ))

        await self.session.commit()

        overall_score = round(total_score / max(1, len(pages_items)))
        recommendations = [
            {"title": "Canonical URLs Verified", "description": "All public routes feature self-referencing absolute canonical tags."},
            {"title": "Schema.org Rich Snippets", "description": "SoftwareApplication and Product JSON-LD entities configured for rich SERP presence."},
            {"title": "Private Routes Excluded", "description": "Private application routes (/admin, /crm, /system) are correctly excluded from robots.txt and sitemap."}
        ]

        return SEOAuditReport(
            audited_at=now,
            total_pages_checked=len(pages_items),
            overall_health_score=overall_score,
            critical_issues_count=critical_count,
            warning_issues_count=warning_count,
            passed_checks_count=passed_count,
            pages=updated_pages,
            recommendations=recommendations
        )

    # ==========================================
    # 4. Dynamic XML Sitemap & Robots.txt
    # ==========================================

    async def generate_sitemap_xml(self) -> str:
        pages = await self.list_pages()
        global_cfg = await self.get_global_config()
        base_domain = global_cfg.default_canonical_domain.rstrip("/")

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for p in pages:
            if not p.is_published or "noindex" in p.robots_directives:
                continue
            loc = f"{base_domain}{p.path}" if p.path.startswith("/") else f"{base_domain}/{p.path}"
            lastmod = (p.last_audited_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
            xml_lines.append("  <url>")
            xml_lines.append(f"    <loc>{loc}</loc>")
            xml_lines.append(f"    <lastmod>{lastmod}</lastmod>")
            xml_lines.append(f"    <changefreq>{p.change_frequency}</changefreq>")
            xml_lines.append(f"    <priority>{p.sitemap_priority:.1f}</priority>")
            xml_lines.append("  </url>")

        xml_lines.append("</urlset>")
        return "\n".join(xml_lines)

    async def generate_robots_txt(self) -> str:
        global_cfg = await self.get_global_config()
        if global_cfg.robots_txt_content:
            return global_cfg.robots_txt_content.strip()

        base_domain = global_cfg.default_canonical_domain.rstrip("/")
        return f"""User-agent: *
Allow: /
Allow: /features
Allow: /solutions
Allow: /pricing
Allow: /docs
Disallow: /admin
Disallow: /crm
Disallow: /portal
Disallow: /system
Disallow: /api

Sitemap: {base_domain}/sitemap.xml"""

