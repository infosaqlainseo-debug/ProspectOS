import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.db.session import async_session_maker
from app.models import (
    Company, CompanyContact, WebsiteScan, OpportunityProfile,
    MediaPlan, OutreachDraft, OutreachMessage,
    CRMDeal, CRMTask, CRMActivity, CRMNote
)
from app.schemas.crm import DealCreate, DealUpdate, TaskCreate, TaskCompleteRequest, NoteCreate
from app.services.crm.service import CRMService


@pytest.mark.asyncio
async def test_crm_stage_transitions_and_history(db_session):
    """Test prospect sales stage transitions, validation, and activity logging."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"CRM Test Corp {suffix}",
        canonical_domain=f"crm-test-{suffix}.com",
        sales_stage="NEW"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = CRMService(db_session)

    # 1. Valid transition: NEW -> RESEARCHED
    updated = await service.update_prospect_stage(
        company_id=company.id,
        new_stage="RESEARCHED",
        reason="Website crawled and tech stack analyzed",
        actor="analyst_1"
    )
    assert updated.sales_stage == "RESEARCHED"
    assert updated.stage_reason == "Website crawled and tech stack analyzed"

    # Check activity audit trail
    stmt_act = select(CRMActivity).where(CRMActivity.company_id == company.id)
    activities = (await db_session.execute(stmt_act)).scalars().all()
    assert len(activities) == 1
    act = activities[0]
    assert act.activity_type == "STAGE_CHANGE"
    assert act.actor == "analyst_1"
    assert act.details["old_stage"] == "NEW"
    assert act.details["new_stage"] == "RESEARCHED"

    # 2. Invalid stage name must raise ValueError
    with pytest.raises(ValueError, match="Invalid sales stage"):
        await service.update_prospect_stage(company.id, "NOT_A_STAGE")

    # 3. Transition to QUALIFIED
    await service.update_prospect_stage(company.id, "QUALIFIED", notes="High SEO opportunity score")
    await db_session.refresh(company)
    assert company.sales_stage == "QUALIFIED"
    assert company.qualification_notes == "High SEO opportunity score"


@pytest.mark.asyncio
async def test_crm_deal_management_and_revenue_integrity(db_session):
    """Test deal lifecycle, stage transitions, won/lost tracking, and distinction between pipeline vs revenue."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Deal Corp {suffix}",
        canonical_domain=f"deal-{suffix}.com"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = CRMService(db_session)

    # 1. Create Deal
    deal_in = DealCreate(
        company_id=company.id,
        deal_name="Enterprise Technical SEO Retainer",
        service_category="TECHNICAL_SEO",
        stage="DISCOVERY",
        estimated_value=12500.0,
        currency="USD"
    )
    deal = await service.create_deal(deal_in, actor="sales_lead")
    assert deal.deal_name == "Enterprise Technical SEO Retainer"
    assert deal.estimated_value == 12500.0
    assert deal.currency == "USD"
    assert deal.stage == "DISCOVERY"

    # 2. Update to PROPOSAL with proposed value
    deal_up = DealUpdate(
        stage="PROPOSAL",
        proposed_value=15000.0,
        notes="Proposed 6-month publisher outreach bundle"
    )
    deal = await service.update_deal(deal.id, deal_up)
    assert deal.stage == "PROPOSAL"
    assert deal.proposed_value == 15000.0

    # 3. Close Deal as WON
    deal_won = DealUpdate(
        stage="WON",
        closed_amount=15000.0,
        win_reason="Demonstrated clear publisher inventory quality",
        actor="sales_lead"
    )
    deal = await service.update_deal(deal.id, deal_won)
    assert deal.stage == "WON"
    assert deal.outcome == "WON"
    assert deal.closed_amount == 15000.0
    assert deal.actual_close_date is not None

    # Verify company sales_stage automatically synced to WON
    await db_session.refresh(company)
    assert company.sales_stage == "WON"

    # Check DEAL_WON activity log
    stmt_act = select(CRMActivity).where(
        CRMActivity.deal_id == deal.id,
        CRMActivity.activity_type == "DEAL_WON"
    )
    act_won = (await db_session.execute(stmt_act)).scalars().first()
    assert act_won is not None
    assert act_won.details["closed_amount"] == 15000.0

    # 4. Create another deal and close as LOST
    deal_in2 = DealCreate(
        company_id=company.id,
        deal_name="Content Strategy Add-on",
        service_category="CONTENT_STRATEGY",
        estimated_value=5000.0
    )
    deal2 = await service.create_deal(deal_in2)
    deal_lost = DealUpdate(
        stage="LOST",
        loss_reason="Budget allocated elsewhere for Q4"
    )
    deal2 = await service.update_deal(deal2.id, deal_lost)
    assert deal2.stage == "LOST"
    assert deal2.outcome == "LOST"
    assert deal2.loss_reason == "Budget allocated elsewhere for Q4"


