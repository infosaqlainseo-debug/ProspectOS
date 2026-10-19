import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models import Company, SEOMetric, WebsiteScan, AIObservation, OpportunityProfile
from app.services.intelligence.opportunity import OpportunityEngine

def get_utc_now():
    return datetime.now(timezone.utc)

@pytest.mark.asyncio
async def test_opportunity_engine_missing_data(db_session):
    company = Company(id=uuid.uuid4(), company_name="Test Missing Data")
    db_session.add(company)
    await db_session.commit()
    
    engine = OpportunityEngine(db_session)
    profile = await engine.evaluate_company(company.id)
    
    assert profile.opportunity_score == 50.0
    assert profile.confidence_level == 0.0
    assert len(profile.missing_information) == 4
    assert "Website scan data is missing" in profile.missing_information
    assert "Domain Rating / Authority Score is missing" in profile.missing_information
    assert "Organic traffic data is missing" in profile.missing_information
    assert profile.data_freshness == "FRESH"
    assert profile.recommended_next_action == "Collect missing data"

@pytest.mark.asyncio
async def test_opportunity_engine_tech_seo(db_session):
    company = Company(id=uuid.uuid4(), company_name="Tech SEO Issue")
    db_session.add(company)
    await db_session.commit()
    
    # Add bad scan
    scan = WebsiteScan(
        company_id=company.id,
        url="http://test.com",
        http_status=404,
        https_enabled=False,
        scan_status="COMPLETED"
    )
    db_session.add(scan)
    await db_session.commit()
    
    engine = OpportunityEngine(db_session)
    profile = await engine.evaluate_company(company.id)
    
    assert profile.recommended_service == "Technical SEO"
    assert profile.opportunity_score == 100.0
    assert "Website did not return 200 OK" in profile.identified_problems
    assert "HTTPS is not enabled" in profile.identified_problems

@pytest.mark.asyncio
async def test_opportunity_engine_stale_metrics(db_session):
    company = Company(id=uuid.uuid4(), company_name="Stale Data")
    db_session.add(company)
    await db_session.commit()
    
    # 40 days ago
    stale_date = get_utc_now() - timedelta(days=40)
    metric = SEOMetric(
        company_id=company.id,
        metric_name="domain_rating",
        metric_value=20,
        provider="ahrefs",
        verification_status="VERIFIED",
        retrieved_at=stale_date
    )
    db_session.add(metric)
    await db_session.commit()
    
    engine = OpportunityEngine(db_session)
    profile = await engine.evaluate_company(company.id)
    
    assert profile.data_freshness == "STALE"

@pytest.mark.asyncio
async def test_opportunity_engine_link_building_vs_content(db_session):
    company = Company(id=uuid.uuid4(), company_name="Link Build vs Content")
    db_session.add(company)
    await db_session.commit()
    
    metric = SEOMetric(
        company_id=company.id,
        metric_name="domain_rating",
        metric_value=20,
        provider="ahrefs",
        verification_status="VERIFIED"
    )
    db_session.add(metric)
    
    obs = AIObservation(
        company_id=company.id,
        extraction_run_id=uuid.uuid4(),
        attribute_name="content_quality",
        attribute_value="POOR",
        verification_status="VERIFIED"
    )
    # fake extraction run for constraint
    from app.models import AIExtractionRun
    run = AIExtractionRun(id=obs.extraction_run_id, company_id=company.id, provider="test", model="test", prompt_version="1", schema_version="1", status="COMPLETED")
    db_session.add(run)
    db_session.add(obs)
    await db_session.commit()
    
    engine = OpportunityEngine(db_session)
    profile = await engine.evaluate_company(company.id)
    
    # Content quality issue should override link building
    assert profile.recommended_service == "Content strategy"

@pytest.mark.asyncio
async def test_opportunity_engine_scoring_reproducibility(db_session):
    company = Company(id=uuid.uuid4(), company_name="Repro")
    db_session.add(company)
    await db_session.commit()
    
    engine = OpportunityEngine(db_session)
    profile1 = await engine.evaluate_company(company.id)
    profile2 = await engine.evaluate_company(company.id)
    
    assert profile1.opportunity_score == profile2.opportunity_score
    assert profile1.recommended_service == profile2.recommended_service
    assert profile1.confidence_level == profile2.confidence_level
