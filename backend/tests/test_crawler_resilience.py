import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import respx

from app.models import (
    Company,
    WebsiteScan,
    Evidence,
    SEOMetric,
    PublisherRecord,
    PublisherObservation,
    SalesOpportunity,
    SalesIntelligenceScore,
    OpportunityProfile
)
from app.services.crawler.client import CrawlerClient
from app.services.intelligence.runner import WebsiteIntelligenceRunner
from app.services.intelligence.opportunity import OpportunityEngine
from app.services.intelligence.sales_intelligence import SalesIntelligenceService
from app.services.ai.runner import AIExtractionRunner


def get_utc_now():
    return datetime.now(timezone.utc)


# =============================================================================
# 1. Test Crawler Safe Failure Classification & Non-Aggressive Retries
# =============================================================================

@pytest.mark.asyncio
async def test_crawler_classifies_cloudflare_bot_challenge():
    """Verify that HTTP 403 with Cloudflare headers is cleanly classified as a bot challenge without retrying."""
    crawler = CrawlerClient(timeout=5)
    
    with respx.mock(assert_all_called=True) as respx_mock:
        # Mock 403 challenge response
        challenge_html = "<!DOCTYPE html><html><head><title>Just a moment...</title></head><body>Cloudflare Ray ID: 8d2c123</body></html>"
        route = respx_mock.get("https://thedefiant.io/").respond(
            status_code=403,
            headers={
                "server": "cloudflare",
                "cf-ray": "8d2c12345abc-SYD",
                "content-type": "text/html; charset=UTF-8"
            },
            text=challenge_html
        )
        
        result = await crawler.fetch_page("https://thedefiant.io/")
        
        # Verify single request (no aggressive retries on 403)
        assert route.call_count == 1
        assert result["http_status"] == 403
        assert result["is_accessible"] is False
        assert result["status"] == "ACCESS_RESTRICTED"
        assert "BOT_PROTECTION_CHALLENGE" in result["failure_reason"]
        assert "Cloudflare WAF" in result["failure_reason"]
        # Crucial: challenge HTML must be blanked out to prevent pollution
        assert result["html"] == ""


@pytest.mark.asyncio
async def test_crawler_classifies_http_failure_status_codes():
    """Verify classification of 401, 429, and 500 status codes."""
    crawler = CrawlerClient(timeout=5)
    
    test_cases = [
        (401, "AUTHENTICATION_REQUIRED", "ACCESS_RESTRICTED"),
        (429, "RATE_LIMIT_EXCEEDED", "RATE_LIMITED"),
        (500, "SERVER_ERROR", "SERVER_ERROR")
    ]
    
    for status_code, expected_reason, expected_status in test_cases:
        with respx.mock() as respx_mock:
            respx_mock.get(f"https://example-{status_code}.com/").respond(
                status_code=status_code,
                headers={"server": "nginx"},
                text="Error"
            )
            result = await crawler.fetch_page(f"https://example-{status_code}.com/")
            assert result["http_status"] == status_code
            assert result["is_accessible"] is False
            assert result["status"] == expected_status
            assert expected_reason in result["failure_reason"]
            assert result["html"] == ""


# =============================================================================
# 2. Test WebsiteIntelligenceRunner Fallback Execution & Provenance
# =============================================================================

