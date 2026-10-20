import asyncio
import logging
from datetime import datetime, timezone
from arq import Worker
from app.core.config import settings
from arq.connections import RedisSettings
from app.db.session import async_session_maker
from app.models import Job
from app.services.discovery.pipeline import run_discovery_pipeline
from app.services.discovery.github import GitHubOrgProvider
from app.schemas.discovery import DiscoveryRequest

logger = logging.getLogger(__name__)

from app.core.redis import get_redis_settings
from arq import create_pool

async def _trigger_orchestrator_if_needed(job_id: str, session):
    from app.models import Job
    job = await session.get(Job, job_id)
    if job and job.workflow_run_id:
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job("workflow_orchestrator_job", str(job.workflow_run_id))
        await redis.close()


async def health_check_job(ctx, job_id: str):
    """A simple test job to verify worker infrastructure."""
    logger.info(f"Executing health check job for database ID: {job_id}")
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()
            
            await asyncio.sleep(1) # simulate work
            
            job.status = "COMPLETED"
            await session.commit()
            logger.info(f"Health check job {job_id} completed.")
        else:
            logger.error(f"Job {job_id} not found in database.")

async def company_discovery_job(ctx, job_id: str, request_dict: dict):
    logger.info(f"Executing company discovery job: {job_id}")
    request = DiscoveryRequest(**request_dict)
    
    from app.services.discovery.directory import BusinessDirectoryProvider
    from app.services.discovery.duckduckgo import DuckDuckGoProvider
    from app.services.discovery.github import GitHubOrgProvider

    sources = [s.lower() for s in (request.source_preferences or [])]
    if "directory" in sources or (request.country and "mex" in request.country.lower()):
        provider = BusinessDirectoryProvider()
    elif "github" in sources:
        provider = GitHubOrgProvider()
    else:
        provider = DuckDuckGoProvider()
    
    async with async_session_maker() as session:
        await run_discovery_pipeline(uuid.UUID(job_id), request, provider, session)
    logger.info(f"Finished discovery job: {job_id}")

async def google_drive_sync_job(ctx, company_id: str, sync_type: str = "AUTOMATIC"):
    logger.info(f"Executing google_drive_sync_job for company {company_id}")
    from app.services.gdrive.service import GoogleDriveService
    async with async_session_maker() as session:
        service = GoogleDriveService(session)
        result = await service.sync_company_to_drive(uuid.UUID(company_id), sync_type=sync_type)
        return result


from app.services.intelligence.runner import WebsiteIntelligenceRunner
import uuid

async def website_analysis_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing website analysis job for company: {company_id} (Job: {job_id})")
    
    # Update Job status
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()
    
    runner = WebsiteIntelligenceRunner()
    status = await runner.analyze_company(uuid.UUID(company_id))
    
    # Finalize Job status
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = status if status in ["COMPLETED", "FAILED", "PARTIAL", "TIMEOUT"] else "COMPLETED"
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished website analysis job: {job_id} with status {status}")

from app.services.enrichment.runner import SEOEnrichmentRunner

async def seo_enrichment_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing SEO enrichment job for company: {company_id} (Job: {job_id})")
    
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()
            
    runner = SEOEnrichmentRunner(job_id)
    result = await runner.enrich_company(uuid.UUID(company_id))
    
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = result.get("status", "COMPLETED")
            job.metrics_created = result.get("metrics_created", 0)
            job.metrics_skipped = result.get("metrics_skipped", 0)
            job.provider_error_count = result.get("provider_errors", 0)
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished SEO enrichment job: {job_id} with status {job.status}")


from app.services.ai.runner import AIExtractionRunner

async def ai_extraction_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing AI extraction job for company: {company_id} (Job: {job_id})")
    
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()
            
    runner = AIExtractionRunner(job_id)
    result = await runner.run_extraction(uuid.UUID(company_id))
    
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = result.get("status", "COMPLETED")
            job.successful_count = result.get("observations_created", 0)
            job.partial_count = result.get("contradictions_found", 0) # Use partial_count for contradictions for now
            if result.get("status") == "FAILED":
                job.error_message = result.get("error")
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished AI extraction job: {job_id} with status {job.status}")


