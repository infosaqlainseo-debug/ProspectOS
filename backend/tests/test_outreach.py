import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.db.session import async_session_maker
from app.models import (
    Company, CompanyContact, WebsiteScan, OpportunityProfile,
    MediaPlan, MediaPlanItem, PublisherRecord, OutreachCampaign,
    OutreachDraft, OutreachMessage, OutreachSuppression
)
from app.services.outreach.contacts import ContactResearcher
from app.services.outreach.personalization import OutreachPersonalizationEngine
from app.services.outreach.sender import OutreachSenderService
from app.services.outreach.providers.registry import email_registry
from app.services.outreach.providers.mock import MockEmailProvider


@pytest.mark.asyncio
async def test_contact_validation_and_provenance(db_session):
    """Test contact validation, extraction from website scan, provenance and non-fabrication."""
    suffix = uuid.uuid4().hex[:6]
    
    # 1. Email validation checks
    assert ContactResearcher.is_valid_email("editor@techcrunch.com") is True
    assert ContactResearcher.is_valid_email("invalid-email") is False
    assert ContactResearcher.is_valid_email("image@logo.png") is False
    assert ContactResearcher.is_valid_email("test@example.com") is False
    
    # 2. Company with website scan containing mailto / metadata email
    company = Company(
        company_name=f"Venture Corp {suffix}",
        canonical_domain=f"venture-{suffix}.com"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://venture-{suffix}.com",
        title="Venture Corp Innovations",
        meta_description=f"Inquiries welcome at press@venture-{suffix}.com for media kits.",
        scan_status="COMPLETED"
    )
    db_session.add(scan)
    await db_session.commit()

    researcher = ContactResearcher(db_session)
    contacts = await researcher.discover_company_contacts(company.id)

    assert len(contacts) > 0
    press_contact = next((c for c in contacts if c.email == f"press@venture-{suffix}.com"), None)
    assert press_contact is not None
    assert press_contact.source_type == "WEBSITE_PAGE"
    assert press_contact.verification_status == "VERIFIED"
    assert press_contact.confidence >= 0.8
    assert press_contact.retrieval_timestamp is not None
    assert press_contact.opt_out is False


@pytest.mark.asyncio
async def test_inferred_contact_fallback_non_fabrication(db_session):
    """When no email is found in metadata, fallback must be marked INFERRED with low confidence."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Silent Corp {suffix}",
        canonical_domain=f"silent-{suffix}.com"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    researcher = ContactResearcher(db_session)
    contacts = await researcher.discover_company_contacts(company.id)

    assert len(contacts) == 1
    fallback = contacts[0]
    assert fallback.email == f"contact@silent-{suffix}.com"
    assert fallback.source_type == "INFERRED_ROLE"
    assert fallback.verification_status == "INFERRED"
    assert fallback.confidence <= 0.5


@pytest.mark.asyncio
async def test_evidence_based_personalization_non_fabrication(db_session):
    """Verify that every claim in outreach drafts traces to evidence and missing metrics are not fabricated."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"CloudScale {suffix}",
        canonical_domain=f"cloudscale-{suffix}.com",
        industry="Enterprise SaaS"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Add Scan
    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://cloudscale-{suffix}.com",
        title=f"CloudScale Enterprise Platform {suffix}",
        https_enabled=True,
        scan_status="COMPLETED"
    )
    db_session.add(scan)

    # Add Opportunity Profile with explicit identified problems
    opp = OpportunityProfile(
        company_id=company.id,
        recommended_service="Technical SEO",
        opportunity_score=85.0,
        identified_problems=["Missing H1 tags", "Robots.txt issue"],
        confidence_level=0.9,
        data_freshness="FRESH",
        methodology_version="1.8.0"
    )
    db_session.add(opp)

    # Add Media Plan with recommended publisher
    pub_co = Company(canonical_domain=f"saas-daily-{suffix}.com", company_name=f"SaaS Daily {suffix}")
    db_session.add(pub_co)
    await db_session.commit()
    await db_session.refresh(pub_co)

    pub = PublisherRecord(company_id=pub_co.id, publisher_name=f"SaaS Daily {suffix}")
    db_session.add(pub)
    await db_session.commit()
    await db_session.refresh(pub)

    plan = MediaPlan(company_id=company.id, name=f"Plan {suffix}", status="DRAFT")
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    item = MediaPlanItem(media_plan_id=plan.id, publisher_id=pub.id, proposed_price=350.0)
    db_session.add(item)
    await db_session.commit()

    engine = OutreachPersonalizationEngine(db_session)
    draft_data = await engine.generate_draft(company_id=company.id, save=False)

    # Verify message contents and non-fabrication
    assert f"CloudScale {suffix}" in draft_data["subject_line"]
    assert "Enterprise SaaS" in draft_data["body_text"]
    assert "Technical SEO" in draft_data["body_text"]
    assert f"SaaS Daily {suffix}" in draft_data["body_text"]
    
    # Evidence citations verification
    citations = draft_data["evidence_citations"]
    assert len(citations) >= 3
    source_types = [c["source_type"] for c in citations]
    assert "WebsiteScan" in source_types
    assert "OpportunityProfile" in source_types
    assert "MediaPlan" in source_types


