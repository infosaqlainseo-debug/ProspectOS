"""
Script: run_live_ahrefs_verification.py
Description: Production-Readiness Live Verification for Ahrefs API v3.
Audits configuration, performs a minimal authorized live request for techcrunch.com,
validates response schema and metric mapping, persists records into PostgreSQL
using standard ProspectOS models and runners, and queries stored records with provenance.
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
from app.models import Company, Job, SEOMetric, HistoricalSnapshot, Evidence, ProviderUsage
from app.services.providers.ahrefs import AhrefsProvider
from app.services.enrichment.runner import SEOEnrichmentRunner


async def run_live_ahrefs_verification():
    print("=" * 80)
    print("PROSPECTOS: LIVE AHREFS API V3 INTEGRATION & PERSISTENCE VERIFICATION")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Configuration & Security Audit
    # -------------------------------------------------------------------------
    print("\n[1. Configuration & Security Inspection]")
    env_var_name = "AHREFS_API_KEY"
    api_key = getattr(settings, env_var_name, None)

    if not api_key:
        print(f"  ❌ FAILED: Environment variable '{env_var_name}' is unset or empty.")
        print(f"  Please configure {env_var_name} in backend/.env before running.")
        return False

    # Mask key strictly
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"  • Expected Env Variable : {env_var_name}")
    print(f"  • Configuration Status  : CONFIGURED (Masked: {masked_key})")
    print(f"  • Provider Adapter      : AhrefsProvider (app.services.providers.ahrefs)")
    print(f"  • Base API Endpoint     : {AhrefsProvider.base_url} (Ahrefs API v3)")

    if not AhrefsProvider.base_url.endswith("/v3"):
        print("  ❌ ERROR: Adapter does not use current Ahrefs API v3.")
        return False
    print("  ✓ Confirmed API v3 compliance (no deprecated v2 endpoints).")

    # -------------------------------------------------------------------------
    # 2. Minimal Live API Request
    # -------------------------------------------------------------------------
    target_domain = "techcrunch.com"
    print(f"\n[2. Executing Minimal Live Request for '{target_domain}']")
    print("  • Endpoint Target   : /public/domain-rating-free (Eligible zero-cost free test)")
    print("  • Unit Consumption  : 0.0 units (Protects account API quota)")
    
    provider = AhrefsProvider()
    resp = await provider.get_authority_metrics(target_domain)

    print(f"  • Provider Name     : {resp.provider_name}")
    print(f"  • Endpoint Used     : {resp.endpoint}")
    print(f"  • Request Error     : {resp.error or 'None (SUCCESS)'}")
    print(f"  • API Units Tracked : {resp.usage_units}")

    if resp.error:
        print(f"  ❌ Live Request Failed: {resp.error}")
        return False

    if not resp.metrics:
        print("  ❌ ERROR: No metrics returned in ProviderResponse.")
        return False

    # -------------------------------------------------------------------------
    # 3. Response Schema & Metric Mapping Validation
    # -------------------------------------------------------------------------
    print(f"\n[3. Response Schema & Metric Mapping Validation]")
    dr_metric = resp.metrics[0]
    print(f"  • Metric Name       : {dr_metric.metric_name}")
    print(f"  • Metric Value      : {dr_metric.value}")
    print(f"  • Verification Tag  : {dr_metric.status}")
    print(f"  • Raw Reference Data: {dr_metric.raw_reference}")

    assert dr_metric.metric_name == "domain_rating", "Expected metric name 'domain_rating'"
    assert dr_metric.value is not None and isinstance(dr_metric.value, float), "Expected float domain rating"
    assert dr_metric.value > 0.0, "Domain rating must be greater than zero for valid domain"
    assert dr_metric.status == "VERIFIED_PROVIDER_RESPONSE", "Status must be VERIFIED_PROVIDER_RESPONSE"
    print("  ✓ Schema and non-fabrication validated (non-zero live metric, no synthetic zeroes).")

    # -------------------------------------------------------------------------
    # 4. Persistence into PostgreSQL Database
    # -------------------------------------------------------------------------
    print(f"\n[4. Database Persistence via Existing ProspectOS Services]")
    async with async_session_maker() as session:
        # Check target company
        stmt = select(Company).where(Company.canonical_domain == target_domain)
        company = (await session.execute(stmt)).scalar_one_or_none()

        if not company:
            company = Company(
                company_name="TechCrunch",
                canonical_domain=target_domain,
                website_url=f"https://{target_domain}"
            )
            session.add(company)
            await session.commit()
            await session.refresh(company)
            print(f"  • Created Company Record: ID={company.id}")
        else:
            print(f"  • Found Existing Company Record: ID={company.id} ({company.company_name})")

        # Create tracking Job
        test_job = Job(
            job_type="ahrefs_live_verification",
            status="RUNNING"
        )
        session.add(test_job)
        await session.commit()
        await session.refresh(test_job)
        print(f"  • Created Verification Job : ID={test_job.id}")

        # Use runner persistence methods
        runner = SEOEnrichmentRunner(job_id=str(test_job.id))
        mc, ms = await runner._save_metrics(session, company.id, target_domain, resp, resp.provider_name)
        await runner._track_usage(session, company.id, resp.provider_name, resp)
        
        test_job.status = "COMPLETED"
        await session.commit()
        print(f"  ✓ Saved Metrics: Created={mc}, Skipped={ms}")
        print(f"  ✓ Tracked Usage: Job ID={test_job.id}, Status=COMPLETED")

    # -------------------------------------------------------------------------
    # 5. Database Verification Query & Provenance Assertion
    # -------------------------------------------------------------------------
    print(f"\n[5. Database Verification & Provenance Confirmation]")
    async with async_session_maker() as session:
        # Query SEOMetric
        metric_stmt = select(SEOMetric).where(
            SEOMetric.company_id == company.id,
            SEOMetric.provider == resp.provider_name,
            SEOMetric.metric_name == "domain_rating"
        ).order_by(SEOMetric.created_at.desc())
        stored_metric = (await session.execute(metric_stmt)).scalars().first()

        assert stored_metric is not None, "SEOMetric row not found in database!"
        print(f"  • SEOMetric Record      : ID={stored_metric.id}")
        print(f"    - Company ID          : {stored_metric.company_id}")
        print(f"    - Domain              : {stored_metric.domain}")
        print(f"    - Provider            : {stored_metric.provider}")
        print(f"    - Provider Endpoint   : {stored_metric.provider_endpoint}")
        print(f"    - Metric Name         : {stored_metric.metric_name}")
        print(f"    - Metric Value        : {stored_metric.metric_value}")
        print(f"    - Verification Status : {stored_metric.verification_status}")
        print(f"    - Retrieved Timestamp : {stored_metric.retrieved_at.isoformat()}")
        print(f"    - Raw Reference       : {stored_metric.raw_reference}")

        # Query HistoricalSnapshot
        snap_stmt = select(HistoricalSnapshot).where(
            HistoricalSnapshot.company_id == company.id,
            HistoricalSnapshot.provider == resp.provider_name
        ).order_by(HistoricalSnapshot.created_at.desc())
        stored_snap = (await session.execute(snap_stmt)).scalars().first()
        assert stored_snap is not None, "HistoricalSnapshot row not found!"
        print(f"  • HistoricalSnapshot    : ID={stored_snap.id}, Metric={stored_snap.metric_name}, Value={stored_snap.metric_value}")

        # Query Evidence
        ev_stmt = select(Evidence).where(
            Evidence.company_id == company.id,
            Evidence.provider == resp.provider_name
        ).order_by(Evidence.created_at.desc())
        stored_ev = (await session.execute(ev_stmt)).scalars().first()
        assert stored_ev is not None, "Evidence row not found!"
        print(f"  • Evidence Record       : ID={stored_ev.id}, Field={stored_ev.field_name}, Value={stored_ev.value}, Status={stored_ev.verification_status}")

        # Query ProviderUsage
        usage_stmt = select(ProviderUsage).where(
            ProviderUsage.job_id == test_job.id
        ).order_by(ProviderUsage.timestamp.desc())
        stored_usage = (await session.execute(usage_stmt)).scalars().first()
        assert stored_usage is not None, "ProviderUsage row not found!"
        print(f"  • ProviderUsage Record  : ID={stored_usage.id}, Units={stored_usage.estimated_units}, Endpoint={stored_usage.endpoint}")

    print("\n" + "=" * 80)
    print("ALL VERIFICATION CHECKS PASSED: AHREFS API V3 IS OPERATIONAL IN POSTGRESQL")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_live_ahrefs_verification())
    if not success:
        sys.exit(1)
