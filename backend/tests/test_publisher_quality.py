import uuid
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import (
    Company,
    Domain,
    WebsiteScan,
    PublisherRecord,
    PublisherObservation,
    PublisherQualityScore,
    PublisherQualityFinding,
    PublisherRefreshLog,
    CRMActivity,
    CampaignProfile,
    MatchingRun,
    MatchResult
)
from app.services.publishers.quality_service import PublisherQualityService
from app.services.matching.engine import MatchingEngine


@pytest.mark.asyncio
async def test_domain_normalization_and_url_validation(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Publisher Normalization Test {suffix}",
        canonical_domain=f"valid-pub-{suffix}.com",
        website_url=f"https://valid-pub-{suffix}.com",
        industry="Technology"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # 1. Test publisher with valid URL
    pub_valid = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://www.valid-pub-{suffix}.com/about",
        publisher_name="Valid Publisher",
        audience_focus="Technology",
        status="UNVERIFIED"
    )
    db_session.add(pub_valid)
    await db_session.commit()
    await db_session.refresh(pub_valid)

    service = PublisherQualityService(db_session)
    score, findings = await service.audit_publisher(pub_valid.id)

    # URL is valid, so no INVALID_DATA for website_url
    url_invalid_findings = [f for f in findings if f.field_name == "website_url" and f.issue_type == "INVALID_DATA"]
    assert len(url_invalid_findings) == 0

    # 2. Test publisher with unparseable URL
    pub_valid.original_submitted_url = "not-a-valid-url-at-all"
    await db_session.commit()

    score2, findings2 = await service.audit_publisher(pub_valid.id)
    invalid_url_findings = [f for f in findings2 if f.field_name == "website_url" and f.issue_type == "INVALID_DATA"]
    assert len(invalid_url_findings) == 1
    assert "Invalid or Malformed Website URL" in invalid_url_findings[0].title


@pytest.mark.asyncio
async def test_duplicate_publisher_detection(db_session):
    suffix = uuid.uuid4().hex[:6]
    # Two distinct companies; one publisher submits URL that collides with the first's domain
    c1 = Company(
        company_name=f"Primary Publisher {suffix}",
        canonical_domain=f"duplicate-domain-{suffix}.org",
        industry="Media"
    )
    c2 = Company(
        company_name=f"Secondary Publisher {suffix}",
        canonical_domain=f"secondary-partner-{suffix}.org",
        industry="Media"
    )
    db_session.add_all([c1, c2])
    await db_session.commit()

    p1 = PublisherRecord(
        company_id=c1.id,
        original_submitted_url=f"https://duplicate-domain-{suffix}.org",
        publisher_name=f"Pub 1 {suffix}",
        audience_focus="Media"
    )
    p2 = PublisherRecord(
        company_id=c2.id,
        original_submitted_url=f"https://duplicate-domain-{suffix}.org/syndication",
        publisher_name=f"Pub 2 {suffix}",
        audience_focus="Media"
    )
    db_session.add_all([p1, p2])
    await db_session.commit()

    service = PublisherQualityService(db_session)
    score1, findings1 = await service.audit_publisher(p1.id)

    dup_findings = [f for f in findings1 if f.issue_type == "DUPLICATE_RECORD"]
    assert len(dup_findings) == 1
    assert "Duplicate Publisher Record Detected" in dup_findings[0].title
    assert score1.has_duplicates is True
    assert score1.consistency_score < 100.0


@pytest.mark.asyncio
async def test_field_level_freshness_tracking(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Freshness Test {suffix}",
        canonical_domain=f"freshness-{suffix}.com",
        industry="SaaS"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://freshness-{suffix}.com",
        publisher_name="Freshness Pub",
        audience_focus="SaaS"
    )
    db_session.add(pub)
    await db_session.commit()

    # Create observation 45 days ago (Price stale > 30 days, metrics fresh <= 60 days)
    obs_45_days = PublisherObservation(
        publisher_id=pub.id,
        price=350.0,
        currency="USD",
        metric_da=45.0,
        observation_timestamp=datetime.now(timezone.utc) - timedelta(days=45),
        source_name="Old Import Batch",
        verification_status="UNVERIFIED"
    )
    db_session.add(obs_45_days)
    await db_session.commit()

    service = PublisherQualityService(db_session)
    score, findings = await service.audit_publisher(pub.id)

    assert score.price_freshness_status == "STALE"
    assert score.metrics_freshness_status == "FRESH"
    stale_price = [f for f in findings if f.field_name == "price" and f.issue_type == "STALE_DATA"]
    assert len(stale_price) == 1
    assert "Stale Pricing Data" in stale_price[0].title


