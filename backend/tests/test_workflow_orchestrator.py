import pytest
import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.session import async_session_maker
from app.models import (
    Company, Workflow, WorkflowRun, Job, WebsiteScan,
    SEOMetric, OpportunityProfile, CampaignProfile,
    PublisherRecord, PublisherObservation, MatchResult,
    MatchingRun, MediaPlan, MediaPlanItem, AIObservation, AIExtractionRun
)
from app.services.orchestrator.runner import WorkflowOrchestrator, matches_cron, STAGES
from app.schemas.workflow import VALID_WORKFLOW_STAGES

@pytest.mark.asyncio
async def test_workflow_stages_and_validation():
    """Verify all 8 stages are valid and invalid stages are rejected."""
    assert len(VALID_WORKFLOW_STAGES) == 8
    expected = [
        'discovery', 'website_analysis', 'seo_enrichment', 'ai_extraction',
        'opportunity_scoring', 'publisher_matching', 'media_plan_generation', 'human_review'
    ]
    assert VALID_WORKFLOW_STAGES == expected

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid stage should be rejected with 422
        bad_resp = await client.post("/workflows/", json={
            "name": "Invalid Stage Workflow",
            "enabled_stages": ["discovery", "cold_email_spam"] # forbidden stage
        })
        assert bad_resp.status_code == 422

        # Valid workflow creation with all 8 stages
        valid_resp = await client.post("/workflows/", json={
            "name": "Full 8-Stage Pipeline",
            "enabled_stages": VALID_WORKFLOW_STAGES,
            "target_company_count": 5,
            "schedule_cron": "0 9 * * 1",
            "schedule_timezone": "UTC",
            "batch_size": 5,
            "max_retries": 2,
            "retry_backoff_seconds": 60,
            "is_enabled": True
        })
        assert valid_resp.status_code == 200, valid_resp.text
        wf_data = valid_resp.json()
        assert wf_data["name"] == "Full 8-Stage Pipeline"
        assert len(wf_data["enabled_stages"]) == 8
        wf_id = wf_data["id"]

        # Update workflow
        put_resp = await client.put(f"/workflows/{wf_id}", json={
            "is_enabled": False,
            "name": "Updated Pipeline"
        })
        assert put_resp.status_code == 200
        assert put_resp.json()["is_enabled"] is False
        assert put_resp.json()["name"] == "Updated Pipeline"

        # Get workflow
        get_resp = await client.get(f"/workflows/{wf_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == wf_id

@pytest.mark.asyncio
async def test_duplicate_run_prevention_and_idempotency():
    """Verify duplicate workflow runs are prevented unless force=True."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        wf = Workflow(
            name=f"Duplicate Test {suffix}",
            enabled_stages=["website_analysis", "opportunity_scoring"],
            batch_size=2
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)
        wf_id = wf.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start first run
        resp1 = await client.post(f"/workflows/{wf_id}/runs", json={"trigger_type": "manual"})
        assert resp1.status_code == 200
        run1_id = resp1.json()["id"]

        # 2. Start second run without force -> should be rejected with 400
        resp2 = await client.post(f"/workflows/{wf_id}/runs", json={"trigger_type": "manual", "force": False})
        assert resp2.status_code == 400
        assert "already has an active run" in resp2.json()["detail"]

        # 3. Start with force=True -> should succeed
        resp3 = await client.post(f"/workflows/{wf_id}/runs", json={"trigger_type": "manual", "force": True})
        assert resp3.status_code == 200
        assert resp3.json()["id"] != run1_id

@pytest.mark.asyncio
async def test_workflow_cancellation():
    """Verify workflow cancellation halts pending jobs and marks status CANCELLED."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        wf = Workflow(
            name=f"Cancel Test {suffix}",
            enabled_stages=["website_analysis", "opportunity_scoring"],
            batch_size=2
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)
        wf_id = wf.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(f"/workflows/{wf_id}/runs", json={"trigger_type": "manual"})
        assert resp.status_code == 200
        run_id = resp.json()["id"]

        cancel_resp = await client.post(f"/workflows/runs/{run_id}/cancel")
        assert cancel_resp.status_code == 200
        data = cancel_resp.json()
        assert data["status"] == "CANCELLED"
        assert data["completed_at"] is not None

