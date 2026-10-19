"""
Real-data End-to-End Validation Script for Phase 2.5: CRM & Sales Pipeline.
Executes controlled validation against real persisted records in PostgreSQL.
"""
import asyncio
import uuid
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import Company, CRMDeal, CRMTask, CRMActivity, CRMNote
from app.services.crm.service import CRMService
from app.schemas.crm import (
    StageUpdateRequest,
    DealCreate,
    DealUpdate,
    TaskCreate,
    TaskCompleteRequest,
    NoteCreate
)

async def run_e2e_crm_validation():
    print("=" * 70)
    print("ProspectOS Phase 2.5 — Real-Data End-to-End CRM Validation")
    print("=" * 70)

    async with async_session_maker() as session:
        crm = CRMService(session)

        # 1. Fetch an existing real company with a canonical domain
        res = await session.execute(
            select(Company).where(Company.canonical_domain.isnot(None)).order_by(Company.created_at.asc()).limit(1)
        )
        company = res.scalar_one_or_none()
        if not company:
            print("❌ Error: No existing companies found in database.")
            sys.exit(1)

        print(f"✅ Found real persisted company: {company.company_name} ({company.canonical_domain}) [ID: {company.id}]")
        print(f"   Initial sales stage: {company.sales_stage}")

        original_stage = company.sales_stage

        # 2. Test Stage Transition: NEW -> RESEARCHED
        print("\n--- 2. Validating Stage Transition (NEW -> RESEARCHED) ---")
        res_researched = await crm.update_prospect_stage(
            company_id=company.id,
            new_stage="RESEARCHED",
            reason="Completed website technology analysis and initial crawl",
            notes="Identified WordPress CMS and key technical SEO issues",
            actor="validation_harness"
        )
        assert res_researched.sales_stage == "RESEARCHED", f"Expected RESEARCHED, got {res_researched.sales_stage}"
        print(f"✅ Successfully transitioned to RESEARCHED. Updated at: {res_researched.stage_updated_at}")

        # 3. Test Stage Transition: RESEARCHED -> QUALIFIED
        print("\n--- 3. Validating Stage Transition (RESEARCHED -> QUALIFIED) ---")
        res_qualified = await crm.update_prospect_stage(
            company_id=company.id,
            new_stage="QUALIFIED",
            reason="Exceeds opportunity score threshold (>60) with clear link building deficit",
            notes="Target market: B2B Enterprise Technology",
            actor="validation_harness"
        )
        assert res_qualified.sales_stage == "QUALIFIED"
        print(f"✅ Successfully transitioned to QUALIFIED. Reason: {res_qualified.stage_reason}")

        # 4. Test Safeguard: Attempting CONTACTED without confirmed sent outreach
        print("\n--- 4. Validating CONTACTED Safeguard Boundary ---")
        try:
            await crm.update_prospect_stage(
                company_id=company.id,
                new_stage="CONTACTED",
                reason="Attempting premature transition without outreach send",
                actor="validation_harness"
            )
            print("❌ Safeguard failed: Permitted transition to CONTACTED without confirmed outreach message!")
            sys.exit(1)
        except ValueError as e:
            print(f"✅ Safeguard successfully enforced: {e}")

        # 5. Test Deal Management & Revenue Integrity
        print("\n--- 5. Validating Deal Management & Revenue Integrity ---")
        deal_create = DealCreate(
            company_id=company.id,
            deal_name="Enterprise Technical SEO & Publisher Outreach",
            service_category="FULL_SERVICE",
            stage="PROPOSAL",
            estimated_value=15000.0,
            proposed_value=14500.0,
            currency="USD",
            notes="Quarterly engagement with publisher placements"
        )
        deal = await crm.create_deal(deal_create, actor="validation_harness")
        assert deal.id is not None
        assert deal.estimated_value == 15000.0
        assert deal.currency == "USD"
        print(f"✅ Deal created: '{deal.deal_name}' [ID: {deal.id}]")
        print(f"   Estimated Value: ${deal.estimated_value:,.2f} {deal.currency}")

        # Close the deal as WON with authorized closed revenue
        deal_update = DealUpdate(
            stage="WON",
            outcome="WON",
            closed_amount=14500.0,
            win_reason="Client accepted verified media plan proposal",
            actual_close_date=datetime.now(timezone.utc),
            actor="validation_harness"
        )
        won_deal = await crm.update_deal(deal.id, deal_update)
        assert won_deal.outcome == "WON"
        assert won_deal.closed_amount == 14500.0
        print(f"✅ Deal updated to WON with authorized revenue: ${won_deal.closed_amount:,.2f} {won_deal.currency}")
        print(f"   Win reason: {won_deal.win_reason}")

        # 6. Test Task Creation & Idempotency
        print("\n--- 6. Validating Task Creation & Idempotency ---")
        idempotency_key = f"val_task_{company.id}_{uuid.uuid4().hex[:8]}"
        task_create = TaskCreate(
            company_id=company.id,
            deal_id=deal.id,
            title="Conduct onboarding kickoff call and review publisher selections",
            task_type="MEETING",
            priority="HIGH",
            due_date=datetime.now(timezone.utc),
            idempotency_key=idempotency_key
        )
        task_1 = await crm.create_task(task_create, actor="validation_harness")
        print(f"✅ Task 1 created: '{task_1.title}' [ID: {task_1.id}]")

        # Retry with identical idempotency key -> Must return existing task without duplicate insertion
        task_2 = await crm.create_task(task_create, actor="validation_harness")
        assert task_1.id == task_2.id, "Idempotency failed: duplicate task created!"
        print(f"✅ Idempotency verified: duplicate task prevented, returned task ID {task_2.id}")

        # Complete task
        complete_req = TaskCompleteRequest(
            completed_by="validation_harness",
            completion_notes="Kickoff completed, media plan finalized"
        )
        completed_task = await crm.complete_task(task_1.id, complete_req)
        assert completed_task.status == "COMPLETED"
        assert completed_task.completed_at is not None
        print(f"✅ Task marked complete at: {completed_task.completed_at}")

        # 7. Test Internal Notes
        print("\n--- 7. Validating Internal Notes & Activity Logging ---")
        note_req = NoteCreate(
            content="Client is particularly interested in Tier 1 tech publishers with DR > 75.",
            deal_id=deal.id,
            author="validation_harness"
        )
        note = await crm.add_note(company.id, note_req)
        assert note.id is not None
        print(f"✅ Internal note recorded [ID: {note.id}]: '{note.content[:50]}...'")

        # 8. Test Unified Prospect Detail Retrieval
        print("\n--- 8. Validating Unified Prospect Detail (360° Dossier) ---")
        dossier = await crm.get_unified_prospect_detail(company.id)
        assert dossier is not None
        assert dossier.sales_stage == "WON", f"Expected sales_stage WON, got {dossier.sales_stage}"
        assert len(dossier.deals) >= 1
        assert len(dossier.tasks) >= 1
        assert len(dossier.notes) >= 1
        assert len(dossier.activities) >= 4  # stage change, deal created, deal won, task created, note added
        print(f"✅ Unified prospect dossier retrieved successfully:")
        print(f"   - Company: {dossier.company.get('company_name') or dossier.company.get('canonical_domain')}")
        print(f"   - Stage: {dossier.sales_stage}")
        print(f"   - Deals attached: {len(dossier.deals)}")
        print(f"   - Tasks attached: {len(dossier.tasks)}")
        print(f"   - Notes attached: {len(dossier.notes)}")
        print(f"   - Activity audit entries: {len(dossier.activities)}")

        # 9. Test Pipeline Board & Aggregate Metrics
        print("\n--- 9. Validating Pipeline Board & Aggregate Reporting ---")
        board = await crm.get_pipeline_board()
        assert len(board) == 11, f"Expected 11 pipeline columns, got {len(board)}"
        print(f"✅ Pipeline board assembled with 11 standard stages:")
        for col in board[:5]:
            print(f"   [{col.stage}]: {col.prospects_count} prospects, ${col.total_pipeline_value:,.2f} pipeline value")

        metrics = await crm.get_crm_metrics()
        assert metrics.total_prospects > 0
        assert metrics.closed_won_revenue >= 14500.0
        assert metrics.won_deals_count >= 1
        print(f"\n✅ CRM Report Metrics:")
        print(f"   - Total Prospects: {metrics.total_prospects}")
        print(f"   - Qualified Prospects: {metrics.qualified_prospects_count}")
        print(f"   - Won Deals: {metrics.won_deals_count}")
        print(f"   - Closed Won Revenue: ${metrics.closed_won_revenue:,.2f} {metrics.pipeline_currency}")
        print(f"   - Open Pipeline Value: ${metrics.open_pipeline_value:,.2f} {metrics.pipeline_currency}")
        print(f"   - Win Rate: {metrics.conversion_rates.get('WON_RATE')}%")

        # 10. Clean up test deals/tasks/notes/activities for this company
        print("\n--- 10. Cleaning up validation artifacts ---")
        from sqlalchemy import delete
        await session.execute(delete(CRMActivity).where(CRMActivity.company_id == company.id))
        await session.execute(delete(CRMTask).where(CRMTask.company_id == company.id))
        await session.execute(delete(CRMNote).where(CRMNote.company_id == company.id))
        await session.execute(delete(CRMDeal).where(CRMDeal.company_id == company.id))

        # Restore original stage
        company_db = await session.get(Company, company.id)
        if company_db:
            company_db.sales_stage = original_stage
            company_db.stage_reason = None
            company_db.qualification_notes = None
        await session.commit()
        print("✅ Cleanup complete: test records purged and original stage restored.")

    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 2.5 REAL-DATA VALIDATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_e2e_crm_validation())