from app.services.intelligence.opportunity import OpportunityEngine

async def opportunity_evaluation_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing opportunity evaluation job for company: {company_id} (Job: {job_id})")
    
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()
            
        engine = OpportunityEngine(session)
        try:
            profile_create = await engine.evaluate_company(uuid.UUID(company_id))
            await engine.save_profile(profile_create)
            status = "COMPLETED"
            error = None
        except Exception as e:
            logger.error(f"Error evaluating opportunity for {company_id}: {e}")
            status = "FAILED"
            error = str(e)
            
        if job:
            job.status = status
            if error:
                job.error_message = error
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished opportunity evaluation job: {job_id} with status {status}")

from app.services.matching.engine import MatchingEngine

async def publisher_matching_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing publisher matching job for company: {company_id} (Job: {job_id})")
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            job.started_at = datetime.now(timezone.utc)
            await session.commit()
            
        engine = MatchingEngine(session)
        try:
            match_run = await engine.run_matching(uuid.UUID(company_id))
            status = "COMPLETED"
            error = None
        except Exception as e:
            logger.error(f"Error matching publishers for {company_id}: {e}")
            status = "FAILED"
            error = str(e)
            
        if job:
            job.status = status
            job.completed_at = datetime.now(timezone.utc)
            if error:
                job.error_message = error
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished publisher matching job: {job_id} with status {status}")

from sqlalchemy import select
from app.models import Company, MatchingRun, MatchResult, MediaPlan, MediaPlanItem, PublisherObservation

async def media_plan_generation_job(ctx, job_id: str, company_id: str):
    logger.info(f"Executing media plan generation job for company: {company_id} (Job: {job_id})")
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            job.started_at = datetime.now(timezone.utc)
            await session.commit()
            
        cid = uuid.UUID(company_id)
        company = await session.get(Company, cid)
        
        status = "COMPLETED"
        error = None
        
        try:
            # Find latest completed MatchingRun for this company
            stmt_run = select(MatchingRun).where(
                MatchingRun.company_id == cid,
                MatchingRun.status == "COMPLETED"
            ).order_by(MatchingRun.completed_at.desc()).limit(1)
            latest_match_run = (await session.execute(stmt_run)).scalar_one_or_none()
            
            if not latest_match_run:
                status = "FAILED"
                error = f"No completed MatchingRun found for company {company_id}"
            else:
                # Fetch top matches (top 5 by rank)
                stmt_results = select(MatchResult).where(
                    MatchResult.matching_run_id == latest_match_run.id
                ).order_by(MatchResult.rank.asc()).limit(5)
                top_results = (await session.execute(stmt_results)).scalars().all()
                
                if not top_results:
                    status = "FAILED"
                    error = f"No match results found in run {latest_match_run.id}"
                else:
                    plan_name = f"Media Plan - {company.company_name or company.canonical_domain or 'Client'}"
                    plan = MediaPlan(
                        company_id=cid,
                        name=plan_name,
                        status="DRAFT",
                        notes=f"Auto-generated from Matching Run {latest_match_run.id} in workflow pipeline."
                    )
                    session.add(plan)
                    await session.flush()
                    
                    for match in top_results:
                        stmt_obs = select(PublisherObservation).where(
                            PublisherObservation.publisher_id == match.publisher_id
                        ).order_by(PublisherObservation.observation_timestamp.desc()).limit(1)
                        latest_obs = (await session.execute(stmt_obs)).scalar_one_or_none()
                        
                        price = latest_obs.price if latest_obs else None
                        currency = latest_obs.currency if latest_obs else "USD"
                        
                        item = MediaPlanItem(
                            media_plan_id=plan.id,
                            publisher_id=match.publisher_id,
                            match_result_id=match.id,
                            proposed_price=price,
                            proposed_currency=currency,
                            notes=f"Matched rank #{match.rank} (score: {match.overall_score:.1f})"
                        )
                        session.add(item)
                    await session.commit()
        except Exception as e:
            logger.error(f"Error generating media plan for {company_id}: {e}")
            status = "FAILED"
            error = str(e)
            
        if job:
            job.status = status
            job.completed_at = datetime.now(timezone.utc)
            if error:
                job.error_message = error
            await session.commit()
            
    await _trigger_orchestrator_if_needed(job_id, session)
    logger.info(f"Finished media plan generation job: {job_id} with status {status}")

