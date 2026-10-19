import logging
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timezone
import json
from zoneinfo import ZoneInfo

from app.models import (
    Workflow, WorkflowRun, Job, Company, Discovery,
    WebsiteScan, SEOMetric, OpportunityProfile,
    MatchingRun, MatchResult, MediaPlan, MediaPlanItem,
    PublisherRecord, PublisherObservation, ProviderUsage, Error
)
from app.schemas.workflow import VALID_WORKFLOW_STAGES
from app.core.redis import get_redis_settings
from arq import create_pool

logger = logging.getLogger(__name__)

STAGES = VALID_WORKFLOW_STAGES

def get_next_stage(enabled_stages: List[str], current_stage: Optional[str]) -> Optional[str]:
    if not enabled_stages:
        return None
        
    if not current_stage:
        return enabled_stages[0]
        
    try:
        current_index = STAGES.index(current_stage)
        for stage in STAGES[current_index + 1:]:
            if stage in enabled_stages:
                return stage
    except ValueError:
        pass
        
    return None

def matches_cron_field(pattern: str, val: int) -> bool:
    if pattern == "*":
        return True
    for part in pattern.split(","):
        if "/" in part:
            subparts = part.split("/")
            step = int(subparts[1])
            if subparts[0] == "*":
                if val % step == 0:
                    return True
            else:
                range_parts = subparts[0].split("-")
                start = int(range_parts[0])
                end = int(range_parts[1])
                if start <= val <= end and (val - start) % step == 0:
                    return True
        elif "-" in part:
            start, end = map(int, part.split("-"))
            if start <= val <= end:
                return True
        elif part.isdigit():
            if int(part) == val:
                return True
    return False

