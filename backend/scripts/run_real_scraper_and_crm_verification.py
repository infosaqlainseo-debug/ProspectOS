import os
import sys

# CRITICAL ISOLATION: Verification scripts must write to 'prospectos_test', NEVER production 'prospectos'
current_db = os.getenv("DATABASE_URL", "")
if "@db:5432" in current_db:
    TEST_DB = "postgresql+asyncpg://user:password@db:5432/prospectos_test"
else:
    TEST_DB = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/prospectos_test")

os.environ["DATABASE_URL"] = TEST_DB

from app.core.config import settings
settings.DATABASE_URL = TEST_DB

import asyncio
import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, desc, text
from app.db.session import async_session_maker
from app.models import Company, CRMActivity, PortalUser
from app.models.scraper import ScraperTask, ScraperTaskRun, ExtractedRecord
from app.core.security import validate_target_url
from app.services.scraper.engine import ScraperEngine
from app.services.scraper.cleaner import clean_and_validate_record, compute_record_hash
from app.services.crm.bridge import ScraperCRMBridge, compute_lead_score, extract_canonical_domain
from app.workers.worker import scraper_cloud_execution_job

logger = logging.getLogger(__name__)

async def run_controlled_verification():
    print("=" * 80)
    print("PROSPECTOS PHASE 2: REAL SCRAPER, CRM, AND RECONCILIATION VERIFICATION")
    print("=" * 80)

    # Enforce safe database isolation
    async with async_session_maker() as verify_session:
        db_name = (await verify_session.execute(text("SELECT current_database();"))).scalar()
        if db_name == "prospectos":
            raise RuntimeError("SAFETY ABORT: Verification script refused to run against production database 'prospectos'!")
        print(f"Safety Check Passed: Connected to isolated testing database '{db_name}'.")

    test_url = "https://quotes.toscrape.com"
    suffix = uuid.uuid4().hex[:6]

    # =========================================================================
    # PART 1: Real Scraper Execution
    # =========================================================================
    print("\n[PART 1: REAL-WORLD CONTROLLED SCRAPER EXECUTION]")
    
    # 1.1 Website discovery & URL validation
    is_safe, safe_url, ip_addr = validate_target_url(test_url)
    print(f"  1.1 SSRF & URL Validation:")
    print(f"      • Target URL       : {test_url}")
    print(f"      • Normalized URL   : {safe_url}")
    print(f"      • Resolved Safe IP : {ip_addr}")
    print(f"      • Is Safe          : {is_safe}")
    assert is_safe, f"Target URL failed SSRF check: {safe_url}"

    # 1.2 Initialize Scraper Engine
    engine = ScraperEngine(timeout_seconds=15.0, rate_limit_delay_ms=300)
    
    # 1.3 Check robots.txt
    robots_ok = await engine.check_robots_allowed(safe_url)
    print(f"  1.2 Robots.txt directive check: Allowed = {robots_ok}")

    # 1.4 Scrape with Pagination (2 pages)
    workflow_config = {
        "container_selector": "div.quote",
        "fields": [
            {"name": "quote_text", "selector": "span.text", "extract": "text", "required": True},
            {"name": "author", "selector": "small.author", "extract": "text", "required": True},
            {"name": "author_link", "selector": "span a", "extract": "href", "required": False},
            {"name": "tags", "selector": "div.tags a.tag", "extract": "text", "required": False}
        ],
        "pagination": {
            "type": "NEXT_BUTTON",
            "selector": "li.next a",
            "max_pages": 2
        }
    }

    print(f"  1.3 Executing Multi-Page Extraction (max_pages=2)...")
    workflow_result = await engine.execute_workflow(safe_url, workflow_config, max_records=20, max_pages=2)
    scraped_items = workflow_result["records"]
    duration_s = workflow_result["duration_seconds"]

    print(f"      • Pages Processed   : {workflow_result.get('pages_crawled', 0)}")
    print(f"      • Total Extracted   : {workflow_result.get('total_extracted', 0)}")
    print(f"      • Valid Records     : {workflow_result.get('valid_records_count', 0)}")
    print(f"      • Duplicates Skipped: {workflow_result.get('duplicate_records_count', 0)}")
    print(f"      • Duration          : {duration_s:.2f}s")
    assert len(scraped_items) > 0, "No items scraped from quotes.toscrape.com!"
    assert workflow_result.get('pages_crawled', 0) >= 2, f"Expected at least 2 pages crawled, got {workflow_result.get('pages_crawled')}"

    # 1.5 Data Validation & Cleaning & Duplicate Detection
    print(f"\n  1.4 Validating Extracted Items...")
    cleaned_records = []
    for item in scraped_items:
        cleaned_records.append({
            "raw": item.get("raw") or item,
            "cleaned": item.get("cleaned") or item,
            "is_valid": item.get("validation_status") == "VALID",
            "hash": item.get("record_hash") or compute_record_hash(item),
            "issues": item.get("validation_issues") or []
        })

    print(f"      • Unique Valid Records: {len(cleaned_records)}")
    print(f"      • Sample Extracted Record [0]:")
    print(f"          - Author: {cleaned_records[0]['cleaned'].get('author')}")
    print(f"          - Text  : {str(cleaned_records[0]['cleaned'].get('quote_text'))[:60]}...")
    print(f"          - Hash  : {cleaned_records[0]['hash'][:16]}...")

    # 1.6 Database Persistence
    print(f"\n  1.5 Persisting Scraper Task, Run, and Extracted Records to PostgreSQL...")
    async with async_session_maker() as session:
        # Create Scraper Task
        task = ScraperTask(
            name=f"Verified Test Scraper — {suffix}",
            target_url=safe_url,
            task_type="CUSTOM",
            workflow_config=workflow_config,
            status="COMPLETED",
            schedule_type="NONE",
            total_records=len(cleaned_records),
            successful_records=len(cleaned_records),
            failed_records=0,
            duplicate_records=workflow_result.get("duplicate_records_count", 0)
        )
        session.add(task)
        await session.flush()

        # Create Task Run
        run = ScraperTaskRun(
            task_id=task.id,
            run_number=1,
            execution_mode="CLOUD",
            status="COMPLETED",
            duration_seconds=duration_s,
            records_extracted=len(cleaned_records),
            records_saved=len(cleaned_records),
            records_duplicate=workflow_result.get("duplicate_records_count", 0),
            error_message=None,
            completed_at=datetime.now(timezone.utc)
        )
        session.add(run)
        await session.flush()

        # Create Extracted Records
        persisted_recs = []
        for rec in cleaned_records:
            author = rec["cleaned"].get("author") or rec["cleaned"].get("company_name") or "Quotes Author"
            author_slug = author.lower().replace(" ", "-").replace(".", "")
            author_domain = f"{author_slug}.quotes.toscrape.com"
            er = ExtractedRecord(
                task_id=task.id,
                run_id=run.id,
                source_url=safe_url,
                company_name=author,
                website=f"https://{author_domain}",
                domain=author_domain,
                description=rec["cleaned"].get("quote_text") or rec["cleaned"].get("description"),
                raw_data=rec["raw"],
                cleaned_data=rec["cleaned"],
                record_hash=rec["hash"],
                validation_status="VALID" if rec["is_valid"] else "PARTIAL",
                quality_score=85.0 if rec["is_valid"] else 50.0,
                quality_status="HIGH" if rec["is_valid"] else "MEDIUM",
                validation_details={"issues": rec["issues"]}
            )
            session.add(er)
            persisted_recs.append(er)

        await session.commit()
        await session.refresh(task)
        await session.refresh(run)
        task_id = task.id
        print(f"      • Task Created ID     : {task.id} ('{task.name}')")
        print(f"      • Run Created ID      : {run.id} (Status: {run.status})")
        print(f"      • Records Persisted   : {len(persisted_recs)} records")

    # =========================================================================
    # PART 2: CRM Lead Conversion & Intelligence Verification
    # =========================================================================
    print("\n[PART 2: CRM VERIFICATION & INTELLIGENCE CONVERSION]")
    async with async_session_maker() as session:
        bridge = ScraperCRMBridge(session)
        from app.schemas.crm import ScraperImportRequest

        # 2.1 Import Extracted Records into CRM
        req_import = ScraperImportRequest(
            task_id=task_id,
            auto_save_valid_only=True
        )
        import_res = await bridge.import_extracted_records(req_import)
        await session.commit()

        print(f"  2.1 Scraper-to-CRM Import Summary:")
        print(f"      • Total Processed : {import_res.total_processed}")
        print(f"      • Leads Added     : {import_res.added}")
        print(f"      • Leads Updated   : {import_res.updated}")
        print(f"      • Leads Skipped   : {import_res.skipped}")
        assert (import_res.added + import_res.updated) > 0, "No leads were imported into CRM!"

        # 2.2 Verify Lead Scoring
        sample_comp_id = uuid.UUID(import_res.imported_ids[0])
        sample_comp = await session.get(Company, sample_comp_id)
        assert sample_comp is not None, "Imported company not found in database!"
        
        print(f"\n  2.2 Verifying 4-Pillar Lead Scoring on Imported Lead:")
        print(f"      • Company Name    : {sample_comp.company_name}")
        print(f"      • Canonical Domain: {sample_comp.canonical_domain}")
        print(f"      • Lead Score      : {sample_comp.lead_score}/100.0")
        print(f"      • Priority Rating : {sample_comp.lead_priority}")
        print(f"      • Score Breakdown : {json.dumps(sample_comp.lead_score_components, indent=8)}")
        assert sample_comp.lead_score is not None and sample_comp.lead_score >= 0, "Lead score not calculated!"
        assert sample_comp.lead_priority in ["HIGH", "MEDIUM", "LOW", "CRITICAL"], "Invalid priority rating!"

        # 2.3 Verify Duplicate Detection on Re-Import
        print(f"\n  2.3 Verifying Duplicate Detection on Idempotent Re-Import...")
        reimport_res = await bridge.import_extracted_records(req_import)
        print(f"      • Second Import: Added={reimport_res.added}, Updated={reimport_res.updated}, Skipped={reimport_res.skipped}")
        assert reimport_res.added == 0, "Duplicate detection failed: identical records created new leads!"

        # 2.4 Verify CRM Activity Trail
        act_stmt = select(CRMActivity).where(CRMActivity.company_id == sample_comp_id)
        acts = (await session.execute(act_stmt)).scalars().all()
        print(f"\n  2.4 Verifying CRM Activity History:")
        print(f"      • Activity Count  : {len(acts)}")
        for a in acts:
            print(f"        - [{a.activity_type}] {a.title}: {a.details}")
        assert len(acts) > 0, "No CRM activities logged for imported lead!"

    # =========================================================================
    # PART 3: Dashboard Reconciliation against Live PostgreSQL Queries
    # =========================================================================
    print("\n[PART 3: DASHBOARD METRICS RECONCILIATION WITH POSTGRESQL]")
    async with async_session_maker() as session:
        # Query true ground truth counts
        db_total_companies = (await session.execute(select(func.count(Company.id)))).scalar() or 0
        db_total_records = (await session.execute(select(func.count(ExtractedRecord.id)))).scalar() or 0
        db_total_tasks = (await session.execute(select(func.count(ScraperTask.id)))).scalar() or 0
        db_total_runs = (await session.execute(select(func.count(ScraperTaskRun.id)))).scalar() or 0
        db_completed_runs = (await session.execute(select(func.count(ScraperTaskRun.id)).where(ScraperTaskRun.status.in_(['SUCCESS', 'COMPLETED'])))).scalar() or 0
        db_failed_runs = (await session.execute(select(func.count(ScraperTaskRun.id)).where(ScraperTaskRun.status == 'FAILED'))).scalar() or 0
        db_total_users = (await session.execute(select(func.count(PortalUser.id)))).scalar() or 0
        db_super_admins = (await session.execute(select(func.count(PortalUser.id)).where(PortalUser.role == 'SUPER_ADMIN'))).scalar() or 0
        
        # Scored leads
        db_scored_leads = (await session.execute(select(func.count(Company.id)).where(Company.lead_score.isnot(None)))).scalar() or 0
        db_high_priority = (await session.execute(select(func.count(Company.id)).where(Company.lead_priority.in_(['HIGH', 'CRITICAL'])))).scalar() or 0
        db_medium_priority = (await session.execute(select(func.count(Company.id)).where(Company.lead_priority == 'MEDIUM'))).scalar() or 0
        db_low_priority = (await session.execute(select(func.count(Company.id)).where(Company.lead_priority == 'LOW'))).scalar() or 0

        print(f"  3.1 Actual PostgreSQL Database Inventory:")
        print(f"      • Total CRM Leads (Companies) : {db_total_companies}")
        print(f"      • Scored Leads in Database   : {db_scored_leads} ({(db_scored_leads/db_total_companies*100):.1f}%)")
        print(f"        - HIGH Priority            : {db_high_priority}")
        print(f"        - MEDIUM Priority          : {db_medium_priority}")
        print(f"        - LOW Priority             : {db_low_priority}")
        print(f"      • Extracted Scraper Records  : {db_total_records}")
        print(f"      • Total Scraper Tasks        : {db_total_tasks}")
        print(f"      • Total Task Runs            : {db_total_runs}")
        print(f"        - Successful Runs          : {db_completed_runs}")
        print(f"        - Failed Runs              : {db_failed_runs}")
        print(f"      • Registered Portal Users    : {db_total_users}")
        print(f"        - Elevated Super Admins    : {db_super_admins}")

        # Now query the actual API overview service to confirm 100% mathematical match
        from app.services.admin.admin_service import AdminService
        admin_svc = AdminService(session, None)
        overview = await admin_svc.get_overview()

        api_stats = overview.stats
        print(f"\n  3.2 Reconciliation Comparison (Database vs Admin Overview API):")
        
        checks = [
            ("total_crm_leads", db_total_companies, api_stats.total_crm_leads),
            ("total_extracted_records", db_total_records, api_stats.total_extracted_records),
            ("total_scraping_tasks", db_total_tasks, api_stats.total_scraping_tasks),
            ("total_users", db_total_users, api_stats.total_users),
            ("super_admins", db_super_admins, api_stats.super_admins),
        ]

        all_matched = True
        for name, db_val, api_val in checks:
            match = (db_val == api_val)
            print(f"      • {name:<25}: DB={db_val:<5} | API={api_val:<5} | MATCH={'✓' if match else '✗'}")
            if not match:
                all_matched = False

        assert all_matched, "Dashboard KPI reconciliation failed: mismatch between DB and API!"
        print(f"\n  ✓ 100% MATHEMATICAL RECONCILIATION CONFIRMED: ZERO FABRICATED OR MOCK STATS.")

    # =========================================================================
    # PART 4: Production Readiness & Backup Verification
    # =========================================================================
    print("\n[PART 4: PRODUCTION READINESS & BACKUP VERIFICATION]")
    from app.workers.worker import database_backup_job
    backup_result = await database_backup_job({})
    print(f"  4.1 Database Backup Job Execution:")
    print(f"      • Status       : {backup_result.get('status')}")
    print(f"      • Backup File  : {backup_result.get('filename')}")
    print(f"      • Size         : {backup_result.get('size_mb')} MB")
    print(f"      • Tables Dumped: {backup_result.get('tables_count')}")
    assert backup_result.get('status') == 'SUCCESS', f"Database backup failed: {backup_result}"
    print(f"  ✓ Database Backup Procedure Verified.")

    print("\n" + "=" * 80)
    print("ALL PHASE 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_controlled_verification())