async def workflow_orchestrator_job(ctx, run_id: str):
    logger.info(f"Executing workflow orchestrator job for run: {run_id}")
    from app.services.orchestrator.runner import WorkflowOrchestrator
    
    async with async_session_maker() as session:
        orchestrator = WorkflowOrchestrator(session)
        await orchestrator.advance_workflow_run(uuid.UUID(run_id))
        
    logger.info(f"Finished workflow orchestrator check for run: {run_id}")

async def workflow_scheduler_tick(ctx):
    logger.info("Running workflow scheduler tick")
    from app.services.orchestrator.runner import WorkflowOrchestrator
    async with async_session_maker() as session:
        orchestrator = WorkflowOrchestrator(session)
        triggered = await orchestrator.evaluate_scheduled_workflows()
        logger.info(f"Scheduler tick evaluated; triggered {len(triggered)} runs")


async def outreach_contact_discovery_job(ctx, company_id: str):
    logger.info(f"Executing outreach contact discovery for company: {company_id}")
    from app.services.outreach.contacts import ContactResearcher
    async with async_session_maker() as session:
        researcher = ContactResearcher(session)
        contacts = await researcher.discover_company_contacts(uuid.UUID(company_id))
        logger.info(f"Discovered {len(contacts)} contacts for company {company_id}")


async def outreach_draft_generation_job(ctx, company_id: str, campaign_id: str = None):
    logger.info(f"Executing outreach draft generation for company: {company_id}")
    from app.services.outreach.personalization import OutreachPersonalizationEngine
    async with async_session_maker() as session:
        engine = OutreachPersonalizationEngine(session)
        cid = uuid.UUID(campaign_id) if campaign_id else None
        draft = await engine.generate_draft(company_id=uuid.UUID(company_id), campaign_id=cid, save=True)
        logger.info(f"Generated outreach draft {draft.id} for company {company_id}")


async def sales_intelligence_evaluation_job(ctx, company_id: str):
    logger.info(f"Executing sales intelligence evaluation for company: {company_id}")
    from app.services.intelligence.sales_intelligence import SalesIntelligenceService
    async with async_session_maker() as session:
        service = SalesIntelligenceService(session)
        score = await service.calculate_priority_score(uuid.UUID(company_id))
        brief = await service.generate_or_get_brief(uuid.UUID(company_id))
        logger.info(f"Completed sales intelligence evaluation for company {company_id} (Score: {score.overall_priority_score})")


async def publisher_quality_audit_job(ctx, publisher_id: str = None, limit: int = 100):
    logger.info(f"Executing publisher quality audit job (publisher_id={publisher_id}, limit={limit})")
    from app.services.publishers.quality_service import PublisherQualityService
    async with async_session_maker() as session:
        service = PublisherQualityService(session)
        if publisher_id:
            score, findings = await service.audit_publisher(uuid.UUID(publisher_id))
            logger.info(f"Audited publisher {publisher_id} (Score: {score.overall_quality_score}, Findings: {len(findings)})")
        else:
            res = await service.audit_all_publishers(limit=limit)
            logger.info(f"Completed batch publisher audit: {res}")


async def publisher_refresh_job(ctx, publisher_id: str, target_fields: list = None, actor: str = "scheduled_worker"):
    logger.info(f"Executing publisher refresh job for {publisher_id}")
    from app.services.publishers.quality_service import PublisherQualityService
    async with async_session_maker() as session:
        service = PublisherQualityService(session)
        fields = target_fields or ["metrics", "site"]
        res = await service.refresh_publisher(uuid.UUID(publisher_id), target_fields=fields, actor=actor)
        logger.info(f"Completed publisher refresh for {publisher_id}: {res}")