@pytest.mark.asyncio
async def test_end_to_end_workflow_execution_and_human_approval():
    """
    Complete end-to-end test executing all stages:
    prospect selection -> website_analysis -> seo_enrichment -> ai_extraction ->
    opportunity_scoring -> publisher_matching -> media_plan_generation -> human_review approval.
    """
    suffix = uuid.uuid4().hex[:8]
    async with async_session_maker() as session:
        # Create a real prospect company
        prospect = Company(
            canonical_domain=f"prospect-e2e-{suffix}.com",
            company_name=f"E2E Enterprise {suffix}",
            industry="Technology",
            country="United States",
            website_url=f"https://prospect-e2e-{suffix}.com"
        )
        session.add(prospect)

        # Create a publisher in the inventory
        pub_co = Company(
            canonical_domain=f"tech-pub-{suffix}.com",
            company_name=f"Tech Publisher {suffix}",
            industry="Technology"
        )
        session.add(pub_co)
        await session.commit()
        await session.refresh(prospect)
        await session.refresh(pub_co)

        pub = PublisherRecord(
            company_id=pub_co.id,
            publisher_name=f"Tech News Daily {suffix}",
            audience_focus="Technology Software"
        )
        session.add(pub)
        await session.commit()
        await session.refresh(pub)

        obs = PublisherObservation(
            publisher_id=pub.id,
            price=250.0,
            currency="USD",
            metric_da=55.0,
            metric_dr=60.0
        )
        session.add(obs)

        # Create workflow covering website analysis through human review
        wf = Workflow(
            name=f"E2E Automation {suffix}",
            enabled_stages=[
                "website_analysis",
                "seo_enrichment",
                "opportunity_scoring",
                "publisher_matching",
                "media_plan_generation",
                "human_review"
            ],
            selected_company_ids=[str(prospect.id)],
            batch_size=1,
            max_retries=1
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)
        wf_id = wf.id
        prospect_id = prospect.id

    # 1. Start workflow run with prospect selection
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_resp = await client.post(
            f"/workflows/{wf_id}/runs",
            json={"trigger_type": "manual", "company_ids": [str(prospect_id)]}
        )
        assert start_resp.status_code == 200, start_resp.text
        run_id = uuid.UUID(start_resp.json()["id"])

    # 2. Advance through stages sequentially consuming persisted outputs
    async with async_session_maker() as session:
        orchestrator = WorkflowOrchestrator(session)

        # Stage 1: website_analysis
        # Simulate worker completing website_analysis
        scan = WebsiteScan(
            company_id=prospect_id,
            url=f"https://prospect-e2e-{suffix}.com",
            http_status=200,
            https_enabled=True,
            title="Leading Enterprise Cloud Platforms",
            meta_description="Enterprise cloud intelligence and automation.",
            h1=["Welcome to Enterprise Cloud"],
            scan_status="COMPLETED"
        )
        session.add(scan)
        # Mark website analysis job COMPLETED
        stmt_job = select(Job).where(Job.workflow_run_id == run_id, Job.job_type == "website_analysis")
        ws_job = (await session.execute(stmt_job)).scalars().first()
        if ws_job:
            ws_job.status = "COMPLETED"
        await session.commit()

        # Advance orchestrator -> moves to seo_enrichment
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.current_stage == "seo_enrichment"
        assert run.stage_progress["website_analysis"]["status"] == "COMPLETED"

        # Stage 2: seo_enrichment
        # Simulate worker creating SEO metric
        metric = SEOMetric(
            company_id=prospect_id,
            metric_name="domain_rating",
            metric_value=25.0, # Low authority
            provider="Ahrefs",
            verification_status="VERIFIED"
        )
        session.add(metric)
        stmt_job = select(Job).where(Job.workflow_run_id == run_id, Job.job_type == "seo_enrichment")
        seo_job = (await session.execute(stmt_job)).scalars().first()
        if seo_job:
            seo_job.status = "COMPLETED"
        await session.commit()

        # Advance orchestrator -> moves to opportunity_scoring
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.current_stage == "opportunity_scoring"
        assert run.stage_progress["seo_enrichment"]["status"] == "COMPLETED"

        # Stage 3: opportunity_scoring
        # Worker evaluates opportunity
        from app.services.intelligence.opportunity import OpportunityEngine
        engine = OpportunityEngine(session)
        profile_create = await engine.evaluate_company(prospect_id)
        await engine.save_profile(profile_create)
        stmt_job = select(Job).where(Job.workflow_run_id == run_id, Job.job_type == "opportunity_scoring")
        opp_job = (await session.execute(stmt_job)).scalars().first()
        if opp_job:
            opp_job.status = "COMPLETED"
        await session.commit()

        # Advance orchestrator -> moves to publisher_matching
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.current_stage == "publisher_matching"
        assert run.stage_progress["opportunity_scoring"]["status"] == "COMPLETED"

        # Stage 4: publisher_matching
        # Worker executes matching engine against real inventory
        from app.services.matching.engine import MatchingEngine
        match_engine = MatchingEngine(session)
        await match_engine.run_matching(prospect_id)
        stmt_job = select(Job).where(Job.workflow_run_id == run_id, Job.job_type == "publisher_matching")
        match_job = (await session.execute(stmt_job)).scalars().first()
        if match_job:
            match_job.status = "COMPLETED"
        await session.commit()

        # Advance orchestrator -> moves to media_plan_generation
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.current_stage == "media_plan_generation"
        assert run.stage_progress["publisher_matching"]["status"] == "COMPLETED"

        # Stage 5: media_plan_generation
        # Execute media plan worker logic
        stmt_match_run = select(MatchingRun).where(
            MatchingRun.company_id == prospect_id,
            MatchingRun.status == "COMPLETED"
        ).order_by(MatchingRun.completed_at.desc()).limit(1)
        latest_match_run = (await session.execute(stmt_match_run)).scalar_one_or_none()
        assert latest_match_run is not None

        stmt_top = select(MatchResult).where(
            MatchResult.matching_run_id == latest_match_run.id
        ).order_by(MatchResult.rank.asc()).limit(5)
        top_matches = (await session.execute(stmt_top)).scalars().all()
        assert len(top_matches) > 0

        plan = MediaPlan(
            company_id=prospect_id,
            name=f"Automated Plan - E2E",
            status="DRAFT"
        )
        session.add(plan)
        await session.flush()

        for m in top_matches:
            item = MediaPlanItem(
                media_plan_id=plan.id,
                publisher_id=m.publisher_id,
                match_result_id=m.id,
                proposed_price=250.0,
                proposed_currency="USD"
            )
            session.add(item)

        stmt_job = select(Job).where(Job.workflow_run_id == run_id, Job.job_type == "media_plan_generation")
        mp_job = (await session.execute(stmt_job)).scalars().first()
        if mp_job:
            mp_job.status = "COMPLETED"
        await session.commit()

        # Advance orchestrator -> moves to human_review!
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        # MUST halt at human_review with status PENDING_APPROVAL
        assert run.current_stage == "human_review"
        assert run.status == "PENDING_APPROVAL"
        assert run.stage_progress["human_review"]["status"] == "AWAITING_REVIEW"

    # 3. Human Review & Approval via API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check run status via API
        run_resp = await client.get(f"/workflows/runs/{run_id}")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["status"] == "PENDING_APPROVAL"
        assert run_data["current_stage"] == "human_review"

        # Approve the run
        approve_resp = await client.post(
            f"/workflows/runs/{run_id}/approve",
            json={"approved_by": "qa_lead", "notes": "Plan thoroughly verified and approved."}
        )
        assert approve_resp.status_code == 200, approve_resp.text
        approved_data = approve_resp.json()
        assert approved_data["status"] == "COMPLETED"
        assert approved_data["approved_by"] == "qa_lead"
        assert approved_data["approved_at"] is not None

    # 4. Verify persisted state in PostgreSQL
    async with async_session_maker() as session:
        # Verify MediaPlan is now FINAL
        stmt_plan = select(MediaPlan).where(MediaPlan.company_id == prospect_id)
        persisted_plan = (await session.execute(stmt_plan)).scalars().first()
        assert persisted_plan is not None
        assert persisted_plan.status == "FINAL"

        # Verify items exist
        stmt_items = select(MediaPlanItem).where(MediaPlanItem.media_plan_id == persisted_plan.id)
        items = (await session.execute(stmt_items)).scalars().all()
        assert len(items) > 0
        assert items[0].proposed_price == 250.0