@pytest.mark.asyncio
async def test_runner_preserves_clean_scan_and_records_fallback_evidence(db_session):
    """
    Verify that when crawl is blocked:
    1. Scan record nullifies on-page tags and records failure_reason
    2. Fallback evidence is recorded with complete provenance
    3. Missing on-page content is marked UNAVAILABLE / UNVERIFIED
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Healthcare Business Today {suffix}",
        canonical_domain=f"healthcarebusinesstoday-{suffix}.com",
        website_url=f"https://healthcarebusinesstoday-{suffix}.com",
        industry="Healthcare",
        sales_stage="DISCOVERED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Seed an authorized publisher catalog match for fallback B
    pub = PublisherRecord(
        company_id=company.id,
        publisher_name="Healthcare Tech Daily",
        audience_focus="Healthcare B2B Decision Makers",
        status="ACTIVE"
    )
    db_session.add(pub)
    await db_session.commit()

    runner = WebsiteIntelligenceRunner()
    
    # Mock crawler client to simulate Cloudflare 403
    mock_crawler = AsyncMock()
    mock_crawler.fetch_page.return_value = {
        "url": company.website_url,
        "final_url": company.website_url,
        "http_status": 403,
        "is_accessible": False,
        "failure_reason": "BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)",
        "status": "ACCESS_RESTRICTED",
        "html": "",
        "headers": {"server": "cloudflare", "cf-ray": "12345678"},
        "redirect_chain": [],
        "load_time_ms": 120
    }
    mock_crawler.fetch_robots_txt.return_value = ("FOUND", "User-agent: *\nDisallow:", True)
    
    with patch.object(runner, "crawler", mock_crawler):
        status = await runner.analyze_company(company.id)

    assert status == "ACCESS_RESTRICTED"

    # Check scan record in DB
    scan = (await db_session.execute(
        WebsiteScan.__table__.select().where(WebsiteScan.company_id == company.id)
    )).mappings().first()
    
    assert scan is not None
    assert scan["http_status"] == 403
    assert scan["scan_status"] == "ACCESS_RESTRICTED"
    assert scan["title"] is None
    assert scan["meta_description"] is None
    assert scan["h1"] is None
    assert scan["technology_signals"]["is_accessible"] is False
    assert "BOT_PROTECTION_CHALLENGE" in scan["technology_signals"]["failure_reason"]

    # Check Evidence records in DB
    evidence_rows = (await db_session.execute(
        Evidence.__table__.select().where(Evidence.company_id == company.id)
    )).mappings().all()

    evidence_by_type = {e["source_type"]: e for e in evidence_rows}
    
    # 1. Fallback C: UNAVAILABLE / UNVERIFIED on-page evidence
    assert "RESTRICTED_CRAWL" in evidence_by_type
    unavail_ev = evidence_by_type["RESTRICTED_CRAWL"]
    assert unavail_ev["field_name"] == "on_page_seo_content"
    assert unavail_ev["value"] == "UNAVAILABLE"
    assert unavail_ev["verification_status"] == "UNVERIFIED"

    # 2. Fallback B: Authorized catalog identity evidence
    assert "AUTHORIZED_CATALOG_FEED" in evidence_by_type
    feed_ev = evidence_by_type["AUTHORIZED_CATALOG_FEED"]
    assert feed_ev["verification_status"] == "VERIFIED"
    assert feed_ev["provider"] == "authorized_catalog_inventory"


# =============================================================================
# 3. Test OpportunityEngine Non-Inflation on HTTP 403
# =============================================================================

@pytest.mark.asyncio
async def test_opportunity_engine_does_not_fabricate_issues_on_403(db_session):
    """Verify OpportunityEngine assigns baseline score (55.0) and records missing information on 403."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        id=uuid.uuid4(),
        company_name=f"Australian Aviation Test {suffix}",
        canonical_domain=f"australianaviation-test-{suffix}.com.au"
    )
    db_session.add(company)
    await db_session.commit()

    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://australianaviation-test-{suffix}.com.au",
        http_status=403,
        https_enabled=True,
        robots_txt_status="FOUND",
        title=None,
        meta_description=None,
        h1=None,
        scan_status="ACCESS_RESTRICTED",
        technology_signals={"is_accessible": False, "failure_reason": "BOT_PROTECTION_CHALLENGE"}
    )
    db_session.add(scan)
    await db_session.commit()

    engine = OpportunityEngine(db_session)
    profile = await engine.evaluate_company(company.id)

    # Must NOT fabricate Missing H1 or Robots.txt issue
    assert "Missing H1 tags" not in profile.identified_problems
    assert not any("Robots.txt issue" in p for p in profile.identified_problems)
    
    # Must identify the bot protection challenge
    assert any("bot protection (HTTP 403)" in p for p in profile.identified_problems)
    
    # Must note unverified on-page data in missing_information
    assert any("unverified due to HTTP 403" in m for m in profile.missing_information)

    # Score must be calibrated (55.0), NOT inflated to 90-100
    assert profile.opportunity_score == 55.0
    assert profile.confidence_level <= 0.70


# =============================================================================
# 4. Test SalesIntelligenceService: Non-Fabrication & Calibrated Scoring
# =============================================================================