def matches_cron(cron_expr: str, dt: datetime) -> bool:
    """Evaluates standard 5-part cron: minute hour day month weekday."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False
    min_pat, hr_pat, dom_pat, mon_pat, dow_pat = parts
    
    # Python weekday(): 0=Mon, 6=Sun. Cron: 0=Sun, 1=Mon, ..., 6=Sat, 7=Sun
    cron_dow = (dt.weekday() + 1) % 7
    
    if not matches_cron_field(min_pat, dt.minute):
        return False
    if not matches_cron_field(hr_pat, dt.hour):
        return False
    if not matches_cron_field(dom_pat, dt.day):
        return False
    if not matches_cron_field(mon_pat, dt.month):
        return False
    # Support both 0 and 7 for Sunday
    if not (matches_cron_field(dow_pat, cron_dow) or (cron_dow == 0 and matches_cron_field(dow_pat, 7))):
        return False
    return True


class WorkflowOrchestrator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_workflow(
        self,
        workflow_id: uuid.UUID,
        trigger_type: str = "manual",
        company_ids: Optional[List[str]] = None,
        force: bool = False
    ) -> WorkflowRun:
        workflow = await self.session.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Idempotency / Duplicate Prevention:
        # Check if an active run is already executing for this workflow
        if not force:
            stmt = select(WorkflowRun).where(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.status.in_(["QUEUED", "RUNNING", "PENDING_APPROVAL"])
            )
            existing = (await self.session.execute(stmt)).scalars().first()
            if existing:
                raise ValueError(
                    f"Workflow {workflow_id} already has an active run ({existing.id}) with status '{existing.status}'. "
                    f"Cancel or complete it first, or use force=True."
                )

        next_stage = get_next_stage(workflow.enabled_stages, None)
        
        # Prepare target company IDs (either passed explicitly, configured on workflow, or to be discovered)
        target_company_ids = company_ids or workflow.selected_company_ids or []
        
        initial_params = {
            "company_ids": target_company_ids,
            "discovery_query": workflow.discovery_query,
            "target_company_count": workflow.target_company_count,
            "batch_size": workflow.batch_size or 10,
        }

        run = WorkflowRun(
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            status="QUEUED" if next_stage else "COMPLETED",
            current_stage=next_stage,
            total_companies=len(target_company_ids),
            successful_companies=0,
            failed_companies=0,
            retry_counts={},
            provider_failures={},
            stage_progress={},
            parameters=initial_params,
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(run)
        
        # Update workflow's last_run_at
        workflow.last_run_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(run)

        if next_stage:
            if next_stage == "human_review":
                run.status = "PENDING_APPROVAL"
                progress = run.stage_progress or {}
                progress["human_review"] = {
                    "status": "AWAITING_REVIEW",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "notes": "Awaiting human review."
                }
                run.stage_progress = progress
                await self.session.commit()
            else:
                await self._start_stage_jobs(run, workflow, next_stage)

        return run

    async def advance_workflow_run(self, run_id: uuid.UUID) -> Optional[WorkflowRun]:
        run = await self.session.get(WorkflowRun, run_id)
        if not run or run.status not in ["QUEUED", "RUNNING", "PENDING_APPROVAL"]:
            return run

        workflow = await self.session.get(Workflow, run.workflow_id)
        if not workflow:
            run.status = "FAILED"
            run.error_summary = f"Workflow {run.workflow_id} not found."
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return run

        # If run is at human_review stage, it stays in PENDING_APPROVAL until human action
        if run.current_stage == "human_review" and run.status == "PENDING_APPROVAL":
            logger.info(f"WorkflowRun {run.id} is waiting for human review.")
            return run

        # Check if current_stage is already completed in stage_progress
        progress = dict(run.stage_progress or {})
        current_stage_status = progress.get(run.current_stage, {}).get("status")
        if current_stage_status in ["COMPLETED", "SKIPPED", "SKIPPED_LIMIT", "PARTIAL"]:
            # Current stage is already completed; skip job checking and advance to next stage
            pass
        elif run.current_stage:
            stmt = select(Job).where(Job.workflow_run_id == run.id, Job.job_type == run.current_stage)
            result = await self.session.execute(stmt)
            jobs = result.scalars().all()

            if jobs:
                all_completed = True
                failed_jobs: List[Job] = []
                completed_jobs: List[Job] = []

                for job in jobs:
                    if job.status not in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "PARTIAL"]:
                        all_completed = False
                        break
                    if job.status in ["FAILED", "CANCELLED", "TIMEOUT"]:
                        failed_jobs.append(job)
                    else:
                        completed_jobs.append(job)

                if not all_completed:
                    # Still running; return and wait for completions
                    return run

                # All jobs for current_stage are finished!
                # Update stage progress metrics
                progress = run.stage_progress or {}
                stage_data = progress.get(run.current_stage, {})
                stage_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                stage_data["total_items"] = len(jobs)
                stage_data["successful_items"] = len(completed_jobs)
                stage_data["failed_items"] = len(failed_jobs)

                # Check if retry is needed for failed jobs
                max_retries = workflow.max_retries if workflow.max_retries is not None else 3
                retry_counts = dict(run.retry_counts or {})
                current_stage_retries = retry_counts.get(run.current_stage, 0)

                if failed_jobs and current_stage_retries < max_retries:
                    # Retry ONLY the failed jobs with backoff
                    retry_counts[run.current_stage] = current_stage_retries + 1
                    run.retry_counts = retry_counts
                    flag_modified(run, "retry_counts")

                    stage_data["status"] = "RETRYING"
                    progress[run.current_stage] = stage_data
                    run.stage_progress = dict(progress)
                    flag_modified(run, "stage_progress")
                    await self.session.commit()

                    logger.info(
                        f"Retrying {len(failed_jobs)} failed jobs for stage {run.current_stage} "
                        f"(attempt {current_stage_retries + 1}/{max_retries})"
                    )
                    await self._retry_failed_jobs(run, workflow, run.current_stage, failed_jobs)
                    return run

                # Retries exhausted or no failed jobs
                if failed_jobs:
                    if not completed_jobs:
                        # All failed: mark stage as FAILED and workflow as FAILED
                        stage_data["status"] = "FAILED"
                        stage_data["error_message"] = f"All {len(failed_jobs)} jobs failed in stage {run.current_stage}."
                        progress[run.current_stage] = stage_data
                        run.stage_progress = dict(progress)
                        flag_modified(run, "stage_progress")
                        run.status = "FAILED"
                        run.error_summary = f"Stage '{run.current_stage}' failed: {failed_jobs[0].error_message or 'Unknown error'}"
                        run.completed_at = datetime.now(timezone.utc)
                        await self.session.commit()
                        return run
                    else:
                        # Partial failure: some succeeded
                        stage_data["status"] = "PARTIAL"
                        stage_data["error_message"] = f"{len(failed_jobs)} of {len(jobs)} jobs failed."
                else:
                    stage_data["status"] = "COMPLETED"

                progress[run.current_stage] = stage_data
                run.stage_progress = dict(progress)
                flag_modified(run, "stage_progress")

                # If stage was discovery, harvest discovered company IDs into parameters
                if run.current_stage == "discovery":
                    discovered_ids = await self._harvest_discovered_company_ids(jobs)
                    params = dict(run.parameters or {})
                    existing_cids = params.get("company_ids", [])
                    merged_cids = list(dict.fromkeys(existing_cids + discovered_ids))
                    params["company_ids"] = merged_cids
                    run.parameters = params
                    flag_modified(run, "parameters")
                    run.total_companies = len(merged_cids)

                await self.session.commit()

            else:
                # No jobs yet for current_stage -> start them
                await self._start_stage_jobs(run, workflow, run.current_stage)
                return run

        # Transition to next stage
        next_stage = get_next_stage(workflow.enabled_stages, run.current_stage)

        if not next_stage:
            # Workflow completed successfully
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return run

        # Move to next stage
        run.current_stage = next_stage

        if next_stage == "human_review":
            # Stage 8: Human review & approval
            # Set to PENDING_APPROVAL and pause automatic progress
            run.status = "PENDING_APPROVAL"
            progress = dict(run.stage_progress or {})
            progress["human_review"] = {
                "status": "AWAITING_REVIEW",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "notes": "Media plan and opportunity analysis ready for human review."
            }
            run.stage_progress = progress
            flag_modified(run, "stage_progress")
            await self.session.commit()
            logger.info(f"WorkflowRun {run.id} reached human_review stage; paused awaiting review.")
            return run

        run.status = "RUNNING"
        await self.session.commit()

        # Start jobs for the new stage
        await self._start_stage_jobs(run, workflow, next_stage)
        return run

    async def _harvest_discovered_company_ids(self, discovery_jobs: List[Job]) -> List[str]:
        job_ids = [j.id for j in discovery_jobs]
        stmt = select(Discovery.company_id).where(Discovery.job_id.in_(job_ids)).distinct()
        res = await self.session.execute(stmt)
        return [str(cid) for cid in res.scalars().all()]

    async def _get_eligible_company_ids(self, run: WorkflowRun, workflow: Workflow, stage: str) -> List[uuid.UUID]:
        params = run.parameters or {}
        candidate_ids = params.get("company_ids", [])

        if candidate_ids:
            c_uuids = [uuid.UUID(str(c)) for c in candidate_ids]
            # Respect batch size
            batch_limit = workflow.batch_size or 10
            return c_uuids[:batch_limit]

        # If discovery was skipped and no explicit IDs, grab recent companies
        batch_limit = workflow.batch_size or 10
        stmt = select(Company.id).order_by(Company.created_at.desc()).limit(batch_limit)
        res = await self.session.execute(stmt)
        c_uuids = list(res.scalars().all())
        
        # Persist candidate IDs in parameters
        params["company_ids"] = [str(cid) for cid in c_uuids]
        run.parameters = params
        flag_modified(run, "parameters")
        run.total_companies = len(c_uuids)
        await self.session.commit()
        return c_uuids

    async def _start_stage_jobs(self, run: WorkflowRun, workflow: Workflow, stage: str):
        now_iso = datetime.now(timezone.utc).isoformat()
        progress = dict(run.stage_progress or {})
        progress[stage] = {
            "status": "RUNNING",
            "started_at": now_iso,
            "completed_at": None,
            "total_items": 0,
            "successful_items": 0,
            "failed_items": 0
        }
        run.stage_progress = progress
        flag_modified(run, "stage_progress")
        run.status = "RUNNING"
        await self.session.commit()

        redis = await create_pool(get_redis_settings())

        try:
            if stage == "discovery":
                params = run.parameters or {}
                selected_cids = params.get("company_ids") or workflow.selected_company_ids or []
                if selected_cids:
                    # Prospect selection stage: complete directly with selected existing prospects
                    progress[stage]["status"] = "COMPLETED"
                    progress[stage]["completed_at"] = datetime.now(timezone.utc).isoformat()
                    progress[stage]["total_items"] = len(selected_cids)
                    progress[stage]["successful_items"] = len(selected_cids)
                    progress[stage]["notes"] = f"Selected {len(selected_cids)} existing prospects."
                    run.stage_progress = progress
                    flag_modified(run, "stage_progress")

                    next_s = get_next_stage(workflow.enabled_stages, "discovery")
                    run.current_stage = next_s
                    if next_s == "human_review":
                        run.status = "PENDING_APPROVAL"
                        progress["human_review"] = {
                            "status": "AWAITING_REVIEW",
                            "started_at": datetime.now(timezone.utc).isoformat(),
                            "notes": "Awaiting human review."
                        }
                    await self.session.commit()
                    if next_s and next_s != "human_review":
                        await self._start_stage_jobs(run, workflow, next_s)
                    return

                job = Job(
                    workflow_run_id=run.id,
                    job_type=stage,
                    status="QUEUED",
                    parameters={
                        "query": workflow.discovery_query,
                        "target_count": workflow.target_company_count or workflow.batch_size or 10
                    },
                    started_at=datetime.now(timezone.utc)
                )
                self.session.add(job)
                await self.session.commit()
                await self.session.refresh(job)

                await redis.enqueue_job(
                    "company_discovery_job",
                    str(job.id),
                    {
                        "query": workflow.discovery_query or "tech",
                        "target_count": workflow.target_company_count or workflow.batch_size or 10
                    }
                )

            elif stage in ["website_analysis", "seo_enrichment", "ai_extraction", "opportunity_scoring", "publisher_matching", "media_plan_generation"]:
                company_ids = await self._get_eligible_company_ids(run, workflow, stage)

                if not company_ids:
                    # No companies available: mark stage as PARTIAL or COMPLETED and return
                    progress[stage]["status"] = "COMPLETED"
                    progress[stage]["completed_at"] = datetime.now(timezone.utc).isoformat()
                    progress[stage]["total_items"] = 0
                    progress[stage]["notes"] = "No eligible companies found for stage."
                    run.stage_progress = progress
                    await self.session.commit()
                    return

                # Check usage limits for provider-heavy stages
                provider_limits = workflow.provider_request_limits or {}
                if stage in ["seo_enrichment", "ai_extraction"] and provider_limits:
                    # Check overall provider request limit
                    max_allowed = provider_limits.get("max_requests", 500)
                    stmt_usage = select(func.count(Job.id)).where(
                        Job.workflow_run_id == run.id,
                        Job.job_type == stage
                    )
                    used = (await self.session.execute(stmt_usage)).scalar() or 0
                    if used >= max_allowed:
                        logger.warning(f"Workflow {workflow.id} reached usage limit ({used}/{max_allowed}) for {stage}")
                        pf = run.provider_failures or {}
                        pf[stage] = f"Usage limit reached ({max_allowed} requests)."
                        run.provider_failures = pf
                        progress[stage]["status"] = "SKIPPED_LIMIT"
                        progress[stage]["completed_at"] = datetime.now(timezone.utc).isoformat()
                        run.stage_progress = progress
                        await self.session.commit()
                        return

                job_mapping = {
                    "website_analysis": "website_analysis_job",
                    "seo_enrichment": "seo_enrichment_job",
                    "ai_extraction": "ai_extraction_job",
                    "opportunity_scoring": "opportunity_evaluation_job",
                    "publisher_matching": "publisher_matching_job",
                    "media_plan_generation": "media_plan_generation_job"
                }
                job_function_name = job_mapping[stage]

                for cid in company_ids:
                    # Idempotency check: don't create duplicate job if completed for this run
                    stmt_dup = select(Job).where(
                        Job.workflow_run_id == run.id,
                        Job.job_type == stage,
                        Job.parameters["company_id"].astext == str(cid),
                        Job.status == "COMPLETED"
                    )
                    existing_job = (await self.session.execute(stmt_dup)).scalars().first()
                    if existing_job:
                        continue

                    job = Job(
                        workflow_run_id=run.id,
                        job_type=stage,
                        status="QUEUED",
                        parameters={"company_id": str(cid)},
                        started_at=datetime.now(timezone.utc)
                    )
                    self.session.add(job)
                    await self.session.commit()
                    await self.session.refresh(job)

                    await redis.enqueue_job(job_function_name, str(job.id), str(cid))

        finally:
            await redis.aclose()

    async def _retry_failed_jobs(self, run: WorkflowRun, workflow: Workflow, stage: str, failed_jobs: List[Job]):
        redis = await create_pool(get_redis_settings())
        try:
            job_mapping = {
                "discovery": "company_discovery_job",
                "website_analysis": "website_analysis_job",
                "seo_enrichment": "seo_enrichment_job",
                "ai_extraction": "ai_extraction_job",
                "opportunity_scoring": "opportunity_evaluation_job",
                "publisher_matching": "publisher_matching_job",
                "media_plan_generation": "media_plan_generation_job"
            }
            job_function_name = job_mapping.get(stage, f"{stage}_job")

            for job in failed_jobs:
                job.status = "QUEUED"
                job.error_message = None
                job.started_at = datetime.now(timezone.utc)
                job.completed_at = None
                await self.session.commit()

                if stage == "discovery":
                    params = job.parameters or {}
                    await redis.enqueue_job("company_discovery_job", str(job.id), params)
                else:
                    cid = (job.parameters or {}).get("company_id")
                    if cid:
                        await redis.enqueue_job(job_function_name, str(job.id), str(cid))
        finally:
            await redis.aclose()

    async def cancel_workflow_run(self, run_id: uuid.UUID) -> WorkflowRun:
        run = await self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")

        run.status = "CANCELLED"
        run.completed_at = datetime.now(timezone.utc)
        progress = dict(run.stage_progress or {})
        if run.current_stage and run.current_stage in progress:
            progress[run.current_stage]["status"] = "CANCELLED"
            progress[run.current_stage]["completed_at"] = datetime.now(timezone.utc).isoformat()
        run.stage_progress = progress
        flag_modified(run, "stage_progress")

        # Cancel all pending jobs in database
        stmt = select(Job).where(
            Job.workflow_run_id == run.id,
            Job.status.in_(["QUEUED", "RUNNING"])
        )
        jobs = (await self.session.execute(stmt)).scalars().all()
        for job in jobs:
            job.status = "CANCELLED"

        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def retry_workflow_run(self, run_id: uuid.UUID) -> WorkflowRun:
        run = await self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")

        workflow = await self.session.get(Workflow, run.workflow_id)
        if not workflow:
            raise ValueError("Associated workflow not found")

        # Resume from current stage or last failed stage
        run.status = "RUNNING"
        run.error_summary = None
        run.completed_at = None

        # Reset retry count for current stage
        retry_counts = dict(run.retry_counts or {})
        if run.current_stage:
            retry_counts[run.current_stage] = 0
        run.retry_counts = retry_counts
        flag_modified(run, "retry_counts")

        await self.session.commit()
        await self.advance_workflow_run(run.id)
        await self.session.refresh(run)
        return run

    async def approve_workflow_run(
        self,
        run_id: uuid.UUID,
        approved_by: str = "human_reviewer",
        notes: Optional[str] = None
    ) -> WorkflowRun:
        run = await self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")

        if run.current_stage != "human_review" or run.status != "PENDING_APPROVAL":
            raise ValueError(f"WorkflowRun is not awaiting human review (current stage: {run.current_stage}, status: {run.status})")

        now = datetime.now(timezone.utc)
        run.status = "COMPLETED"
        run.approved_at = now
        run.approved_by = approved_by
        run.completed_at = now

        progress = dict(run.stage_progress or {})
        progress["human_review"] = {
            "status": "COMPLETED",
            "started_at": progress.get("human_review", {}).get("started_at", now.isoformat()),
            "completed_at": now.isoformat(),
            "approved_by": approved_by,
            "notes": notes or "Approved by human reviewer."
        }
        run.stage_progress = progress
        flag_modified(run, "stage_progress")

        # Update associated MediaPlans to FINAL
        params = run.parameters or {}
        company_ids = params.get("company_ids", [])
        if company_ids:
            c_uuids = [uuid.UUID(str(c)) for c in company_ids]
            stmt_plans = select(MediaPlan).where(MediaPlan.company_id.in_(c_uuids))
            plans = (await self.session.execute(stmt_plans)).scalars().all()
            for plan in plans:
                plan.status = "FINAL"

        await self.session.commit()
        await self.session.refresh(run)
        logger.info(f"WorkflowRun {run.id} approved by {approved_by}; run completed.")
        return run

    async def reject_workflow_run(
        self,
        run_id: uuid.UUID,
        rejected_by: str = "human_reviewer",
        reason: str = "Rejected during human review"
    ) -> WorkflowRun:
        run = await self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")

        now = datetime.now(timezone.utc)
        run.status = "REJECTED"
        run.completed_at = now
        run.error_summary = f"Rejected by {rejected_by}: {reason}"

        progress = dict(run.stage_progress or {})
        progress["human_review"] = {
            "status": "REJECTED",
            "started_at": progress.get("human_review", {}).get("started_at", now.isoformat()),
            "completed_at": now.isoformat(),
            "rejected_by": rejected_by,
            "reason": reason
        }
        run.stage_progress = progress
        flag_modified(run, "stage_progress")

        await self.session.commit()
        await self.session.refresh(run)
        logger.info(f"WorkflowRun {run.id} rejected by {rejected_by}: {reason}")
        return run

    async def evaluate_scheduled_workflows(self) -> List[WorkflowRun]:
        """Evaluates active scheduled workflows against their cron and timezone configurations."""
        stmt = select(Workflow).where(
            Workflow.is_enabled == True,
            Workflow.schedule_cron.is_not(None)
        )
        workflows = (await self.session.execute(stmt)).scalars().all()
        triggered_runs: List[WorkflowRun] = []

        now_utc = datetime.now(timezone.utc)

        for wf in workflows:
            if not wf.schedule_cron:
                continue

            # Resolve timezone safely
            tz_str = wf.schedule_timezone or "UTC"
            try:
                tz = ZoneInfo(tz_str)
            except Exception:
                tz = ZoneInfo("UTC")

            local_dt = now_utc.astimezone(tz)

            if matches_cron(wf.schedule_cron, local_dt):
                # Check last_run_at to avoid running more than once in the same minute slot
                if wf.last_run_at:
                    local_last_run = wf.last_run_at.astimezone(tz)
                    if (
                        local_last_run.year == local_dt.year
                        and local_last_run.month == local_dt.month
                        and local_last_run.day == local_dt.day
                        and local_last_run.hour == local_dt.hour
                        and local_last_run.minute == local_dt.minute
                    ):
                        # Already executed in this minute slot
                        continue

                try:
                    run = await self.start_workflow(
                        wf.id,
                        trigger_type="scheduled",
                        company_ids=wf.selected_company_ids,
                        force=False
                    )
                    triggered_runs.append(run)
                    logger.info(f"Scheduled workflow {wf.id} ('{wf.name}') triggered successfully at {local_dt} ({tz_str}).")
                except ValueError as ve:
                    logger.info(f"Scheduled workflow {wf.id} skipped: {ve}")
                except Exception as e:
                    logger.error(f"Error triggering scheduled workflow {wf.id}: {e}")

        return triggered_runs
