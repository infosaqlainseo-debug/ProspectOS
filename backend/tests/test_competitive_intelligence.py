import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models import (
    Company,
    WebsiteScan,
    SEOMetric,
    PublisherRecord,
    PublisherObservation,
    CompanyCompetitor,
    CompetitiveAnalysisRun,
    SalesOpportunity
)
from app.services.intelligence.competitive_service import CompetitiveIntelligenceService
from app.schemas.competitive import CompetitorCreate, CompetitorUpdate


@pytest.mark.asyncio
async def test_competitor_discovery_and_relevance(db_session):
    suffix = uuid.uuid4().hex[:6]

    # Create Prospect Company
    prospect = Company(
        company_name=f"Alpha SaaS Corp {suffix}",
        canonical_domain=f"alphasass-{suffix}.com",
        industry=f"Technology_{suffix}",
        sub_industry=f"B2B Software_{suffix}",
        sales_stage="NEW"
    )
    # Create Peer Company in same industry
    peer_company = Company(
        company_name=f"Beta Cloud Systems {suffix}",
        canonical_domain=f"betacloud-{suffix}.com",
        industry=f"Technology_{suffix}",
        sub_industry=f"B2B Software_{suffix}",
        sales_stage="QUALIFIED"
    )
    # Create Irrelevant Company in different industry
    other_company = Company(
        company_name=f"Zeta Bakery {suffix}",
        canonical_domain=f"zetabakery-{suffix}.com",
        industry=f"Food_Bakery_{suffix}",
        sales_stage="CLOSED_LOST"
    )
    db_session.add_all([prospect, peer_company, other_company])
    await db_session.commit()
    await db_session.refresh(prospect)
    await db_session.refresh(peer_company)

    # Add scan with content headings for keyword overlap
    p_scan = WebsiteScan(
        company_id=prospect.id,
        url=f"https://alphasass-{suffix}.com",
        h1=["Enterprise Cloud Analytics SaaS Platform"],
        h2=["Scalable B2B Software Solutions"],
        technology_signals={"cms": "WordPress", "word_count": 850},
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    peer_scan = WebsiteScan(
        company_id=peer_company.id,
        url=f"https://betacloud-{suffix}.com",
        h1=["Enterprise Cloud Platform for Modern Businesses"],
        h2=["B2B SaaS Analytics and Automation"],
        technology_signals={"cms": "Next.js", "word_count": 1400},
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    db_session.add_all([p_scan, peer_scan])
    await db_session.commit()

    service = CompetitiveIntelligenceService(db_session)
    candidates = await service.discover_competitors(company_id=prospect.id, max_results=5)

    assert len(candidates) >= 1
    # Peer company should be discovered with high relevance
    matched = next((c for c in candidates if c.canonical_domain == peer_company.canonical_domain), None)
    assert matched is not None
    assert matched.relevance_tier in ["DIRECT", "INDIRECT"]
    assert matched.relevance_score >= 0.50
    assert matched.overlap_evidence.get("shared_industry") is True

    # Zeta Bakery should NOT be in direct candidates
    bakery_match = next((c for c in candidates if c.canonical_domain == other_company.canonical_domain), None)
    assert bakery_match is None


@pytest.mark.asyncio
async def test_competitor_crud_and_validation(db_session):
    suffix = uuid.uuid4().hex[:6]
    prospect = Company(
        company_name=f"Delta Fintech {suffix}",
        canonical_domain=f"deltafintech-{suffix}.com",
        industry="Finance"
    )
    db_session.add(prospect)
    await db_session.commit()
    await db_session.refresh(prospect)

    service = CompetitiveIntelligenceService(db_session)

    # 1. Add Competitor
    create_dto = CompetitorCreate(
        company_id=prospect.id,
        competitor_name="Competitor One",
        competitor_domain=f"compone-{suffix}.com",
        relevance_tier="DIRECT",
        relevance_score=0.92,
        notes="Primary market rival"
    )
    comp = await service.add_competitor(prospect.id, create_dto)
    assert comp.id is not None
    assert comp.competitor_domain == f"compone-{suffix}.com"
    assert comp.relevance_tier == "DIRECT"
    assert comp.validation_status == "VERIFIED"

    # 2. Idempotent upsert on same domain without duplication
    comp_dup = await service.add_competitor(prospect.id, create_dto)
    assert comp_dup.id == comp.id

    comps = await service.get_competitors(prospect.id)
    assert len(comps) == 1

    # 3. Update Competitor
    update_dto = CompetitorUpdate(
        notes="Updated rival notes",
        relevance_score=0.95,
        relevance_tier="DIRECT",
        validation_status="VERIFIED"
    )
    updated = await service.update_competitor(comp.id, update_dto)
    assert updated.notes == "Updated rival notes"
    assert updated.relevance_score == 0.95

    # 4. List Competitors
    comps_after = await service.get_competitors(prospect.id)
    assert len(comps_after) == 1
    assert comps_after[0].id == comp.id


@pytest.mark.asyncio
async def test_side_by_side_competitive_analysis_engine(db_session):
    suffix = uuid.uuid4().hex[:6]

    # Create Prospect and Competitor Companies
    prospect = Company(
        company_name=f"Epsilon SEO Agency {suffix}",
        canonical_domain=f"epsilonseo-{suffix}.com",
        industry="Marketing",
        sub_industry="Digital Marketing"
    )
    competitor_company = Company(
        company_name=f"Omega Growth Media {suffix}",
        canonical_domain=f"omegagrowth-{suffix}.com",
        industry="Marketing",
        sub_industry="Digital Marketing"
    )
    pub_company = Company(
        company_name=f"Search Engine Journal Co {suffix}",
        canonical_domain=f"sejournal-{suffix}.com",
        industry="Media"
    )
    db_session.add_all([prospect, competitor_company, pub_company])
    await db_session.commit()
    await db_session.refresh(prospect)
    await db_session.refresh(competitor_company)
    await db_session.refresh(pub_company)

    # Website scans
    # Prospect has technical gaps and thin content
    p_scan = WebsiteScan(
        company_id=prospect.id,
        url=f"https://epsilonseo-{suffix}.com",
        http_status=200,
        https_enabled=False, # Missing HTTPS
        robots_txt_status="NOT_FOUND", # Missing robots.txt
        sitemap_status="NOT_FOUND", # Missing sitemap
        h1=["Home"],
        h2=["Services", "About Us"],
        technology_signals={"word_count": 350, "viewport_meta": False},
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    # Competitor has rich structure, schemas, topics
    c_scan = WebsiteScan(
        company_id=competitor_company.id,
        url=f"https://omegagrowth-{suffix}.com",
        http_status=200,
        https_enabled=True,
        robots_txt_status="FOUND",
        sitemap_status="FOUND",
        h1=["Enterprise Content Marketing & SEO Authority"],
        h2=[
            "How to Drive Organic Traffic in 2026",
            "B2B Content Marketing Strategy Guide",
            "Pricing and Service Tiers for Global Brands",
            "SEO Case Studies and Client ROI",
            "Free SEO Audit and Pricing Consultation"
        ],
        technology_signals={
            "word_count": 2800,
            "viewport_meta": True,
            "schema_types": ["Organization", "Article", "FAQPage"],
            "cms": "Webflow"
        },
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    db_session.add_all([p_scan, c_scan])

    # Add a Publisher record in Marketing for Digital PR match
    pub = PublisherRecord(
        company_id=pub_company.id,
        publisher_name=f"Search Engine Journal {suffix}",
        audience_focus="Marketing",
        status="VERIFIED"
    )
    db_session.add(pub)
    await db_session.commit()
    await db_session.refresh(pub)

    pub_obs = PublisherObservation(
        publisher_id=pub.id,
        metric_da=78.0,
        metric_dr=82.0,
        price=450.0,
        currency="USD",
        verification_status="VERIFIED",
        observation_timestamp=datetime.now(timezone.utc)
    )
    db_session.add(pub_obs)
    await db_session.commit()

    service = CompetitiveIntelligenceService(db_session)

    # Track competitor
    comp_link = await service.add_competitor(
        prospect.id,
        CompetitorCreate(
            company_id=prospect.id,
            competitor_company_id=competitor_company.id,
            competitor_name=competitor_company.company_name,
            competitor_domain=competitor_company.canonical_domain,
            relevance_tier="DIRECT",
            relevance_score=0.95
        )
    )

    # Run Competitive Analysis
    run = await service.run_competitive_analysis(
        company_id=prospect.id,
        competitor_id=comp_link.id,
        sync_to_sales_opportunities=True
    )

    assert run.id is not None
    assert run.status == "COMPLETED"

    # Verify Content Gaps & Intent Categorization
    assert len(run.content_gaps) >= 2
    intents = {g["search_intent"] for g in run.content_gaps}
    assert any(i in ["INFORMATIONAL", "COMMERCIAL", "TRANSACTIONAL"] for i in intents)

    # Verify Technical Gaps
    assert len(run.technical_gaps) >= 2
    tech_issues = {t["metric_or_feature"] for t in run.technical_gaps}
    assert "XML Sitemap" in tech_issues or "Insecure Protocol (HTTP)" in tech_issues or "Robots.txt Availability" in tech_issues

    # Verify Internal Linking Gaps
    assert len(run.internal_linking_gaps) >= 1

    # Verify Backlink Gap handling (no fabrication of provider metrics)
    assert run.backlink_gaps is not None
    # Because third-party providers (Moz/Ahrefs) are unconfigured in test environment:
    assert run.backlink_gaps.get("is_provider_configured") is False
    assert run.backlink_gaps.get("prospect_da") is None
    assert len(run.backlink_gaps.get("limitations", [])) >= 1

    # Verify Digital PR publisher matches from real inventory
    assert len(run.publisher_opportunities) >= 1
    matched_pub = run.publisher_opportunities[0]
    assert matched_pub["publisher_name"] == pub.publisher_name
    assert "Marketing" in matched_pub["audience_focus"]

    # Verify Prioritized Recommendations
    assert len(run.prioritized_recommendations) >= 3
    rec_services = {r["service"] for r in run.prioritized_recommendations}
    assert any(s in ["TECHNICAL_SEO", "CONTENT_STRATEGY", "DIGITAL_PR", "LINK_BUILDING"] for s in rec_services)

    # Verify SalesOpportunity sync and deduplication
    sync_stmt = select(SalesOpportunity).where(SalesOpportunity.company_id == prospect.id)
    opps = (await db_session.execute(sync_stmt)).scalars().all()
    assert len(opps) >= 1
    assert any(o.category == "COMPETITIVE_GAP" for o in opps)

    # Re-running analysis should update rather than duplicate opportunities
    run_2 = await service.run_competitive_analysis(
        company_id=prospect.id,
        competitor_id=comp_link.id,
        sync_to_sales_opportunities=True
    )
    opps_2 = (await db_session.execute(sync_stmt)).scalars().all()
    comp_opps_count = len([o for o in opps_2 if o.category == "COMPETITIVE_GAP"])
    assert comp_opps_count == len([o for o in opps if o.category == "COMPETITIVE_GAP"])


@pytest.mark.asyncio
async def test_competitive_api_endpoints(db_session):
    suffix = uuid.uuid4().hex[:6]

    company = Company(
        company_name=f"Gamma Health {suffix}",
        canonical_domain=f"gammahealth-{suffix}.com",
        industry="Healthcare",
        sales_stage="NEW"
    )
    competitor = Company(
        company_name=f"Zenith Wellness {suffix}",
        canonical_domain=f"zenithwellness-{suffix}.com",
        industry="Healthcare",
        sales_stage="QUALIFIED"
    )
    db_session.add_all([company, competitor])
    await db_session.commit()
    await db_session.refresh(company)
    await db_session.refresh(competitor)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Discover Competitors
        resp = await client.post(f"/competitive/companies/{company.id}/discover?max_results=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

        # 2. Add Competitor
        add_payload = {
            "company_id": str(company.id),
            "competitor_name": competitor.company_name,
            "competitor_domain": competitor.canonical_domain,
            "competitor_company_id": str(competitor.id),
            "relevance_tier": "DIRECT",
            "relevance_score": 0.90,
            "discovery_method": "MANUAL",
            "notes": "Verified clinic rival"
        }
        resp = await client.post(f"/competitive/companies/{company.id}/competitors", json=add_payload)
        assert resp.status_code == 201
        comp_data = resp.json()
        competitor_id = comp_data["id"]

        # 3. List Competitors
        resp = await client.get(f"/competitive/companies/{company.id}/competitors")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 4. Update Competitor
        update_payload = {
            "notes": "Top tier competitor",
            "relevance_score": 0.96
        }
        resp = await client.put(f"/competitive/competitors/{competitor_id}", json=update_payload)
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Top tier competitor"

        # 5. Run Analysis
        analysis_payload = {
            "competitor_id": competitor_id,
            "sync_to_sales_opportunities": True
        }
        resp = await client.post(f"/competitive/companies/{company.id}/analyze", json=analysis_payload)
        assert resp.status_code == 200
        run_data = resp.json()
        assert run_data["status"] == "COMPLETED"
        assert run_data["competitor_name"] == competitor.company_name
        run_id = run_data["id"]

        # 6. List Analysis Runs
        resp = await client.get(f"/competitive/companies/{company.id}/runs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # 7. Get Run by ID
        resp = await client.get(f"/competitive/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id

        # 8. Get Executive Overview
        resp = await client.get(f"/competitive/companies/{company.id}/overview")
        assert resp.status_code == 200
        overview = resp.json()
        assert overview["company_name"] == company.company_name
        assert overview["competitors_count"] == 1
        assert overview["analyzed_runs_count"] >= 1
        assert overview["latest_run"] is not None