@pytest.mark.asyncio
async def test_crm_tasks_idempotency_and_completion(db_session):
    """Test task creation, duplicate prevention via idempotency_key, and task completion."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Task Corp {suffix}",
        canonical_domain=f"task-{suffix}.com"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = CRMService(db_session)
    idempotency_token = f"task-followup-{suffix}"

    task_in = TaskCreate(
        company_id=company.id,
        title="Follow up regarding proposal review",
        task_type="FOLLOW_UP",
        priority="HIGH",
        due_date=datetime.now(timezone.utc) + timedelta(days=2),
        idempotency_key=idempotency_token
    )

    # 1. First task creation
    task1 = await service.create_task(task_in, actor="account_exec")
    assert task1.id is not None
    assert task1.status == "PENDING"
    assert task1.priority == "HIGH"

    # 2. Retry with same idempotency token -> must return existing task, no duplicate!
    task2 = await service.create_task(task_in, actor="account_exec")
    assert task2.id == task1.id

    stmt_all = select(CRMTask).where(CRMTask.company_id == company.id)
    all_tasks = (await db_session.execute(stmt_all)).scalars().all()
    assert len(all_tasks) == 1

    # 3. Complete Task
    comp_req = TaskCompleteRequest(
        completed_by="account_exec",
        completion_notes="Spoke with VP of Marketing, scheduling demo"
    )
    completed_task = await service.complete_task(task1.id, comp_req)
    assert completed_task.status == "COMPLETED"
    assert completed_task.completed_at is not None
    assert completed_task.completed_by == "account_exec"
    assert completed_task.completion_notes == "Spoke with VP of Marketing, scheduling demo"


@pytest.mark.asyncio
async def test_unified_prospect_detail_linking(db_session):
    """Verify that unified prospect record links intelligence, website scan, contacts, media plan, deals, and activities."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Unified Corp {suffix}",
        canonical_domain=f"unified-{suffix}.com",
        industry="B2B Software",
        sales_stage="QUALIFIED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Add scan
    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://unified-{suffix}.com",
        title="Unified Corp Home",
        http_status=200,
        https_enabled=True,
        scan_status="COMPLETED"
    )
    db_session.add(scan)

    # Add opportunity profile
    opp = OpportunityProfile(
        company_id=company.id,
        recommended_service="Technical SEO",
        opportunity_score=88.5,
        confidence_level=0.95,
        data_freshness="FRESH",
        methodology_version="1.8.0"
    )
    db_session.add(opp)

    # Add contact
    contact = CompanyContact(
        company_id=company.id,
        email=f"press@unified-{suffix}.com",
        source_type="WEBSITE_PAGE",
        verification_status="VERIFIED",
        confidence=0.9
    )
    db_session.add(contact)
    await db_session.commit()

    service = CRMService(db_session)

    # Add deal & note
    deal = await service.create_deal(
        DealCreate(
            company_id=company.id,
            deal_name="SEO Migration Project",
            estimated_value=8000.0
        )
    )
    note = await service.add_note(
        company_id=company.id,
        req=NoteCreate(content="Client expressed strong interest in publisher placements.", author="analyst_2")
    )

    # Retrieve unified detail
    detail = await service.get_unified_prospect_detail(company.id)
    assert detail.company["company_name"] == f"Unified Corp {suffix}"
    assert detail.sales_stage == "QUALIFIED"
    assert detail.opportunity_profile is not None
    assert detail.opportunity_profile["opportunity_score"] == 88.5
    assert detail.website_scan is not None
    assert detail.website_scan["http_status"] == 200
    assert len(detail.contacts) == 1
    assert detail.contacts[0]["email"] == f"press@unified-{suffix}.com"
    assert len(detail.deals) == 1
    assert detail.deals[0].deal_name == "SEO Migration Project"
    assert len(detail.notes) == 1
    assert "publisher placements" in detail.notes[0].content
    assert len(detail.activities) >= 2


@pytest.mark.asyncio
async def test_crm_pipeline_board_and_metrics_calculation(db_session):
    """Test Kanban board aggregation and reporting metric calculations."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(
        company_name=f"Metric Corp {suffix}",
        canonical_domain=f"metric-{suffix}.com",
        sales_stage="MEETING_SCHEDULED"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    service = CRMService(db_session)
    await service.create_deal(
        DealCreate(
            company_id=company.id,
            deal_name="Link Outreach Package",
            estimated_value=6000.0
        )
    )

    # Board
    board = await service.get_pipeline_board()
    assert len(board) == 11 # 11 stages
    meeting_col = next((c for c in board if c.stage == "MEETING_SCHEDULED"), None)
    assert meeting_col is not None
    assert meeting_col.prospects_count >= 1

    # Metrics
    metrics = await service.get_crm_metrics()
    assert metrics.total_prospects >= 1
    assert metrics.prospects_by_stage["MEETING_SCHEDULED"] >= 1
    assert metrics.open_pipeline_value >= 6000.0
    assert metrics.pipeline_currency == "USD"
    assert len(metrics.notes) > 0


@pytest.mark.asyncio
async def test_crm_api_endpoints(db_session):
    """Test CRM REST API endpoints via AsyncClient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Pipeline board
        res_board = await client.get("/crm/pipeline/board")
        assert res_board.status_code == 200
        board_data = res_board.json()
        assert len(board_data) == 11

        # 2. Prospects list
        res_prospects = await client.get("/crm/prospects?page=1&page_size=10")
        assert res_prospects.status_code == 200
        prospects_data = res_prospects.json()
        assert "items" in prospects_data
        assert "total" in prospects_data

        # 3. Report metrics
        res_metrics = await client.get("/crm/reports/metrics")
        assert res_metrics.status_code == 200
        metrics_data = res_metrics.json()
        assert "prospects_by_stage" in metrics_data
        assert "open_pipeline_value" in metrics_data
