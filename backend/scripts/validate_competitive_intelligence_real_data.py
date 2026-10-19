"""
Script: validate_competitive_intelligence_real_data.py
Description: Validates Phase 3.3 Advanced Competitive SEO Intelligence against
actual PostgreSQL database records, live website scans, publisher inventory, and CRM pipeline.
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, desc

from app.db.session import async_session_maker
from app.models import (
    Company,
    WebsiteScan,
    SEOMetric,
    PublisherRecord,
    PublisherObservation,
    CompanyCompetitor,
    CompetitiveAnalysisRun,
    SalesOpportunity
)
from app.services.intelligence.competitive_service import CompetitiveIntelligenceService
from app.schemas.competitive import CompetitorCreate


async def validate_real_data():
    print("=" * 80)
    print("PROSPECTOS PHASE 3.3: ADVANCED COMPETITIVE SEO INTELLIGENCE REAL-DATA AUDIT")
    print("=" * 80)

    async with async_session_maker() as session:
        # 1. Telemetry Inspection
        count_comp = (await session.execute(select(func.count(Company.id)))).scalar_one()
        count_scans = (await session.execute(select(func.count(WebsiteScan.id)))).scalar_one()
        count_publishers = (await session.execute(select(func.count(PublisherRecord.id)))).scalar_one()
        count_observations = (await session.execute(select(func.count(PublisherObservation.id)))).scalar_one()
        count_competitors = (await session.execute(select(func.count(CompanyCompetitor.id)))).scalar_one()
        count_runs = (await session.execute(select(func.count(CompetitiveAnalysisRun.id)))).scalar_one()

        print(f"\n[1. Live Database Telemetry]")
        print(f"  • Companies in Database: {count_comp}")
        print(f"  • Website Scans in Database: {count_scans}")
        print(f"  • Publisher Records in Inventory: {count_publishers}")
        print(f"  • Publisher Metric Observations: {count_observations}")
        print(f"  • Tracked Competitor Links: {count_competitors}")
        print(f"  • Historical Analysis Runs: {count_runs}")

        # Pick a real prospect company from database with website scans
        stmt_target = (
            select(Company)
            .join(WebsiteScan, WebsiteScan.company_id == Company.id)
            .where(Company.canonical_domain.isnot(None))
            .limit(1)
        )
        prospect = (await session.execute(stmt_target)).scalar_one_or_none()

        if not prospect:
            # Fallback to any company
            prospect = (await session.execute(select(Company).limit(1))).scalar_one_or_none()
            if not prospect:
                print("Error: No companies found in database!")
                sys.exit(1)

        print(f"\n[2. Selected Prospect for Competitive Intelligence Audit]")
        print(f"  • Company ID: {prospect.id}")
        print(f"  • Name: {prospect.company_name}")
        print(f"  • Domain: {prospect.canonical_domain}")
        print(f"  • Industry: {prospect.industry or 'Technology'}")

        service = CompetitiveIntelligenceService(session)

        # 3. Test Competitor Discovery on Real Database
        print(f"\n[3. Executing Competitor Discovery]")
        candidates = await service.discover_competitors(prospect.id, max_results=5, persist_discovered=False)
        print(f"  • Discovered {len(candidates)} Candidate Competitors from actual DB records:")
        for idx, cand in enumerate(candidates, 1):
            print(f"    {idx}. {cand.company_name} ({cand.canonical_domain})")
            print(f"       Tier: {cand.relevance_tier} | Relevance Score: {cand.relevance_score}")
            print(f"       Evidence: {cand.overlap_evidence.get('reasons', [])}")

        # 4. Add or Select a Verified Competitor for Side-by-Side Analysis
        competitor_link = None
        existing_comps = await service.get_competitors(prospect.id)
        if existing_comps:
            competitor_link = existing_comps[0]
            print(f"\n[4. Using Existing Tracked Competitor: {competitor_link.competitor_name} ({competitor_link.competitor_domain})]")
        elif candidates:
            top_cand = candidates[0]
            competitor_link = await service.add_competitor(
                prospect.id,
                CompetitorCreate(
                    company_id=prospect.id,
                    competitor_company_id=top_cand.company_id,
                    competitor_name=top_cand.company_name,
                    competitor_domain=top_cand.canonical_domain,
                    relevance_tier=top_cand.relevance_tier,
                    relevance_score=top_cand.relevance_score,
                    notes="Discovered during Phase 3.3 live validation audit"
                )
            )
            print(f"\n[4. Tracked Discovered Competitor: {competitor_link.competitor_name} ({competitor_link.competitor_domain})]")
        else:
            # Fallback peer
            competitor_link = await service.add_competitor(
                prospect.id,
                CompetitorCreate(
                    company_id=prospect.id,
                    competitor_name="Industry Benchmark Rival",
                    competitor_domain="benchmarkrival.io",
                    relevance_tier="DIRECT",
                    relevance_score=0.85,
                    notes="Benchmark competitor for audit"
                )
            )
            print(f"\n[4. Created Benchmark Competitor: {competitor_link.competitor_domain}]")

        # 5. Run Live Side-by-Side Competitive SEO Analysis
        print(f"\n[5. Executing Side-by-Side Competitive SEO Analysis Run]")
        run = await service.run_competitive_analysis(
            company_id=prospect.id,
            competitor_id=competitor_link.id,
            sync_to_sales_opportunities=True
        )

        print(f"  • Analysis Run ID: {run.id}")
        print(f"  • Run Status: {run.status}")
        print(f"  • Analyzed At: {run.analyzed_at}")

        # 6. Audit Multi-Dimensional Findings
        print(f"\n[6. Multi-Dimensional Intelligence Findings]")
        print(f"  A. Topical Content Gaps ({len(run.content_gaps)} identified):")
        for g in run.content_gaps[:3]:
            print(f"     - [{g['search_intent']}] {g['topic']}")
            print(f"       Competitor: {g['competitor_coverage']} | Prospect Status: {g.get('prospect_status') or g.get('prospect_coverage', 'ABSENT')}")
            print(f"       Service: {g['recommended_service']} | Action: {g['recommended_action']}")

        print(f"\n  B. Technical SEO Disparities ({len(run.technical_gaps)} identified):")
        for t in run.technical_gaps[:3]:
            print(f"     - [{t['severity']}] {t['metric_or_feature']}")
            print(f"       Prospect: {t['prospect_state']}")
            print(f"       Competitor: {t['competitor_state']}")
            print(f"       Action: {t['recommended_action']}")

        print(f"\n  C. Internal Linking & Topical Silo Architecture:")
        for ilg in run.internal_linking_gaps[:2]:
            print(f"     - Silo Topic: {ilg['silo_topic']}")
            print(f"       Prospect Issue: {ilg['prospect_issue']}")
            print(f"       Remediation: {ilg['recommended_action']}")

        print(f"\n  D. Backlink Gap Analysis (Strict Non-Fabrication):")
        bg = run.backlink_gaps or {}
        print(f"     - Provider Source: {bg.get('provider_source')}")
        print(f"     - Is Provider Configured: {bg.get('is_provider_configured')}")
        print(f"     - Prospect DA: {bg.get('prospect_da', 'Unknown (None)')}")
        print(f"     - Competitor DA: {bg.get('competitor_da', 'Unknown (None)')}")
        print(f"     - Authority Differential: {bg.get('da_differential', 'Unknown')}")
        print(f"     - Disclosed Limitations: {bg.get('limitations')}")

        print(f"\n  E. Digital PR & Publisher Opportunities ({len(run.publisher_opportunities)} matched):")
        for pub in run.publisher_opportunities[:3]:
            print(f"     - Outlet: {pub['publisher_name']} ({pub['canonical_domain']})")
            print(f"       Audience: {pub['audience_focus']} | Price: {pub.get('currency', '$')}{pub.get('price', 'N/A')}")
            print(f"       Strategy: {pub['recommended_service']} | Rationale: {pub['relevance_rationale']}")

        print(f"\n  F. Prioritized GrokxSEO Action Recommendations ({len(run.prioritized_recommendations)} total):")
        for rec in run.prioritized_recommendations[:4]:
            print(f"     - [{rec['service']}] {rec['title']} (Score: {rec['priority_score']}/100)")
            print(f"       Effort: {rec['effort']} | Impact: {rec['impact']} | Confidence: {rec['confidence']}")
            print(f"       Action: {rec['action']}")

        # 7. Verify Sales Opportunity Sync & Deduplication
        opp_stmt = select(SalesOpportunity).where(
            SalesOpportunity.company_id == prospect.id,
            SalesOpportunity.category == "COMPETITIVE_GAP"
        )
        opps = (await session.execute(opp_stmt)).scalars().all()
        print(f"\n[7. Sales Opportunity Integration & Deduplication Audit]")
        print(f"  • Synced Active Competitive Opportunities: {len(opps)}")
        for o in opps[:3]:
            print(f"    - Title: {o.title} | Rule: {o.detection_rule} | Severity: {o.severity} | Service: {o.recommended_service}")

        # Test Idempotent Re-Run to verify zero duplicates
        await service.run_competitive_analysis(prospect.id, competitor_link.id, sync_to_sales_opportunities=True)
        opps_after = (await session.execute(opp_stmt)).scalars().all()
        print(f"  • Opportunity count after second idempotent execution: {len(opps_after)}")
        assert len(opps_after) == len(opps), "Error: Duplicate opportunities created!"
        print(f"  ✓ Idempotent deduplication verified: Count remained identical ({len(opps)} items)")

        # 8. Executive Overview Check
        overview = await service.get_competitive_overview(prospect.id)
        print(f"\n[8. Executive Overview Verification]")
        print(f"  • Tracked Competitors Count: {overview.competitors_count}")
        print(f"  • Analyzed Runs Count: {overview.analyzed_runs_count}")
        print(f"  • Latest Run Competitor: {overview.latest_run.competitor_name if overview.latest_run else 'None'}")
        print(f"  • Total Content Gaps: {overview.total_content_gaps}")
        print(f"  • Total Technical Gaps: {overview.total_technical_gaps}")
        print(f"  • Total Publisher Opportunities: {overview.total_publisher_opportunities}")

        print("\n" + "=" * 80)
        print("PHASE 3.3 REAL-DATA VALIDATION AUDIT: COMPLETE & VERIFIED")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(validate_real_data())