async def competitive_analysis_job(ctx, job_id: str, company_id: str, competitor_id: str):
    logger.info(f"Executing competitive analysis job {job_id} for company={company_id} vs competitor={competitor_id}")
    from app.services.intelligence.competitive_service import CompetitiveIntelligenceService
    async with async_session_maker() as session:
        job = await session.get(Job, job_id)
        if job:
            job.status = "RUNNING"
            await session.commit()

        try:
            service = CompetitiveIntelligenceService(session)
            run = await service.run_competitive_analysis(
                company_id=uuid.UUID(company_id),
                competitor_id=uuid.UUID(competitor_id)
            )
            if job:
                job.status = "COMPLETED"
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
            logger.info(f"Completed competitive analysis run {run.id} for company {company_id}")
        except Exception as e:
            logger.error(f"Failed competitive analysis job {job_id}: {e}", exc_info=True)
            if job:
                job.status = "FAILED"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
            raise



async def scheduled_report_generation_job(ctx, job_id: str = None):
    """Worker task that evaluates active report schedules and generates client-ready draft reports."""
    logger.info("Executing scheduled_report_generation_job")
    from app.services.reporting.report_service import ReportingAndPortalService
    async with async_session_maker() as session:
        reports = await ReportingAndPortalService.trigger_scheduled_reports(session)
        logger.info(f"Scheduled report generation job generated {len(reports)} reports.")
        return len(reports)


async def report_delivery_job(ctx, job_id: str, report_id: str, recipient_email: str):
    """Worker task for background report delivery with approval check and idempotency."""
    logger.info(f"Executing report delivery job {job_id} for report={report_id} to={recipient_email}")
    from app.services.reporting.report_service import ReportingAndPortalService
    from app.schemas.portal import ReportDeliveryRequest
    from app.models import PortalUser
    from sqlalchemy import select
    async with async_session_maker() as session:
        stmt = select(PortalUser).where(PortalUser.role == "ADMIN").limit(1)
        admin_user = (await session.execute(stmt)).scalar_one_or_none()
        if not admin_user:
            admin_user = PortalUser(id=uuid.uuid4(), email="system@prospectos.local", role="ADMIN", full_name="System Automation", is_active=True)
        req = ReportDeliveryRequest(recipients=[recipient_email], delivery_channel="EMAIL")
        logs = await ReportingAndPortalService.deliver_report(session, uuid.UUID(report_id), admin_user, req)
        return len(logs)


async def database_backup_job(ctx):
    """Automated daily PostgreSQL backup job executed at 02:00 UTC."""
    logger.info("Executing automated database_backup_job...")
    from app.services.backup.backup_manager import BackupManager
    manager = BackupManager()
    entry = manager.create_backup(retention_days=14)
    logger.info(f"Database backup completed successfully: {entry['filename']} ({entry['size_mb']} MB)")
    return entry


from arq import cron

class WorkerSettings:
    functions = [
        health_check_job,
        company_discovery_job,
        website_analysis_job,
        seo_enrichment_job,
        ai_extraction_job,
        opportunity_evaluation_job,
        publisher_matching_job,
        media_plan_generation_job,
        workflow_orchestrator_job,
        workflow_scheduler_tick,
        outreach_contact_discovery_job,
        outreach_draft_generation_job,
        sales_intelligence_evaluation_job,
        publisher_quality_audit_job,
        publisher_refresh_job,
        competitive_analysis_job,
        scheduled_report_generation_job,
        report_delivery_job,
        database_backup_job,
        google_drive_sync_job,
    ]
    cron_jobs = [
        cron(workflow_scheduler_tick, minute=None, second=0),
        cron(database_backup_job, hour=2, minute=0),
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = None
    on_shutdown = None

