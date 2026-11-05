import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func

from app.db.session import async_session_maker
from app.models import Company, CRMActivity
from app.models.scraper import ScraperTask, ExtractedRecord
from app.models.crm import CRMLeadSegment, CRMSegmentMember, CRMUserPreference, CRMFeedbackLog, CRMAIResearch
from app.services.crm.bridge import ScraperCRMBridge, extract_canonical_domain, compute_lead_score
from app.services.crm.learning import AdaptiveLearningService
from app.services.crm.assistant import CRMAssistantService
from app.schemas.crm import ScraperImportRequest, AIAssistantQueryRequest


@pytest.mark.asyncio
async def test_canonical_domain_and_score_computation():
    """Verify URL normalization and transparent 4-pillar scoring logic."""
    url1 = "https://www.ecom-store.mx/products?sort=price"
    assert extract_canonical_domain(url1) == "ecom-store.mx"

    url2 = "http://api.subdomain.example.co.uk:8080/path"
    assert extract_canonical_domain(url2) == "api.subdomain.example.co.uk"

    # Multi-pillar scoring
    score_data = {
        "company_name": "Zapatería Moderna",
        "website_url": "https://zapateriamoderna.mx",
        "industry": "E-Commerce",
        "country": "Mexico",
        "city": "Guadalajara",
        "description": "Leading footwear retailer offering online catalog and regional shipping across Mexico.",
        "public_email": "ventas@zapateriamoderna.mx",
        "phone_number": "+52-33-3812-4455",
        "linkedin_url": "https://linkedin.com/company/zapateria-moderna"
    }
    score, breakdown = compute_lead_score(score_data)

    assert 60.0 <= score <= 100.0
    assert "contact_reachability" in breakdown
    assert "profile_completeness" in breakdown
    assert "website_viability" in breakdown
    assert "seo_opportunity" in breakdown
    assert breakdown["contact_reachability"]["signals"]["has_email"] is True


@pytest.mark.asyncio
async def test_scraper_to_crm_import_and_deduplication():
    """Verify that extracted records save into CRM with canonical domain deduplication and activity history."""
    async with async_session_maker() as session:
        # Create a test task and extracted record
        task = ScraperTask(
            name="Mexico E-Commerce Discovery Test",
            task_type="DISCOVERY",
            status="COMPLETED"
        )
        session.add(task)
        await session.flush()

        test_domain = f"test-store-{uuid.uuid4().hex[:6]}.mx"
        test_company = f"Mexican Retail Test {uuid.uuid4().hex[:6]}"
        rec1 = ExtractedRecord(
            task_id=task.id,
            record_hash=uuid.uuid4().hex,
            company_name=test_company,
            domain=test_domain,
            website=f"https://{test_domain}",
            email=f"info@{test_domain}",
            country="Mexico",
            industry="E-Commerce",
            source_url=f"https://www.{test_domain}/catalog",
            discovery_source="SERP",
            validation_status="VALID",
            quality_score=85,
            quality_status="HIGH",
            cleaned_data={
                "company_name": test_company,
                "website_url": f"https://{test_domain}",
                "public_email": f"info@{test_domain}",
                "country": "Mexico",
                "industry": "E-Commerce"
            }
        )
        session.add(rec1)
        await session.commit()

        bridge = ScraperCRMBridge(session)

        # 1. First Import
        res1 = await bridge.import_extracted_records(ScraperImportRequest(
            extracted_record_ids=[rec1.id],
            default_stage="NEW",
            tags=["mexico", "e-commerce"]
        ))

        assert res1.success is True
        assert res1.added == 1
        assert res1.updated == 0

        # Verify company created
        stmt = select(Company).where(Company.canonical_domain == test_domain)
        comp = (await session.execute(stmt)).scalars().first()
        assert comp is not None
        assert comp.sales_stage == "NEW"
        assert comp.lead_source == "SCRAPER"
        assert "mexico" in comp.tags

        # Verify activity timeline
        act_stmt = select(CRMActivity).where(CRMActivity.company_id == comp.id)
        activities = (await session.execute(act_stmt)).scalars().all()
        assert len(activities) >= 1
        assert activities[0].activity_type == "LEAD_IMPORTED_FROM_SCRAPER"

        # 2. Second Import with same domain (should deduplicate & merge)
        rec2 = ExtractedRecord(
            task_id=task.id,
            record_hash=uuid.uuid4().hex,
            company_name="Mexican Retail Test Updated",
            domain=test_domain,
            website=f"https://{test_domain}",
            phone="+52-55-1234-5678",
            description="Updated company description",
            source_url=f"https://{test_domain}/about",
            discovery_source="SERP",
            validation_status="VALID",
            quality_score=90,
            quality_status="HIGH",
            cleaned_data={
                "company_name": "Mexican Retail Test Updated",
                "phone_number": "+52-55-1234-5678",
                "description": "Updated company description"
            }
        )
        session.add(rec2)
        await session.commit()

        res2 = await bridge.import_extracted_records(ScraperImportRequest(
            extracted_record_ids=[rec2.id],
            conflict_resolution="MERGE"
        ))

        assert res2.added == 0
        assert res2.updated == 1

        # Verify no duplicate Company was created
        comp_count = (await session.execute(
            select(func.count(Company.id)).where(Company.canonical_domain == test_domain)
        )).scalar()
        assert comp_count == 1