@pytest.mark.asyncio
async def test_human_approval_boundary(db_session):
    """Sending an unapproved draft must be blocked immediately."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Target {suffix}", canonical_domain=f"target-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    draft = OutreachDraft(
        company_id=company.id,
        recipient_email=f"ceo@target-{suffix}.com",
        subject_line="Growth Opportunity",
        body_text="Hello, here is our proposal.",
        status="DRAFT",
        approval_status="UNAPPROVED" # Unapproved!
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    sender = OutreachSenderService(db_session)
    
    # Attempting to send unapproved draft must raise ValueError
    with pytest.raises(ValueError, match="Explicit human approval.*is mandatory"):
        await sender.send_draft(draft.id)


@pytest.mark.asyncio
async def test_duplicate_send_prevention(db_session):
    """Drafts that have already been sent cannot be sent again."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Target {suffix}", canonical_domain=f"target-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    draft = OutreachDraft(
        company_id=company.id,
        recipient_email=f"contact@target-{suffix}.com",
        subject_line="Growth Opportunity",
        body_text="Hello, here is our proposal.",
        status="SENT",
        approval_status="APPROVED",
        sent_at=datetime.now(timezone.utc)
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    sender = OutreachSenderService(db_session)
    with pytest.raises(ValueError, match="Draft .* has already been sent"):
        await sender.send_draft(draft.id)


