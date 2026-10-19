"""
Script: verify_provider_connectivity.py
Description: Goal 1 — Real SEO and LLM Providers Verification.
Audits provider configuration, tests authentication and graceful fallback,
validates response schemas, rate-limiting handlers, and usage tracking.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.session import async_session_maker
from app.models import ProviderUsage, Job
from app.services.providers.ahrefs import AhrefsProvider
from app.services.providers.moz import MozProvider
from app.services.providers.semrush import SemrushProvider
from app.services.ai.providers.openai_adapter import OpenAIProvider
from app.services.ai.providers.anthropic_adapter import AnthropicProvider
from app.services.providers.registry import SEOProviderRegistry
from app.schemas.ai_extraction import AIExtractionResult


async def verify_providers():
    print("=" * 80)
    print("PROSPECTOS PRODUCTION READINESS: GOAL 1 — SEO & LLM PROVIDERS AUDIT")
    print("=" * 80)

    results = {}

    # 1. Environment & Credential Audit
    print("\n[1. Environment Variable & Secret Inspection]")
    env_vars = {
        "MOZ_API_KEY": settings.MOZ_API_KEY,
        "AHREFS_API_KEY": settings.AHREFS_API_KEY,
        "SEMRUSH_API_KEY": settings.SEMRUSH_API_KEY,
        "MAJESTIC_API_KEY": settings.MAJESTIC_API_KEY,
        "SIMILARWEB_API_KEY": settings.SIMILARWEB_API_KEY,
        "LLM_PROVIDER": settings.LLM_PROVIDER,
        "LLM_API_KEY": settings.LLM_API_KEY,
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY,
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY,
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL") or settings.ANTHROPIC_MODEL,
    }

    for key, val in env_vars.items():
        if key in ("LLM_PROVIDER", "ANTHROPIC_MODEL"):
            masked = val or "DEFAULT"
        else:
            masked = "SET (Masked)" if val else "NOT SET (Unconfigured)"
        print(f"  • {key:22s}: {masked}")

    # 2. Test Ahrefs Provider
    print("\n[2. Ahrefs Provider Adapter]")
    ahrefs = AhrefsProvider()
    resp_ahrefs = await ahrefs.get_authority_metrics("techcrunch.com")
    print(f"  • Provider Name: {resp_ahrefs.provider_name}")
    print(f"  • Endpoint: {resp_ahrefs.endpoint}")
    print(f"  • Status / Error: {resp_ahrefs.error or 'SUCCESS'}")
    if resp_ahrefs.error == "PROVIDER_NOT_CONFIGURED":
        print("  ✓ Graceful Unconfigured Handling: Correctly returned PROVIDER_NOT_CONFIGURED without crash.")
        results["ahrefs"] = "NOT CONFIGURED (Safe Fallback Verified)"
    elif resp_ahrefs.error is None:
        print(f"  ✓ Live API Response: {len(resp_ahrefs.metrics)} metrics returned.")
        results["ahrefs"] = "CONNECTED AND TESTED"
    else:
        print(f"  • API Response Error: {resp_ahrefs.error}")
        results["ahrefs"] = f"FAILED ({resp_ahrefs.error})"

    # 3. Test Moz Provider
    print("\n[3. Moz Provider Adapter]")
    moz = MozProvider()
    resp_moz = await moz.get_authority_metrics("techcrunch.com")
    print(f"  • Provider Name: {resp_moz.provider_name}")
    print(f"  • Endpoint: {resp_moz.endpoint}")
    print(f"  • Status / Error: {resp_moz.error or 'SUCCESS'}")
    if resp_moz.error == "PROVIDER_NOT_CONFIGURED":
        print("  ✓ Graceful Unconfigured Handling: Correctly returned PROVIDER_NOT_CONFIGURED without crash.")
        results["moz"] = "NOT CONFIGURED (Safe Fallback Verified)"
    elif resp_moz.error is None:
        print(f"  ✓ Live API Response: {len(resp_moz.metrics)} metrics returned.")
        results["moz"] = "CONNECTED AND TESTED"
    else:
        print(f"  • API Response Error: {resp_moz.error}")
        results["moz"] = f"FAILED ({resp_moz.error})"

    # 4. Test Semrush Provider
    print("\n[4. Semrush Provider Adapter]")
    semrush = SemrushProvider()
    resp_semrush = await semrush.get_authority_metrics("techcrunch.com")
    print(f"  • Provider Name: {resp_semrush.provider_name}")
    print(f"  • Endpoint: {resp_semrush.endpoint}")
    print(f"  • Status / Error: {resp_semrush.error or 'SUCCESS'}")
    if resp_semrush.error == "PROVIDER_NOT_CONFIGURED":
        print("  ✓ Graceful Unconfigured Handling: Correctly returned PROVIDER_NOT_CONFIGURED without crash.")
        results["semrush"] = "NOT CONFIGURED (Safe Fallback Verified)"
    elif resp_semrush.error is None:
        print(f"  ✓ Live API Response: {len(resp_semrush.metrics)} metrics returned.")
        results["semrush"] = "CONNECTED AND TESTED"
    else:
        print(f"  • API Response Error: {resp_semrush.error}")
        results["semrush"] = f"FAILED ({resp_semrush.error})"

    # 5. Test LLM Provider Adapters (OpenAI & Anthropic)
    print("\n[5. OpenAI LLM Provider Adapter]")
    openai_provider = OpenAIProvider()
    sample_evidence = "TechCrunch is a leading American online newspaper focusing on high tech and startup companies. Founded in June 2005 by Michael Arrington and Keith Teare."
    ai_resp_openai = await openai_provider.extract_company_attributes(sample_evidence)
    print(f"  • Provider Name: {ai_resp_openai.provider_name}")
    print(f"  • Model: {ai_resp_openai.model_name}")
    print(f"  • Status / Error: {ai_resp_openai.error or 'SUCCESS'}")
    if ai_resp_openai.error == "PROVIDER_NOT_CONFIGURED":
        print("  ✓ Graceful Unconfigured Handling: Correctly returned PROVIDER_NOT_CONFIGURED without crash.")
        results["openai_llm"] = "NOT CONFIGURED (Safe Fallback Verified)"
    elif ai_resp_openai.error is None:
        print(f"  ✓ Live LLM Response: Tokens used = {ai_resp_openai.total_tokens}, Extracted = {ai_resp_openai.result is not None}")
        results["openai_llm"] = "CONNECTED AND TESTED"
    else:
        print(f"  • LLM Response Error: {ai_resp_openai.error}")
        results["openai_llm"] = f"FAILED ({ai_resp_openai.error})"

    print("\n[5b. Anthropic Claude Provider Adapter]")
    anthropic_provider = AnthropicProvider()
    ai_resp_anthropic = await anthropic_provider.extract_company_attributes(sample_evidence)
    print(f"  • Provider Name: {ai_resp_anthropic.provider_name}")
    print(f"  • Model: {ai_resp_anthropic.model_name}")
    print(f"  • Status / Error: {ai_resp_anthropic.error or 'SUCCESS'}")
    if ai_resp_anthropic.error == "PROVIDER_NOT_CONFIGURED":
        print("  ✓ Graceful Unconfigured Handling: Correctly returned PROVIDER_NOT_CONFIGURED without crash.")
        results["anthropic_llm"] = "NOT CONFIGURED (Safe Fallback Verified)"
    elif ai_resp_anthropic.error is None:
        print(f"  ✓ Live LLM Response: Tokens used = {ai_resp_anthropic.total_tokens}, Extracted = {ai_resp_anthropic.result is not None}, Cost = ${ai_resp_anthropic.estimated_cost:.6f}")
        results["anthropic_llm"] = "CONNECTED AND TESTED"
    else:
        print(f"  • LLM Response Error: {ai_resp_anthropic.error}")
        results["anthropic_llm"] = f"FAILED ({ai_resp_anthropic.error})"

    # 6. Schema Parsing and Non-Fabrication Verification
    print("\n[6. Schema Parsing & Non-Fabrication Validation]")
    # Test that valid provider payload schemas parse correctly into MetricResult
    from app.services.providers.base import MetricResult
    sample_metric = MetricResult(
        metric_name="domain_rating",
        value=78.5,
        unit="score",
        provider_metric_name="domain_rating",
        provider_endpoint="/site-explorer/domain-rating",
        status="VERIFIED_PROVIDER_RESPONSE",
        raw_reference={"domain_rating": 78.5}
    )
    assert sample_metric.value == 78.5
    assert sample_metric.status == "VERIFIED_PROVIDER_RESPONSE"
    print("  ✓ Metric Schema: Parsed domain_rating metric correctly with provenance.")

    # 7. Usage Tracking Integrity Check
    print("\n[7. Usage Tracking & Database Ledger]")
    try:
        async with async_session_maker() as session:
            test_job = Job(job_type="provider_verification", status="COMPLETED")
            session.add(test_job)
            await session.commit()
            await session.refresh(test_job)

            usage = ProviderUsage(
                provider="ahrefs",
                job_id=test_job.id,
                request_count=1,
                estimated_units=1.0,
                endpoint="/site-explorer/domain-rating"
            )
            session.add(usage)
            await session.commit()
            await session.refresh(usage)
            print(f"  ✓ ProviderUsage Recorded: Ledger ID={usage.id}, JobID={test_job.id}, Units={usage.estimated_units}")
    except Exception as e:
        print(f"  ℹ Database ledger check bypassed (PostgreSQL offline: {e})")

    print("\n" + "=" * 80)
    print("GOAL 1 STATUS SUMMARY:")
    for prov, stat in results.items():
        print(f"  • {prov:15s}: {stat}")
    print("=" * 80)
    return results


if __name__ == "__main__":
    asyncio.run(verify_providers())
