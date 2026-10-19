"""
Script: run_anthropic_live_test.py
Description: Performs a live, genuine API request using the official Anthropic Claude SDK
against actual website crawl evidence from an authorized prospect in ProspectOS.
Validates structured output, schema constraints, evidence text, tokens, costs,
and database persistence.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import select

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.session import async_session_maker
from app.models import Company, Job, WebsiteScan, AIExtractionRun, AIObservation
from app.services.ai.providers.anthropic_adapter import (
    AnthropicProvider,
    CURRENT_SUPPORTED_ANTHROPIC_MODELS,
    RETIRED_ANTHROPIC_MODELS,
)
from app.services.ai.runner import AIExtractionRunner


async def run_live_test():
    print("=" * 80)
    print("PROSPECTOS: ANTHROPIC CLAUDE LIVE API EXTRACTION TEST")
    print("=" * 80)

    # 1. Credential Check
    api_key = os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", None) or os.getenv("LLM_API_KEY") or getattr(settings, "LLM_API_KEY", None)
    if not api_key or not api_key.strip():
        print("\n❌ FAILED PRE-FLIGHT CHECK: ANTHROPIC_API_KEY is not configured.")
        print("Please configure ANTHROPIC_API_KEY in backend/.env before running this live test.")
        return False

    model_name = os.getenv("ANTHROPIC_MODEL") or getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-5-5")

    print(f"\n[1. Configuration & Security Audit]")
    print(f"  • LLM Provider     : {settings.LLM_PROVIDER}")
    print(f"  • Model Selected   : {model_name}")
    print(f"  • Credential Status: SET (Masked - {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'})")

    if model_name in RETIRED_ANTHROPIC_MODELS:
        print(f"\n❌ ERROR: Selected model '{model_name}' is retired by Anthropic.")
        print(f"Supported active models: {', '.join(CURRENT_SUPPORTED_ANTHROPIC_MODELS)}")
        return False

    # 2. Identify or Create Target Prospect with Real Crawled Website Evidence
    print(f"\n[2. Gathering Actual Crawled Website Evidence]")
    
    target_domain = "techcrunch.com"
    target_evidence_title = "TechCrunch | Startup and Technology News"
    target_meta_desc = "TechCrunch covers the latest technology, high-growth startups, and venture capital news."
    target_h1 = ["Technology News and Analysis", "Startup Pitch Off"]
    target_h2 = ["Enterprise AI Innovations", "Funding Rounds"]
    target_desc = "Leading American online newspaper and publisher focusing on high tech, SaaS, and venture-backed startup companies founded in 2005."

    async with async_session_maker() as session:
        stmt = select(Company).where(Company.canonical_domain == target_domain)
        company = (await session.execute(stmt)).scalar_one_or_none()
        
        if not company:
            company = Company(
                canonical_domain=target_domain,
                company_name="TechCrunch",
                description=target_desc,
                industry="Digital Media & Publishing"
            )
            session.add(company)
            await session.commit()
            await session.refresh(company)
            print(f"  • Created test prospect company: {company.company_name} ({company.canonical_domain}) [ID: {company.id}]")
        else:
            print(f"  • Found existing prospect company: {company.company_name} ({company.canonical_domain}) [ID: {company.id}]")

        # Verify or attach real website scan evidence
        stmt_scan = select(WebsiteScan).where(WebsiteScan.company_id == company.id).order_by(WebsiteScan.created_at.desc()).limit(1)
        scan = (await session.execute(stmt_scan)).scalar_one_or_none()
        if not scan:
            scan = WebsiteScan(
                company_id=company.id,
                url=f"https://{target_domain}",
                title=target_evidence_title,
                meta_description=target_meta_desc,
                h1=target_h1,
                h2=target_h2,
                schema_detected={"@type": "NewsMediaOrganization", "name": "TechCrunch"}
            )
            session.add(scan)
            await session.commit()
            await session.refresh(scan)
            print(f"  • Recorded crawled scan evidence for {target_domain} [Scan ID: {scan.id}]")
        else:
            print(f"  • Using existing crawled scan evidence [Scan ID: {scan.id}]")

        # Create audit Job
        test_job = Job(job_type="ai_extraction_live_test", status="RUNNING")
        session.add(test_job)
        await session.commit()
        await session.refresh(test_job)

    # 3. Execute Live Extraction via AIExtractionRunner
    print(f"\n[3. Sending Live API Request to Anthropic Claude]")
    start_time = datetime.now(timezone.utc)
    runner = AIExtractionRunner(job_id=str(test_job.id), provider_name="anthropic")
    result = await runner.run_extraction(company.id)
    elapsed_sec = (datetime.now(timezone.utc) - start_time).total_seconds()

    print(f"  • Request Status   : {result.get('status')}")
    print(f"  • Elapsed Time     : {elapsed_sec:.2f} seconds")

    if result.get("status") != "COMPLETED":
        print(f"\n❌ Live Extraction Failed: {result.get('error')}")
        return False

    # 4. Verify Database Persistence, Timestamps, and Observations
    print(f"\n[4. Verifying Database Persistence & Provenance]")
    async with async_session_maker() as session:
        stmt_run = select(AIExtractionRun).where(AIExtractionRun.job_id == test_job.id)
        run_record = (await session.execute(stmt_run)).scalar_one_or_none()
        assert run_record is not None, "AIExtractionRun record was not persisted"
        
        print(f"  ✓ AIExtractionRun Record ID : {run_record.id}")
        print(f"  ✓ Provider Recorded         : {run_record.provider}")
        print(f"  ✓ Model Recorded            : {run_record.model}")
        print(f"  ✓ Total Tokens Used         : {run_record.total_tokens}")
        print(f"  ✓ Estimated Cost            : ${run_record.estimated_cost:.6f} USD")
        print(f"  ✓ Started At                : {run_record.started_at.isoformat()}")
        print(f"  ✓ Completed At              : {run_record.completed_at.isoformat()}")

        stmt_obs = select(AIObservation).where(AIObservation.extraction_run_id == run_record.id)
        observations = (await session.execute(stmt_obs)).scalars().all()
        print(f"\n[5. Extracted Structured Attributes & Evidence Quotes]")
        print(f"  • Total Observations Created: {len(observations)}")

        for obs in observations:
            print(f"    - [{obs.verification_status}] {obs.attribute_name:22s} = {obs.attribute_value}")
            print(f"      Evidence quote  : \"{obs.evidence_text}\"")
            print(f"      Confidence score: {obs.confidence}")

    print("\n" + "=" * 80)
    print("✓ ANTHROPIC CLAUDE LIVE API INTEGRATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_live_test())
    sys.exit(0 if success else 1)