@pytest.mark.asyncio
async def test_opt_out_and_suppression_enforcement(db_session):
    """Recipients or domains on suppression list are blocked from all sends."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"OptOut Corp {suffix}", canonical_domain=f"optout-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    target_email = f"lead@optout-{suffix}.com"
    suppression = OutreachSuppression(
        email=target_email,
        domain=f"optout-{suffix}.com",
        reason="UNSUBSCRIBED"
    )
    db_session.add(suppression)

    draft = OutreachDraft(
        company_id=company.id,
        recipient_email=target_email,
        subject_line="Pitch",
        body_text="Proposal details...",
        status="APPROVED",
        approval_status="APPROVED"
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    sender = OutreachSenderService(db_session)
    with pytest.raises(ValueError, match="opt-out / suppression list"):
        await sender.send_draft(draft.id)

    # Verify draft was updated to CANCELLED
    await db_session.refresh(draft)
    assert draft.status == "CANCELLED"


@pytest.mark.asyncio
async def test_follow_up_scheduling_and_cancellation(db_session):
    """Verified follow-up creation and subsequent cancellation upon reply/opt-out."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Sequenced {suffix}", canonical_domain=f"sequenced-{suffix}.com")
    campaign = OutreachCampaign(
        name=f"Campaign {suffix}",
        follow_up_delay_days=3,
        max_follow_ups=2
    )
    db_session.add(company)
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(company)
    await db_session.refresh(campaign)

    target_email = f"founder@sequenced-{suffix}.com"
    draft = OutreachDraft(
        campaign_id=campaign.id,
        company_id=company.id,
        recipient_email=target_email,
        subject_line="Partnership Discussion",
        body_text="Initial note...",
        status="APPROVED",
        approval_status="APPROVED",
        sequence_step=1
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    # Temporarily set active provider to Mock for this test
    mock_prov = MockEmailProvider()
    email_registry._providers["mock"] = mock_prov
    from app.core.config import settings
    orig_prov = settings.EMAIL_PROVIDER
    settings.EMAIL_PROVIDER = "mock"

    try:
        sender = OutreachSenderService(db_session)
        res = await sender.send_draft(draft.id)
        assert res.success is True

        # Check that follow-up draft was created
        stmt_fu = select(OutreachDraft).where(
            OutreachDraft.parent_draft_id == draft.id,
            OutreachDraft.is_follow_up == True
        )
        follow_up = (await db_session.execute(stmt_fu)).scalars().first()
        assert follow_up is not None
        assert follow_up.sequence_step == 2
        assert follow_up.approval_status == "UNAPPROVED" # Must be unapproved!
        assert "Following up:" in follow_up.subject_line

        # Now simulate prospect reply or manual cancellation
        await sender.cancel_follow_ups(company.id, target_email, reason="Prospect replied to initial note")

        await db_session.refresh(follow_up)
        assert follow_up.status == "CANCELLED"
        assert "Prospect replied" in follow_up.error_message
    finally:
        settings.EMAIL_PROVIDER = orig_prov


@pytest.mark.asyncio
async def test_unconfigured_provider_safeguard(db_session):
    """When email provider is not configured, send is aborted safely with descriptive missing fields."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Safety {suffix}", canonical_domain=f"safety-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    draft = OutreachDraft(
        company_id=company.id,
        recipient_email=f"hello@safety-{suffix}.com",
        subject_line="Audit",
        body_text="Text...",
        status="APPROVED",
        approval_status="APPROVED"
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    from app.core.config import settings
    orig_prov = settings.EMAIL_PROVIDER
    settings.EMAIL_PROVIDER = "none"

    try:
        sender = OutreachSenderService(db_session)
        result = await sender.send_draft(draft.id)
        assert result.success is False
        assert "PROVIDER_NOT_CONFIGURED" in result.error
        
        await db_session.refresh(draft)
        assert draft.status == "FAILED"
    finally:
        settings.EMAIL_PROVIDER = orig_prov


@pytest.mark.asyncio
async def test_api_draft_approve_reject_and_preview():
    """Test REST API endpoints for draft generation preview, approval, and rejection."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        co = Company(company_name=f"API Test {suffix}", canonical_domain=f"apitest-{suffix}.com")
        session.add(co)
        await session.commit()
        await session.refresh(co)
        co_id = str(co.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Preview draft without saving
        prev_resp = await client.post("/outreach/drafts/generate", json={
            "company_id": co_id,
            "save_draft": False
        })
        assert prev_resp.status_code == 200
        prev_data = prev_resp.json()
        assert prev_data["company_name"] == f"API Test {suffix}"
        assert prev_data["recipient_email"] == f"contact@apitest-{suffix}.com"
        assert len(prev_data["evidence_citations"]) >= 0

        # 2. Save draft
        save_resp = await client.post("/outreach/drafts/generate", json={
            "company_id": co_id,
            "save_draft": True
        })
        assert save_resp.status_code == 200
        draft_id = save_resp.json()["id"]

        # 3. Approve draft
        appr_resp = await client.post(f"/outreach/drafts/{draft_id}/approve", json={
            "approved_by": "lead_strategist",
            "notes": "Verified facts against scan"
        })
        assert appr_resp.status_code == 200
        assert appr_resp.json()["approval_status"] == "APPROVED"
        assert appr_resp.json()["approved_by"] == "lead_strategist"

        # 4. Reject draft
        rej_resp = await client.post(f"/outreach/drafts/{draft_id}/reject", json={
            "rejected_by": "qa_reviewer",
            "reason": "Target changed"
        })
        assert rej_resp.status_code == 200
        assert rej_resp.json()["approval_status"] == "REJECTED"
        assert rej_resp.json()["rejection_reason"] == "Target changed"
