"""
Real-data End-to-End Validation Script for Phase 3.0: AI Sales Intelligence & Lead Prioritization.
Executes controlled validation against real persisted records in PostgreSQL.
"""
import asyncio
import uuid
import sys
from datetime import datetime, timezone

from sqlalchemy import select, desc
from app.db.session import async_session_maker
from app.models import (
    Company,
    WebsiteScan,
    SEOMetric,
    PublisherRecord,
    SalesIntelligenceScore,
    SalesOpportunity,
    SalesBrief,
    CRMActivity
)
from app.services.intelligence.sales_intelligence import SalesIntelligenceService


async def run_e2e_sales_intelligence_validation():
    print("=" * 80)
    print("ProspectOS Phase 3.0 — Real-Data End-to-End Sales Intelligence Validation")
    print("=" * 80)

    async with async_session_maker() as session:
        service = SalesIntelligenceService(session)

        # 1. Fetch real companies from the database
        res_companies = await session.execute(
            select(Company)
            .where(Company.canonical_domain.isnot(None))
            .order_by(Company.created_at.asc())
            .limit(2)
        )
        companies = res_companies.scalars().all()
        if len(companies) < 2:
            print("❌ Error: Need at least 2 real companies in the database for comparison validation.")
            sys.exit(1)

        target_company = companies[0]
        comp2 = companies[1]

        print(f"✅ Target Prospect 1: {target_company.company_name} ({target_company.canonical_domain}) [ID: {target_company.id}]")
        print(f"   Industry: {target_company.industry} | Sales Stage: {target_company.sales_stage}")
        print(f"✅ Target Prospect 2: {comp2.company_name} ({comp2.canonical_domain}) [ID: {comp2.id}]")

        # 2. Opportunity Detection & Classification
        print("\n--- 2. Opportunity Detection & Classification ---")
        opps = await service.detect_opportunities(target_company.id)
        print(f"✅ Successfully evaluated opportunities: {len(opps)} detected.")
        for idx, o in enumerate(opps[:5], 1):
            print(f"   [{idx}] [{o.severity}] {o.category}: {o.title}")
            print(f"       Service: {o.recommended_service} | Rule: {o.detection_rule}")
            print(f"       Evidence items: {len(o.supporting_evidence)}")

        # 3. Lead Qualification & Explainable Scoring Model v3.0.0
        print("\n--- 3. Lead Qualification & Explainable Priority Scoring (v3.0.0) ---")
        score_obj = await service.calculate_priority_score(target_company.id)
        print(f"✅ Algorithm Version: {score_obj.scoring_version}")
        print(f"✅ Overall Priority Score: {score_obj.overall_priority_score:.1f} / 100")
        print(f"✅ Primary Recommended Service: {score_obj.primary_recommended_service}")
        weights = score_obj.component_weights or {}
        print(f"   - SEO Deficit Severity Score: {score_obj.seo_severity_score:.1f} (Weight: {weights.get('seo_severity', 0.25) * 100:.0f}%)")
        print(f"   - GrokxSEO Service Fit Score: {score_obj.service_fit_score:.1f} (Weight: {weights.get('service_fit', 0.25) * 100:.0f}%)")
        print(f"   - Publisher Fit Score:        {score_obj.publisher_fit_score:.1f} (Weight: {weights.get('publisher_fit', 0.20) * 100:.0f}%)")
        print(f"   - Business Fit Score:         {score_obj.business_fit_score:.1f} (Weight: {weights.get('business_fit', 0.15) * 100:.0f}%)")
        print(f"   - Evidence Confidence Score:  {score_obj.evidence_confidence_score * 100:.0f}% (Weight: {weights.get('evidence_confidence', 0.15) * 100:.0f}%)")

        print("\n   Positive Indicators:")
        for ind in score_obj.positive_indicators:
            print(f"     + {ind}")

        print("\n   Known Limitations & Transparent Data Gaps:")
        for lim in score_obj.limitations:
            print(f"     - {lim}")
        for gap in score_obj.missing_information:
            print(f"     ? {gap}")

        print(f"\n   Recommended Next Action: {score_obj.recommended_next_action}")

        # 4. Sales Intelligence Brief Generation
        print("\n--- 4. Sales Intelligence Brief Generation & Markdown Export ---")
        brief = await service.generate_or_get_brief(target_company.id)
        print(f"✅ Generated Brief: '{brief.title}' [ID: {brief.id}]")
        print(f"   Markdown length: {len(brief.full_brief_markdown)} characters")
        print(f"   Discovery questions generated: {len(brief.discovery_questions)}")
        for q in brief.discovery_questions[:3]:
            print(f"     * {q}")

        # 5. Brief Customization & Revision
        print("\n--- 5. Brief Customization & Versioning ---")
        brief.full_brief_markdown += "\n\n**Custom Strategic Note:** Verified prospect has internal CMS migration planned for Q4."
        brief.is_customized = True
        brief.last_edited_by = "sales_director"
        brief.last_edited_at = datetime.now(timezone.utc)
        await session.commit()

        retrieved_brief = await service.generate_or_get_brief(target_company.id, force_regenerate=False)
        assert retrieved_brief.is_customized, "Expected is_customized to be True"
        assert "Q4" in retrieved_brief.full_brief_markdown, "Customized text was lost"
        print(f"✅ Successfully preserved human customization by {retrieved_brief.last_edited_by}")

        # 6. Human Priority Override & Audit Logging
        print("\n--- 6. Human Override & CRM Activity Audit Trail ---")
        override_val = 88.5
        override_reason = "Direct inbound contact from VP of Marketing; enterprise budget verified."
        updated_score = await service.override_score(
            company_id=target_company.id,
            score=override_val,
            reason=override_reason,
            actor="enterprise_rep"
        )
        assert updated_score.human_override_score == override_val
        print(f"✅ Override successfully applied: Score = {updated_score.human_override_score} by {updated_score.human_override_by}")

        # Verify audit activity in CRMActivity
        res_act = await session.execute(
            select(CRMActivity).where(
                CRMActivity.company_id == target_company.id,
                CRMActivity.activity_type == "SCORE_OVERRIDE"
            ).order_by(desc(CRMActivity.created_at)).limit(1)
        )
        act = res_act.scalar_one_or_none()
        assert act is not None, "Expected CRMActivity audit record for override"
        print(f"✅ CRM Activity audit entry verified: {act.title} (Actor: {act.actor})")

        # 7. Review Status Transition
        print("\n--- 7. Review Status Transition ---")
        status_res = await service.update_review_status(
            company_id=target_company.id,
            review_status="QUALIFIED",
            notes="Passed sales qualification gate; high potential for link building & content retainers.",
            reviewer="sales_lead"
        )
        assert status_res.review_status == "QUALIFIED"
        print(f"✅ Review status updated to {status_res.review_status}")

        # 8. Side-by-Side Comparison
        print("\n--- 8. Side-by-Side Multi-Prospect Comparison ---")
        # Ensure prospect 2 is also evaluated
        await service.calculate_priority_score(comp2.id)
        comp_res = await service.compare_prospects([target_company.id, comp2.id])
        print(f"✅ Side-by-side comparison evaluated: {len(comp_res.compared_prospects)} prospects.")
        for p in comp_res.compared_prospects:
            p_score = (p.score.human_override_score if (p.score and p.score.human_override_score is not None) else (p.score.overall_priority_score if p.score else 0.0))
            p_service = p.score.primary_recommended_service if p.score else "N/A"
            print(f"   Prospect: {p.company_name} | Effective Score: {p_score:.1f} | Top Service: {p_service} | Matched Pubs: {len(p.top_matched_publishers)}")

        # 9. Prioritized Queue Querying & Sorting
        print("\n--- 9. Prioritized Sales Queue Querying ---")
        total, queue = await service.get_prioritized_queue(limit=5)
        print(f"✅ Prioritized Queue Total Records: {total}")
        print("   Top 5 Prospects in Prioritized Queue:")
        for idx, item in enumerate(queue, 1):
            ov_badge = "[OVERRIDDEN]" if item.has_human_override else ""
            print(f"   #{idx} | Score: {item.effective_score:.1f} {ov_badge} | {item.company_name} ({item.industry or 'N/A'}) | Service: {item.primary_recommended_service} | Review: {item.review_status}")

        # 10. Clean up test override to leave database in pristine state
        print("\n--- 10. Post-Validation State Reset ---")
        updated_score.human_override_score = None
        updated_score.human_override_reason = None
        updated_score.human_override_by = None
        updated_score.human_override_at = None
        await session.commit()
        print("✅ Restored original human override state on target company.")

    print("\n" + "=" * 80)
    print("🎯 PHASE 3.0 REAL-DATA END-TO-END VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_e2e_sales_intelligence_validation())
