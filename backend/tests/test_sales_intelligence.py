import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import (
    Company,
    WebsiteScan,
    SEOMetric,
    AIObservation,
    PublisherRecord,
    PublisherObservation,
    AIExtractionRun,
    SalesIntelligenceScore,
    SalesOpportunity,
    SalesBrief,
    CRMActivity
)
from app.services.intelligence.sales_intelligence import SalesIntelligenceService


@pytest.mark.asyncio
async def test_opportunity_detection_and_classification(db_session):
    suffix = uuid.uuid4().hex[:6]
    # Setup test company
    company = Company(
        company_name=f"Acme Tech SaaS {suffix}",
        canonical_domain=f"acmetech-{suffix}.io",
        website_url=f"http://acmetech-{suffix}.io",
        industry="SaaS",
        sales_stage="NEW"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Add website scan with observable deficits
    scan = WebsiteScan(
        company_id=company.id,
        url=f"http://acmetech-{suffix}.io",
        http_status=503,
        https_enabled=False,
        robots_txt_status="NOT_FOUND",
        title="Acme", # short title
        meta_description=None, # missing description
        h1=[], # missing H1
        technology_signals={"word_count": 120}, # thin content
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    db_session.add(scan)

    # Add authority metric deficits
    metric_dr = SEOMetric(
        company_id=company.id,
        metric_name="domain_rating",
        metric_value=12.0,
        provider="ahrefs",
        verification_status="VERIFIED",
        retrieved_at=datetime.now(timezone.utc)
    )
    metric_traffic = SEOMetric(
        company_id=company.id,
        metric_name="organic_traffic",
        metric_value=250.0,
        provider="semrush",
        verification_status="VERIFIED",
        retrieved_at=datetime.now(timezone.utc)
    )
    db_session.add(metric_dr)
    db_session.add(metric_traffic)

    # Add AI qualitative observation
    ext_run = AIExtractionRun(
        id=uuid.uuid4(),
        company_id=company.id,
        provider="gemini",
        model="gemini-2.0-flash",
        prompt_version="1.0",
        schema_version="1.0",
        status="COMPLETED"
    )
    obs = AIObservation(
        company_id=company.id,
        extraction_run_id=ext_run.id,
        attribute_name="content_quality",
        attribute_value="POOR",
        confidence=0.88,
        verification_status="VERIFIED"
    )
    db_session.add(ext_run)
    db_session.add(obs)
    await db_session.commit()

    service = SalesIntelligenceService(db_session)
    opps = await service.detect_opportunities(company.id)

    assert len(opps) >= 6
    categories = [o.category for o in opps]
    assert "TECHNICAL_SEO" in categories
    assert "PAGE_METADATA" in categories
    assert "CONTENT_COVERAGE" in categories
    assert "BACKLINK_AUTHORITY" in categories

    # Verify severity & impact rationale
    critical_opps = [o for o in opps if o.severity == "CRITICAL"]
    assert len(critical_opps) >= 1
    assert "503" in critical_opps[0].title
    assert len(critical_opps[0].supporting_evidence) > 0


@pytest.mark.asyncio
async def test_service_fit_and_priority_scoring(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Apex Growth Labs {suffix}",
        canonical_domain=f"apexgrowth-{suffix}.com",
        industry="Marketing",
        target_market="B2B Enterprise",
        sales_stage="QUALIFIED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Add scan with missing metadata & thin content
    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://apexgrowth-{suffix}.com",
        http_status=200,
        https_enabled=True,
        title="Apex Growth Labs - Premier Strategic B2B Revenue Optimization",
        meta_description=None, # Missing meta description
        h1=["Apex Revenue Engine"],
        technology_signals={"word_count": 180},
        scan_status="COMPLETED",
        scanned_at=datetime.now(timezone.utc)
    )
    db_session.add(scan)

    # Add backlink metrics
    metric_dr = SEOMetric(
        company_id=company.id,
        metric_name="domain_rating",
        metric_value=18.0,
        provider="ahrefs",
        verification_status="VERIFIED"
    )
    db_session.add(metric_dr)

    # Add matching publisher
    pub_company = Company(
        company_name=f"Marketing Tech Weekly {suffix}",
        canonical_domain=f"martechweekly-{suffix}.com"
    )
    db_session.add(pub_company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=pub_company.id,
        publisher_name="Marketing Tech Weekly",
        audience_focus="Marketing, SaaS, B2B Enterprise",
        status="VERIFIED"
    )
    db_session.add(pub)
    await db_session.commit()

    pub_obs = PublisherObservation(
        publisher_id=pub.id,
        metric_da=55.0,
        metric_dr=60.0,
        price=750.0,
        currency="USD"
    )
    db_session.add(pub_obs)
    await db_session.commit()

    service = SalesIntelligenceService(db_session)
    score_obj = await service.calculate_priority_score(company.id)

    assert score_obj.overall_priority_score > 0
    assert score_obj.scoring_version == "v3.0.0"
    assert score_obj.primary_recommended_service in ["LINK_BUILDING", "CONTENT_STRATEGY", "DIGITAL_PR", "TECHNICAL_SEO"]
    assert score_obj.seo_severity_score > 0
    assert score_obj.service_fit_score > 0
    assert score_obj.publisher_fit_score > 0
    assert len(score_obj.positive_indicators) > 0


@pytest.mark.asyncio
async def test_sales_brief_generation_and_customization(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Cloudscale DevOps {suffix}",
        canonical_domain=f"cloudscale-{suffix}.dev",
        industry="DevOps",
        sales_stage="RESEARCHED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = SalesIntelligenceService(db_session)
    brief = await service.generate_or_get_brief(company.id)

    assert brief.id is not None
    assert f"Cloudscale DevOps {suffix}" in brief.title
    assert "Sales Intelligence Brief" in brief.full_brief_markdown
    assert "Strategic Sales Discovery Questions" in brief.full_brief_markdown
    assert len(brief.discovery_questions) > 0
    assert not brief.is_customized

    # Test custom revision
    brief.full_brief_markdown += "\n\n**Custom Strategic Note:** Client prefers quarterly retainer over one-off audits."
    brief.is_customized = True
    brief.last_edited_by = "lead_account_exec"
    await db_session.commit()
    await db_session.refresh(brief)

    # Retrieval must preserve customized brief
    retrieved = await service.generate_or_get_brief(company.id, force_regenerate=False)
    assert retrieved.is_customized
    assert "Custom Strategic Note" in retrieved.full_brief_markdown


@pytest.mark.asyncio
async def test_human_override_and_crm_activity_logging(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Pinnacle Logistics {suffix}",
        canonical_domain=f"pinnaclelogistics-{suffix}.net",
        industry="Logistics",
        sales_stage="NEW"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = SalesIntelligenceService(db_session)
    initial_score = await service.calculate_priority_score(company.id)
    assert initial_score.human_override_score is None

    # Perform human override
    updated = await service.override_score(
        company_id=company.id,
        score=92.5,
        reason="Direct executive introduction; high Q4 enterprise budget verified",
        actor="sales_director"
    )
    assert updated.human_override_score == 92.5
    assert updated.human_override_by == "sales_director"
    assert "Direct executive introduction" in updated.human_override_reason

    # Verify CRMActivity audit trail entry for override
    from sqlalchemy import select
    res_act = await db_session.execute(
        select(CRMActivity).where(
            CRMActivity.company_id == company.id,
            CRMActivity.activity_type == "SCORE_OVERRIDE"
        )
    )
    act = res_act.scalar_one_or_none()
    assert act is not None
    assert act.actor == "sales_director"
    assert "92.5" in act.title

    # Verify CRMActivity audit trail entry for initial score evaluation (scoring history preservation)
    res_eval_act = await db_session.execute(
        select(CRMActivity).where(
            CRMActivity.company_id == company.id,
            CRMActivity.activity_type == "SCORE_EVALUATION"
        )
    )
    eval_act = res_eval_act.scalar_one_or_none()
    assert eval_act is not None
    assert eval_act.actor == "system_scorer"
    assert "Sales Priority Evaluated" in eval_act.title
    assert "overall_priority_score" in eval_act.details


@pytest.mark.asyncio
async def test_prioritized_queue_and_comparison(db_session):
    suffix = uuid.uuid4().hex[:6]
    c1 = Company(company_name=f"High Priority Alpha {suffix}", canonical_domain=f"alpha-{suffix}.io", industry=f"Fintech_{suffix}")
    c2 = Company(company_name=f"Low Priority Beta {suffix}", canonical_domain=f"beta-{suffix}.io", industry=f"Fintech_{suffix}")
    db_session.add_all([c1, c2])
    await db_session.commit()

    service = SalesIntelligenceService(db_session)
    score1 = await service.calculate_priority_score(c1.id)
    score2 = await service.calculate_priority_score(c2.id)

    # Artificially set override on c1 to ensure ranking order
    await service.override_score(c1.id, 95.0, "Top tier lead", "test_runner")

    total, queue = await service.get_prioritized_queue(industry=f"Fintech_{suffix}")
    assert total >= 2
    assert queue[0].company_id == c1.id
    assert queue[0].effective_score == 95.0

    # Side-by-side comparison
    comp_res = await service.compare_prospects([c1.id, c2.id])
    assert len(comp_res.compared_prospects) == 2
    names = [p.company_name for p in comp_res.compared_prospects]
    assert f"High Priority Alpha {suffix}" in names
    assert f"Low Priority Beta {suffix}" in names


@pytest.mark.asyncio
async def test_sales_intelligence_api_endpoints(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"API Test Prospect {suffix}",
        canonical_domain=f"apitestprospect-{suffix}.com",
        industry=f"Cybersec_{suffix}",
        sales_stage="NEW"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Evaluate & Score
        res_score = await client.get(f"/sales-intelligence/prospects/{company.id}/score")
        assert res_score.status_code == 200
        data_score = res_score.json()
        assert "overall_priority_score" in data_score
        assert data_score["scoring_version"] == "v3.0.0"

        # 2. Opportunities list
        res_opps = await client.get(f"/sales-intelligence/prospects/{company.id}/opportunities")
        assert res_opps.status_code == 200
        assert isinstance(res_opps.json(), list)

        # 3. Brief endpoint
        res_brief = await client.get(f"/sales-intelligence/prospects/{company.id}/brief")
        assert res_brief.status_code == 200
        data_brief = res_brief.json()
        assert "full_brief_markdown" in data_brief
        assert f"API Test Prospect {suffix}" in data_brief["title"]

        # 4. Export endpoint
        res_export = await client.get(f"/sales-intelligence/prospects/{company.id}/brief/export")
        assert res_export.status_code == 200
        assert "Sales Intelligence Brief" in res_export.text

        # 5. Queue endpoint
        res_queue = await client.get(f"/sales-intelligence/queue?industry=Cybersec_{suffix}")
        assert res_queue.status_code == 200
        data_queue = res_queue.json()
        assert data_queue["total"] >= 1
        assert any(item["company_id"] == str(company.id) for item in data_queue["items"])

        # 6. Override score
        res_override = await client.post(
            f"/sales-intelligence/prospects/{company.id}/override",
            json={"score": 88.0, "reason": "Verified high market demand"}
        )
        assert res_override.status_code == 200
        assert res_override.json()["human_override_score"] == 88.0

        # 7. Update Review Status
        res_status = await client.post(
            f"/sales-intelligence/prospects/{company.id}/review-status",
            json={"review_status": "QUALIFIED", "notes": "Approved for sales outreach"}
        )
        assert res_status.status_code == 200
        assert res_status.json()["review_status"] == "QUALIFIED"