@pytest.mark.asyncio
async def test_historical_observations_preservation(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"History Preservation {suffix}",
        canonical_domain=f"history-{suffix}.com",
        industry="Finance"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://history-{suffix}.com",
        publisher_name="History Pub",
        audience_focus="Finance"
    )
    db_session.add(pub)
    await db_session.commit()

    # Initial Observation
    obs1 = PublisherObservation(
        publisher_id=pub.id,
        price=200.0,
        currency="USD",
        metric_da=30.0,
        observation_timestamp=datetime.now(timezone.utc) - timedelta(days=70),
        source_name="Batch 1",
        verification_status="UNVERIFIED"
    )
    db_session.add(obs1)
    await db_session.commit()

    service = PublisherQualityService(db_session)

    # Apply manual correction with updated price
    new_obs = await service.apply_manual_correction(
        publisher_id=pub.id,
        price=350.0,
        currency="USD",
        metric_da=38.0,
        notes="Verified 2026 media kit rate card from publisher direct",
        actor="senior_media_planner"
    )

    # VERIFY: Historical observation was NOT deleted or overwritten!
    from sqlalchemy import select
    all_obs = (await db_session.execute(
        select(PublisherObservation).where(PublisherObservation.publisher_id == pub.id)
    )).scalars().all()

    assert len(all_obs) == 2
    prices = [o.price for o in all_obs]
    assert 200.0 in prices
    assert 350.0 in prices
    assert new_obs.verification_status == "HUMAN_VERIFIED"
    assert "senior_media_planner" in new_obs.source_name

    # Check CRMActivity logged
    act = (await db_session.execute(
        select(CRMActivity).where(
            CRMActivity.company_id == company.id,
            CRMActivity.activity_type == "PUBLISHER_CORRECTION"
        )
    )).scalar_one_or_none()
    assert act is not None
    assert act.actor == "senior_media_planner"


@pytest.mark.asyncio
async def test_price_currency_validation_and_conflicts(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Price Conflict {suffix}",
        canonical_domain=f"conflict-{suffix}.com",
        industry="Retail"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://conflict-{suffix}.com",
        publisher_name="Conflict Pub",
        audience_focus="Retail"
    )
    db_session.add(pub)
    await db_session.commit()

    # Two conflicting observations with divergent prices ($100 vs $600)
    obs1 = PublisherObservation(
        publisher_id=pub.id,
        price=100.0,
        currency="USD",
        metric_da=50.0,
        observation_timestamp=datetime.now(timezone.utc) - timedelta(days=10),
        source_name="Vendor A Import"
    )
    obs2 = PublisherObservation(
        publisher_id=pub.id,
        price=600.0,
        currency="USD",
        metric_da=50.0,
        observation_timestamp=datetime.now(timezone.utc) - timedelta(days=5),
        source_name="Vendor B Import"
    )
    db_session.add_all([obs1, obs2])
    await db_session.commit()

    service = PublisherQualityService(db_session)
    score, findings = await service.audit_publisher(pub.id)

    conflict_findings = [f for f in findings if f.issue_type == "CONFLICTING_DATA" and f.field_name == "price"]
    assert len(conflict_findings) == 1
    assert "Conflicting Price Observations" in conflict_findings[0].title
    assert score.has_conflicts is True


@pytest.mark.asyncio
async def test_provider_refresh_safety_and_non_fabrication(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Provider Refresh Safety {suffix}",
        canonical_domain=f"safety-{suffix}.com",
        industry="Health"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://safety-{suffix}.com",
        publisher_name="Safety Pub",
        audience_focus="Health"
    )
    db_session.add(pub)
    await db_session.commit()

    service = PublisherQualityService(db_session)
    # Refresh without API keys configured must gracefully report PROVIDER_NOT_CONFIGURED and NOT crash or fabricate!
    res = await service.refresh_publisher(publisher_id=pub.id, target_fields=["metrics"], actor="test_user")

    assert res["metrics"]["status"] == "PROVIDER_NOT_CONFIGURED"

    # Verify log recorded
    from sqlalchemy import select
    log = (await db_session.execute(
        select(PublisherRefreshLog).where(PublisherRefreshLog.publisher_id == pub.id)
    )).scalar_one_or_none()

    assert log is not None
    assert log.status == "PROVIDER_NOT_CONFIGURED"
    assert "API credentials" in log.error_message