@pytest.mark.asyncio
async def test_human_review_rejection():
    """Verify human review rejection halts workflow and marks REJECTED."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        wf = Workflow(
            name=f"Reject Test {suffix}",
            enabled_stages=["human_review"]
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)
        wf_id = wf.id

        orchestrator = WorkflowOrchestrator(session)
        run = await orchestrator.start_workflow(wf_id, trigger_type="manual")
        run_id = run.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reject_resp = await client.post(
            f"/workflows/runs/{run_id}/reject",
            json={"rejected_by": "editor", "reason": "Target budget exceeded."}
        )
        assert reject_resp.status_code == 200
        data = reject_resp.json()
        assert data["status"] == "REJECTED"
        assert "Target budget exceeded." in data["error_summary"]

@pytest.mark.asyncio
async def test_cron_matcher_and_scheduled_workflows():
    """Test standard cron matching logic and evaluate_scheduled_workflows."""
    # Test cron expressions
    dt_monday_9am = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc) # Monday
    assert matches_cron("0 9 * * 1", dt_monday_9am) is True
    assert matches_cron("0 10 * * 1", dt_monday_9am) is False
    assert matches_cron("*/15 * * * *", dt_monday_9am) is True
    assert matches_cron("0 9 * * 2", dt_monday_9am) is False # Tuesday only

    # Test scheduler execution
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        # Create a scheduled workflow matching every minute
        wf = Workflow(
            name=f"Scheduled WF {suffix}",
            enabled_stages=["website_analysis"],
            schedule_cron="* * * * *",
            schedule_timezone="UTC",
            is_enabled=True,
            batch_size=1
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)

        orchestrator = WorkflowOrchestrator(session)
        triggered = await orchestrator.evaluate_scheduled_workflows()
        
        # Verify it was triggered
        triggered_wf_ids = [r.workflow_id for r in triggered]
        assert wf.id in triggered_wf_ids

        # Running evaluate again in the same minute should NOT trigger duplicates
        second_triggered = await orchestrator.evaluate_scheduled_workflows()
        assert wf.id not in [r.workflow_id for r in second_triggered]

        # Disabling workflow prevents future triggers
        wf.is_enabled = False
        wf.last_run_at = None
        await session.commit()

        third_triggered = await orchestrator.evaluate_scheduled_workflows()
        assert wf.id not in [r.workflow_id for r in third_triggered]

@pytest.mark.asyncio
async def test_retry_backoff_and_exhaustion():
    """Verify that stage failures trigger retry up to max_retries and then transition to FAILED."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        co = Company(canonical_domain=f"retry-{suffix}.com", company_name=f"Retry {suffix}")
        session.add(co)
        await session.commit()
        await session.refresh(co)

        wf = Workflow(
            name=f"Retry Test {suffix}",
            enabled_stages=["website_analysis"],
            selected_company_ids=[str(co.id)],
            batch_size=1,
            max_retries=1, # 1 retry allowed
            retry_backoff_seconds=10
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)

        orchestrator = WorkflowOrchestrator(session)
        run = await orchestrator.start_workflow(wf.id)
        run_id = run.id

        # Job was created; simulate job failure
        stmt_job = select(Job).where(Job.workflow_run_id == run_id)
        job = (await session.execute(stmt_job)).scalars().first()
        assert job is not None
        job.status = "FAILED"
        job.error_message = "DNS resolution failed"
        await session.commit()

        # Advance orchestrator -> should trigger retry (attempt 1 of 1)
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.retry_counts["website_analysis"] == 1
        assert run.stage_progress["website_analysis"]["status"] == "RETRYING"

        # The job was re-queued; simulate second failure
        job = (await session.get(Job, job.id))
        job.status = "FAILED"
        job.error_message = "DNS resolution failed again"
        await session.commit()

        # Advance orchestrator -> retries exhausted, should mark FAILED
        await orchestrator.advance_workflow_run(run_id)
        run = await session.get(WorkflowRun, run_id)
        assert run.status == "FAILED"
        assert run.stage_progress["website_analysis"]["status"] == "FAILED"
        assert "DNS resolution failed again" in run.error_summary

@pytest.mark.asyncio
async def test_provider_usage_limits():
    """Verify provider usage limits prevent runaway API requests."""
    suffix = uuid.uuid4().hex[:6]
    async with async_session_maker() as session:
        co = Company(canonical_domain=f"limit-{suffix}.com", company_name=f"Limit {suffix}")
        session.add(co)
        await session.commit()
        await session.refresh(co)

        # Create workflow with max_requests limit of 0 for seo_enrichment
        wf = Workflow(
            name=f"Limit Test {suffix}",
            enabled_stages=["seo_enrichment"],
            selected_company_ids=[str(co.id)],
            batch_size=1,
            provider_request_limits={"max_requests": 0} # 0 allowed
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)

        orchestrator = WorkflowOrchestrator(session)
        run = await orchestrator.start_workflow(wf.id)

        # Verify provider stage was safely skipped due to limit
        run = await session.get(WorkflowRun, run.id)
        assert "seo_enrichment" in (run.provider_failures or {})
        assert run.stage_progress["seo_enrichment"]["status"] == "SKIPPED_LIMIT"
