import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from app.db.session import async_session_maker
from app.models import (
    Company,
    PublisherRecord,
    PublisherObservation,
    Workflow,
    WorkflowRun,
    Job,
    MediaPlan,
    MediaPlanItem,
    MatchingRun,
    MatchResult,
    OpportunityProfile,
)
from app.services.orchestrator.runner import WorkflowOrchestrator
from app.workers.worker import (
    website_analysis_job,
    seo_enrichment_job,
    ai_extraction_job,
    opportunity_evaluation_job,
    publisher_matching_job,
    media_plan_generation_job,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_validation")

async def run_controlled_validation():
    logger.info("=== Starting Phase 2.3 Controlled Real-Data E2E Validation ===")

    async with async_session_maker() as session:
        # 1. Audit real database records
        total_companies = await session.scalar(select(func.count(Company.id)))
        total_publishers = await session.scalar(select(func.count(PublisherRecord.id)))
        total_obs = await session.scalar(select(func.count(PublisherObservation.id)))
        logger.info(f"Existing DB inventory: {total_companies} Companies, {total_publishers} Publishers, {total_obs} Observations.")
        assert total_companies > 0, "No companies found in database!"
        assert total_publishers > 0, "No publishers found in database!"

        # Pick a real company with domain and website
        stmt_comp = select(Company).where(Company.company_name == "TechCrunch").limit(1)
        real_company = (await session.execute(stmt_comp)).scalars().first()
        assert real_company is not None, "Could not find TechCrunch company."
        logger.info(f"Selected real company: ID={real_company.id}, Name='{real_company.company_name}', Domain='{real_company.canonical_domain}'")

        # 2. Create a persistent Workflow for this real company
        workflow = Workflow(
            name=f"E2E Real Validation - {real_company.canonical_domain}",
            is_enabled=True,
            enabled_stages=[
                "discovery",
                "website_analysis",
                "opportunity_scoring",
                "publisher_matching",
                "media_plan_generation",
                "human_review"
            ],
            selected_company_ids=[str(real_company.id)],
            batch_size=1,
            max_retries=2,
            provider_request_limits={"max_requests": 50}
        )
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        logger.info(f"Created persistent Workflow: ID={workflow.id}")

        # 3. Create a WorkflowRun
        orchestrator = WorkflowOrchestrator(session)
        run = await orchestrator.start_workflow(
            workflow_id=workflow.id,
            trigger_type="MANUAL",
            company_ids=[str(real_company.id)]
        )
        await session.refresh(run)
        logger.info(f"Initialized WorkflowRun: ID={run.id}, Status={run.status}, CurrentStage={run.current_stage}")
        assert run.stage_progress["discovery"]["status"] == "COMPLETED"
        logger.info(f"Stage 1 (discovery/selection) completed: {run.stage_progress.get('discovery')}")

        run_id = run.id
        company_id = real_company.id

        # Stages 2 through 7: website_analysis, seo_enrichment, ai_extraction, opportunity_scoring, publisher_matching, media_plan_generation
        stage_job_handlers = {
            "website_analysis": website_analysis_job,
            "seo_enrichment": seo_enrichment_job,
            "ai_extraction": ai_extraction_job,
            "opportunity_scoring": opportunity_evaluation_job,
            "publisher_matching": publisher_matching_job,
            "media_plan_generation": media_plan_generation_job,
        }

        while True:
            run = await session.get(WorkflowRun, run_id)
            await session.refresh(run)
            if run.status != "RUNNING" or run.current_stage not in stage_job_handlers:
                break

            current_stage = run.current_stage
            logger.info(f"--- Processing Stage: {current_stage} ---")

            stmt_jobs = select(Job).where(
                Job.workflow_run_id == run_id,
                Job.job_type == current_stage,
                Job.status == "QUEUED"
            )
            queued_jobs = (await session.execute(stmt_jobs)).scalars().all()
            logger.info(f"Stage '{current_stage}' has {len(queued_jobs)} queued jobs.")

            # Execute the queued jobs
            job_handler = stage_job_handlers[current_stage]
            for job in queued_jobs:
                cid = job.parameters["company_id"]
                logger.info(f"Executing handler for Job {job.id} on Company {cid}...")
                await job_handler(None, str(job.id), cid)

            # Advance orchestrator in a clean session
            async with async_session_maker() as orch_session:
                orch = WorkflowOrchestrator(orch_session)
                await orch.advance_workflow_run(run_id)

            run = await session.get(WorkflowRun, run_id)
            await session.refresh(run)
            logger.info(f"Stage '{current_stage}' result: Status={run.stage_progress.get(current_stage, {}).get('status')}, Next Stage={run.current_stage}")

        # 5. Verify Stage 8: Human Review boundary
        run = await session.get(WorkflowRun, run_id)
        await session.refresh(run)
        logger.info(f"Workflow Run State: Status={run.status}, CurrentStage={run.current_stage}")
        assert run.status == "PENDING_APPROVAL", f"Expected PENDING_APPROVAL, got {run.status}"
        assert run.current_stage == "human_review", f"Expected human_review, got {run.current_stage}"
        assert run.stage_progress["human_review"]["status"] == "AWAITING_REVIEW"
        logger.info("Human Review boundary safely halted automated progression.")

        # 6. Verify Persisted Media Plan & Match Results
        stmt_plan = select(MediaPlan).where(
            MediaPlan.company_id == company_id,
            MediaPlan.status == "DRAFT"
        ).order_by(MediaPlan.created_at.desc()).limit(1)
        draft_plan = (await session.execute(stmt_plan)).scalar_one_or_none()
        assert draft_plan is not None, "MediaPlan was not generated in PostgreSQL!"
        logger.info(f"Verified Persisted MediaPlan: ID={draft_plan.id}, Name='{draft_plan.name}', Status={draft_plan.status}")

        stmt_items = select(MediaPlanItem).where(MediaPlanItem.media_plan_id == draft_plan.id)
        plan_items = (await session.execute(stmt_items)).scalars().all()
        logger.info(f"MediaPlan contains {len(plan_items)} recommended publisher items.")
        assert len(plan_items) > 0, "MediaPlan has no items!"
        for idx, item in enumerate(plan_items[:3]):
            pub = await session.get(PublisherRecord, item.publisher_id)
            logger.info(f"  Item #{idx+1}: Publisher='{pub.publisher_name if pub else item.publisher_id}', Score={item.relevance_score if hasattr(item, 'relevance_score') else 'N/A'}, Price={item.proposed_price}")

        # 7. Perform Human Approval
        logger.info("Performing authorized Human Review approval...")
        async with async_session_maker() as approval_session:
            appr_orch = WorkflowOrchestrator(approval_session)
            approved_run = await appr_orch.approve_workflow_run(run_id, approved_by="senior_seo_strategist@prospectos.local")

        run = await session.get(WorkflowRun, run_id)
        await session.refresh(run)
        await session.refresh(draft_plan)

        assert approved_run.status == "COMPLETED", f"Expected COMPLETED, got {approved_run.status}"
        assert approved_run.stage_progress["human_review"]["status"] == "COMPLETED"
        assert approved_run.approved_by == "senior_seo_strategist@prospectos.local"
        assert draft_plan.status == "FINAL", f"Expected MediaPlan status FINAL, got {draft_plan.status}"
        logger.info(f"Approval successful: WorkflowRun Status={approved_run.status}, MediaPlan Status={draft_plan.status}, ApprovedBy={approved_run.approved_by}")

        logger.info("=== Phase 2.3 Controlled Real-Data E2E Validation PASSED with 100% Data Integrity ===")

if __name__ == "__main__":
    asyncio.run(run_controlled_validation())