@pytest.mark.asyncio
async def test_finding_resolution_workflow(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Resolve Finding {suffix}",
        canonical_domain=f"resolve-{suffix}.com",
        industry="Education"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://resolve-{suffix}.com",
        publisher_name="Resolve Pub",
        audience_focus="" # Missing audience focus
    )
    db_session.add(pub)
    await db_session.commit()

    service = PublisherQualityService(db_session)
    score, findings = await service.audit_publisher(pub.id)

    missing_niche = next((f for f in findings if f.field_name == "audience_focus"), None)
    assert missing_niche is not None
    assert missing_niche.status == "OPEN"

    # Resolve finding
    resolved = await service.resolve_finding(
        finding_id=missing_niche.id,
        action="ACCEPTED_VALUE",
        notes="General news publication covers all educational topics broadly",
        actor="content_lead"
    )

    assert resolved.status == "RESOLVED"
    assert resolved.resolved_by == "content_lead"
    assert "General news" in resolved.resolution_notes


@pytest.mark.asyncio
async def test_matching_engine_recognizes_stale_data(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Matching Target {suffix}",
        canonical_domain=f"target-{suffix}.com",
        industry="Cybersecurity"
    )
    pub_company = Company(
        company_name=f"Stale Pub Company {suffix}",
        canonical_domain=f"stalepub-{suffix}.com",
        industry="Cybersecurity"
    )
    db_session.add_all([company, pub_company])
    await db_session.commit()

    pub = PublisherRecord(
        company_id=pub_company.id,
        original_submitted_url=f"https://stalepub-{suffix}.com",
        publisher_name=f"Cyber Daily {suffix}",
        audience_focus="Cybersecurity"
    )
    db_session.add(pub)
    await db_session.commit()

    # Observation from 90 days ago (> 60 days threshold) and unverified
    stale_obs = PublisherObservation(
        publisher_id=pub.id,
        price=400.0,
        currency="USD",
        metric_da=60.0,
        observation_timestamp=datetime.now(timezone.utc) - timedelta(days=90),
        source_name="Old Vendor File",
        verification_status="UNVERIFIED"
    )
    db_session.add(stale_obs)
    await db_session.commit()

    engine = MatchingEngine(db_session)
    match_run = await engine.run_matching(company.id)

    from sqlalchemy import select
    results = (await db_session.execute(
        select(MatchResult).where(MatchResult.matching_run_id == match_run.id)
    )).scalars().all()

    target_match = next((r for r in results if r.publisher_id == pub.id), None)
    assert target_match is not None

    # Matching engine MUST include warnings for unverified and stale data!
    warnings_text = " ".join(target_match.warnings)
    assert "unverified" in warnings_text.lower()
    assert "stale" in warnings_text.lower()


@pytest.mark.asyncio
async def test_publisher_quality_api_endpoints(db_session):
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"API Quality Test {suffix}",
        canonical_domain=f"apiquality-{suffix}.com",
        industry="Fintech"
    )
    db_session.add(company)
    await db_session.commit()

    pub = PublisherRecord(
        company_id=company.id,
        original_submitted_url=f"https://apiquality-{suffix}.com",
        publisher_name="API Quality Pub",
        audience_focus="Fintech"
    )
    db_session.add(pub)
    await db_session.commit()

    obs = PublisherObservation(
        publisher_id=pub.id,
        price=150.0,
        currency="USD",
        metric_da=42.0,
        observation_timestamp=datetime.now(timezone.utc),
        source_name="API Test",
        verification_status="VERIFIED"
    )
    db_session.add(obs)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Summary Endpoint
        res_sum = await client.get("/publishers/quality/summary")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert "total_publishers" in data_sum
        assert "average_quality_score" in data_sum

        # 2. Single Publisher Audit
        res_audit = await client.post(f"/publishers/{pub.id}/audit")
        assert res_audit.status_code == 200
        assert res_audit.json()["overall_quality_score"] > 0

        # 3. Detailed Dossier
        res_dossier = await client.get(f"/publishers/{pub.id}/quality")
        assert res_dossier.status_code == 200
        data_dossier = res_dossier.json()
        assert data_dossier["publisher_name"] == "API Quality Pub"
        assert "observations_history" in data_dossier
        assert "field_freshness" in data_dossier

        # 4. List Findings
        res_findings = await client.get("/publishers/quality/findings")
        assert res_findings.status_code == 200
        assert isinstance(res_findings.json(), list)

        # 5. Attributable Manual Correction
        res_corr = await client.post(
            f"/publishers/{pub.id}/correction",
            json={
                "price": 275.0,
                "currency": "USD",
                "metric_da": 48.0,
                "notes": "Direct confirmation with editorial team",
                "actor": "api_test_editor"
            }
        )
        assert res_corr.status_code == 200
        assert res_corr.json()["price"] == 275.0
        assert res_corr.json()["verification_status"] == "HUMAN_VERIFIED"