@pytest.mark.asyncio
async def test_sales_intelligence_single_advisory_opportunity_on_403(db_session):
    """
    Verify that an access-restricted scan (HTTP 403):
    1. Produces ONLY a single INDEXABILITY_CRAWLABILITY opportunity (MEDIUM severity)
    2. Does NOT produce PAGE_METADATA or CONTENT_COVERAGE opportunities
    3. Calibrates overall priority score without artificial inflation
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"The Defiant Media {suffix}",
        canonical_domain=f"thedefiant-{suffix}.io",
        website_url=f"https://thedefiant-{suffix}.io",
        industry="Cryptocurrency",
        target_market="Web3 Investors",
        sales_stage="DISCOVERED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Add access-restricted scan
    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://thedefiant-{suffix}.io",
        http_status=403,
        https_enabled=True,
        robots_txt_status="FOUND",
        title=None,
        meta_description=None,
        h1=None,
        technology_signals={
            "is_accessible": False,
            "failure_reason": "BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)"
        },
        scan_status="ACCESS_RESTRICTED",
        scanned_at=datetime.now(timezone.utc)
    )
    db_session.add(scan)

    # Add authorized Ahrefs metric (high DR)
    dr_metric = SEOMetric(
        company_id=company.id,
        metric_name="domain_rating",
        metric_value=73.0,
        provider="ahrefs",
        verification_status="VERIFIED",
        retrieved_at=datetime.now(timezone.utc)
    )
    db_session.add(dr_metric)

    # Add publisher record matching industry
    pub = PublisherRecord(
        company_id=company.id,
        publisher_name="Crypto Chronicle",
        audience_focus="Cryptocurrency and DeFi",
        status="ACTIVE"
    )
    db_session.add(pub)
    await db_session.commit()
    await db_session.refresh(pub)

    pub_obs = PublisherObservation(
        publisher_id=pub.id,
        metric_da=68,
        price=350.0,
        currency="USD",
        observation_timestamp=datetime.now(timezone.utc)
    )
    db_session.add(pub_obs)
    await db_session.commit()

    service = SalesIntelligenceService(db_session)
    opps = await service.detect_opportunities(company.id)

    # Assert opportunity counts and categories
    opp_categories = [o.category for o in opps]
    assert "INDEXABILITY_CRAWLABILITY" in opp_categories
    assert "PAGE_METADATA" not in opp_categories
    assert "CONTENT_COVERAGE" not in opp_categories
    assert "CONTENT_ARCHITECTURE" not in opp_categories

    # Assert single crawl opportunity severity is MEDIUM, not CRITICAL
    crawl_opp = next(o for o in opps if o.category == "INDEXABILITY_CRAWLABILITY")
    assert crawl_opp.severity == "MEDIUM"
    assert "HTTP 403" in crawl_opp.title

    # Compute priority score
    score_record = await service.calculate_priority_score(company.id)
    
    # Assert score is properly calibrated (~50-65), not inflated to 80-95
    assert 45.0 <= score_record.overall_priority_score <= 65.0
    
    # Service fit: DIGITAL_PR is favored over false TECHNICAL_SEO
    assert score_record.primary_recommended_service == "DIGITAL_PR"

    # Assert limitations document bot protection
    assert any("blocked by bot protection" in lim for lim in score_record.limitations)
    assert any("unverified" in mi for mi in score_record.missing_information)


# =============================================================================
# 5. Test AI Extraction Runner Evidence Gathering Anti-Hallucination
# =============================================================================

@pytest.mark.asyncio
async def test_ai_runner_gather_evidence_anti_hallucination(db_session):
    """Verify that AI runner includes explicit anti-hallucination instructions and fallback evidence."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Secure SaaS {suffix}",
        canonical_domain=f"securesaas-{suffix}.io",
        website_url=f"https://securesaas-{suffix}.io",
        industry="Cybersecurity",
        description="Enterprise zero trust authentication"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    scan = WebsiteScan(
        company_id=company.id,
        url=company.website_url,
        http_status=403,
        scan_status="ACCESS_RESTRICTED",
        title=None,
        meta_description=None,
        h1=None
    )
    db_session.add(scan)

    ev_fallback = Evidence(
        company_id=company.id,
        source_type="AUTHORIZED_CATALOG_FEED",
        field_name="primary_product",
        value="Zero Trust Identity Management",
        provider="authorized_catalog_inventory",
        verification_status="VERIFIED",
        confidence=0.95
    )
    db_session.add(ev_fallback)
    await db_session.commit()

    runner = AIExtractionRunner(job_id=str(uuid.uuid4()))
    evidence_text = await runner._gather_evidence_text(db_session, company.id)

    assert "access-restricted (HTTP 403" in evidence_text
    assert "CRITICAL INSTRUCTION: Live on-page HTML is blocked by bot protection" in evidence_text
    assert "AUTHORIZED_CATALOG_FEED" in evidence_text
    assert "Zero Trust Identity Management" in evidence_text
    assert "Page Title" not in evidence_text