@pytest.mark.asyncio
async def test_adaptive_learning_feedback_loop():
    """Verify that reviewer stage updates and qualifications adapt scoring weights and log feedback."""
    async with async_session_maker() as session:
        # Create test company
        comp = Company(
            company_name="AutoLearning Prospect",
            canonical_domain=f"learning-{uuid.uuid4().hex[:6]}.com",
            country="Mexico",
            industry="Healthcare",
            sales_stage="NEW",
            lead_score=72.0,
            public_email="doctor@learning-health.com"
        )
        session.add(comp)
        await session.commit()

        learn_svc = AdaptiveLearningService(session)

        # 1. Log qualification feedback
        feedback = await learn_svc.log_user_feedback(
            company_id=comp.id,
            action_taken="QUALIFIED",
            previous_stage="NEW",
            new_stage="QUALIFIED",
            feedback_reason="Excellent medical directory lead with verified direct email."
        )

        assert feedback.action_taken == "QUALIFIED"
        assert feedback.company_id == comp.id

        # 2. Check updated user preferences
        pref = await learn_svc.get_or_create_user_preferences()
        assert "Healthcare" in pref.preferred_industries
        assert "Mexico" in pref.preferred_countries

        # 3. Retrieve explainable insights
        insights = await learn_svc.get_adaptive_insights()
        assert insights["total_feedback_events"] >= 1
        assert insights["qualified_count"] >= 1
        assert len(insights["learned_patterns"]) >= 1

        # 4. Reset preferences
        reset_pref = await learn_svc.reset_preferences()
        assert reset_pref.preferred_industries == []
        assert reset_pref.min_lead_score == 50.0


@pytest.mark.asyncio
async def test_ai_intelligence_assistant_and_deep_research():
    """Verify natural language CRM querying and automated AI company research generation."""
    async with async_session_maker() as session:
        # Create a test company
        test_domain = f"ai-target-{uuid.uuid4().hex[:6]}.com"
        comp = Company(
            company_name="AI Target Enterprise",
            canonical_domain=test_domain,
            website_url=f"https://{test_domain}",
            industry="Software",
            country="United States",
            sales_stage="QUALIFIED",
            lead_score=88.0,
            lead_priority="HIGH",
            public_email=f"ceo@{test_domain}"
        )
        session.add(comp)
        await session.commit()

        assistant_svc = CRMAssistantService(session)

        # 1. Query assistant
        query_res = await assistant_svc.query_intelligence(AIAssistantQueryRequest(
            query="Show me qualified software companies in the USA"
        ))

        assert query_res.confidence >= 0.9
        assert len(query_res.matched_leads) >= 1
        matched_names = [m["company_name"] for m in query_res.matched_leads]
        assert "AI Target Enterprise" in matched_names

        # 2. Run Deep AI Company Research
        research = await assistant_svc.analyze_lead_with_ai(comp.id)

        assert research.company_id == comp.id
        assert research.executive_summary is not None
        assert len(research.seo_weaknesses) >= 2
        assert len(research.backlink_opportunities) >= 2
        assert len(research.recommended_services) >= 2

        # Verify research persisted in database
        saved_research = (await session.execute(
            select(CRMAIResearch).where(CRMAIResearch.company_id == comp.id)
        )).scalars().first()
        assert saved_research is not None
        assert saved_research.id == research.id


@pytest.mark.asyncio
async def test_dynamic_lead_segments():
    """Verify dynamic segment creation and rule-based lead count evaluation."""
    async with async_session_maker() as session:
        # Create a dynamic segment
        seg = CRMLeadSegment(
            name="High Score Software Test Segment",
            description="Software companies with score >= 75",
            is_dynamic=True,
            filter_criteria={"industry": "Software", "min_score": 75}
        )
        session.add(seg)
        await session.commit()
        await session.refresh(seg)

        # Query matching leads
        crit = seg.filter_criteria
        stmt = select(func.count(Company.id)).where(
            Company.industry.ilike(f"%{crit['industry']}%"),
            Company.lead_score >= float(crit["min_score"])
        )
        count = (await session.execute(stmt)).scalar() or 0
        assert count >= 1  # From previous test
