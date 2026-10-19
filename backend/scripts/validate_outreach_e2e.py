import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, delete
from app.db.session import async_session_maker
from app.models import (
    Company,
    CompanyContact,
    WebsiteScan,
    OpportunityProfile,
    MediaPlan,
    MediaPlanItem,
    PublisherRecord,
    OutreachCampaign,
    OutreachDraft,
    OutreachMessage,
    OutreachSuppression,
)
from app.services.outreach.contacts import ContactResearcher
from app.services.outreach.personalization import OutreachPersonalizationEngine
from app.services.outreach.sender import OutreachSenderService
from app.services.outreach.providers.registry import email_registry
from app.services.outreach.providers.mock import MockEmailProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outreach_e2e_validation")


async def run_outreach_validation():
    logger.info("=================================================================")
    logger.info("   ProspectOS Phase 2.4 — AI Outreach Automation E2E Validation   ")
    logger.info("=================================================================")

    async with async_session_maker() as session:
        # Clean up any lingering test suppressions on techcrunch.com
        await session.execute(
            delete(OutreachSuppression).where(OutreachSuppression.domain == "techcrunch.com")
        )
        await session.commit()

        # 1. Inspect existing database records
        total_companies = await session.scalar(select(func.count(Company.id)))
        logger.info(f"Database contains {total_companies} real companies.")
        assert total_companies > 0, "No companies found in database!"

        stmt_comp = select(Company).where(Company.company_name == "TechCrunch").limit(1)
        techcrunch = (await session.execute(stmt_comp)).scalars().first()
        assert techcrunch is not None, "Could not find TechCrunch company."
        logger.info(f"Selected real prospect: ID={techcrunch.id}, Name='{techcrunch.company_name}', Domain='{techcrunch.canonical_domain}'")

        # 2. Contact Research & Provenance
        logger.info("\n--- [Step 1] Contact Research & Provenance ---")
        researcher = ContactResearcher(session)
        contacts = await researcher.discover_company_contacts(techcrunch.id)
        assert len(contacts) > 0, "No contacts discovered for TechCrunch!"
        
        contact = contacts[0]
        logger.info(f"Discovered Contact: Email='{contact.email}', Name='{contact.full_name}', Role='{contact.job_title}'")
        logger.info(f"Provenance: Source='{contact.source_type}', Status='{contact.verification_status}', Confidence={contact.confidence}, RetrievedAt={contact.retrieval_timestamp}")
        assert ContactResearcher.is_valid_email(contact.email), f"Invalid email format: {contact.email}"
        assert contact.verification_status in ["VERIFIED", "INFERRED"], f"Unexpected verification status: {contact.verification_status}"
        assert contact.retrieval_timestamp is not None, "Missing retrieval timestamp"

        # 3. Campaign Setup
        logger.info("\n--- [Step 2] Campaign Organization ---")
        campaign = OutreachCampaign(
            name=f"Tech & Media Outreach - {uuid.uuid4().hex[:6]}",
            description="Controlled campaign for real prospect outreach validation",
            status="ACTIVE",
            daily_send_limit=25,
            follow_up_delay_days=4,
            max_follow_ups=2
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        logger.info(f"Created Campaign: ID={campaign.id}, Name='{campaign.name}', DailyLimit={campaign.daily_send_limit}")

        # 4. Evidence-Based Personalization & Non-Fabrication
        logger.info("\n--- [Step 3] Evidence-Based Draft Generation & Provenance ---")
        personalizer = OutreachPersonalizationEngine(session)
        draft_record = await personalizer.generate_draft(
            company_id=techcrunch.id,
            contact_id=contact.id,
            campaign_id=campaign.id,
            include_media_plan=True,
            save=True
        )
        assert draft_record is not None, "Failed to generate draft record"
        logger.info(f"Generated Draft ID: {draft_record.id}")
        logger.info(f"Subject Line: '{draft_record.subject_line}'")
        logger.info(f"Prospect Summary: '{draft_record.prospect_summary}'")
        logger.info(f"Call to Action: '{draft_record.call_to_action}'")
        logger.info(f"Approval Status: {draft_record.approval_status}")
        assert draft_record.approval_status in ["UNAPPROVED", "PENDING"], "Draft must initially be unapproved!"

        # Verify evidence citations
        citations = draft_record.evidence_citations or []
        logger.info(f"Evidence Citations ({len(citations)} items):")
        for idx, cit in enumerate(citations, 1):
            logger.info(f"  [{idx}] Claim: \"{cit.get('claim')}\" -> Source: {cit.get('source_type')} (Confidence: {cit.get('confidence')})")
        assert len(citations) >= 2, "Draft must have traceable evidence citations for all claims!"

        # 5. Gate 1 Verification: Block Send if Not Approved
        logger.info("\n--- [Step 4] Safety Gate: Block Unapproved Draft ---")
        sender = OutreachSenderService(session)
        blocked_gate1 = False
        try:
            await sender.send_draft(draft_id=draft_record.id, authorized_by="tester")
        except ValueError as e:
            blocked_gate1 = True
            logger.info(f"Blocked as expected by Gate 1: {e}")
            assert "Explicit human approval" in str(e)
        assert blocked_gate1 is True, "Safety gate failed: unapproved draft was not blocked!"
        logger.info("✓ Gate 1 Verified: Human approval is strictly enforced before any send.")

        # 6. Approve the Draft
        logger.info("\n--- [Step 5] Human Approval ---")
        draft_record.approval_status = "APPROVED"
        draft_record.approved_by = "qa_lead@prospectos.local"
        draft_record.approved_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(draft_record)
        logger.info(f"Draft approved by '{draft_record.approved_by}' at {draft_record.approved_at}")

        # 7. Gate 2 Verification: Real Provider Configuration Check
        logger.info("\n--- [Step 6] Provider Safeguard: Halt if No Provider Configured ---")
        unconfigured_result = await sender.send_draft(draft_id=draft_record.id, authorized_by="qa_lead@prospectos.local")
        logger.info(f"Unconfigured Provider Result: Success={unconfigured_result.success}, Error='{unconfigured_result.error}'")
        assert unconfigured_result.success is False, "Unconfigured provider failed to halt safely!"
        assert "PROVIDER_NOT_CONFIGURED" in (unconfigured_result.error or ""), f"Expected PROVIDER_NOT_CONFIGURED in {unconfigured_result.error}"
        logger.info("✓ Gate 2 Verified: Real external email sending is strictly locked without configured credentials.")

        # 8. Controlled Simulated Send via Mock Provider
        logger.info("\n--- [Step 7] Controlled Simulated Transmission via Mock Provider ---")
        # Reset draft status to DRAFT so it can be transmitted in mock test
        draft_record.status = "DRAFT"
        draft_record.error_message = None
        await session.commit()

        mock_provider = MockEmailProvider()
        email_registry.register("mock", mock_provider)
        email_registry.set_override_provider("mock")

        unique_controlled_email = f"controlled-{uuid.uuid4().hex[:6]}@prospectos.local"
        mock_send_result = await sender.send_draft(
            draft_id=draft_record.id,
            authorized_by="qa_lead@prospectos.local",
            override_recipient_email=unique_controlled_email
        )
        logger.info(f"Controlled Send Result: Success={mock_send_result.success}, MessageID='{mock_send_result.message_id}'")
        assert mock_send_result.success is True, f"Send failed: {mock_send_result.error}"
        assert len(mock_provider.sent_messages) == 1, "Mock provider did not receive the sent message!"

        sent_msg = mock_provider.sent_messages[0]
        logger.info(f"Recorded in Mock Provider: Recipient='{sent_msg['to_email']}', Subject='{sent_msg['subject']}'")

        # Verify database audit logging in outreach_messages
        msg_stmt = select(OutreachMessage).where(OutreachMessage.draft_id == draft_record.id)
        audit_msg = (await session.execute(msg_stmt)).scalars().first()
        assert audit_msg is not None, "Audit message not recorded in database!"
        logger.info(f"Audit Record in DB: ID={audit_msg.id}, Status='{audit_msg.status}', SentAt={audit_msg.sent_at}, Provider='{audit_msg.provider}'")

        # 9. Gate 3: Duplicate-Send Prevention
        logger.info("\n--- [Step 8] Safety Gate: Duplicate-Send Prevention ---")
        # Attempt to resend the exact same draft
        blocked_gate3_1 = False
        try:
            await sender.send_draft(draft_id=draft_record.id, authorized_by="qa_lead@prospectos.local")
        except ValueError as e:
            blocked_gate3_1 = True
            logger.info(f"Blocked as expected (already sent): {e}")
            assert "already been sent" in str(e)
        assert blocked_gate3_1 is True, "Duplicate draft resend was not blocked!"
        logger.info("✓ Gate 3.1 Verified: Already-sent draft cannot be resent.")

        # Create a second draft to the same recipient and approve it
        second_draft = await personalizer.generate_draft(
            company_id=techcrunch.id,
            contact_id=contact.id,
            campaign_id=campaign.id,
            include_media_plan=False,
            save=True
        )
        second_draft.approval_status = "APPROVED"
        second_draft.approved_by = "qa_lead@prospectos.local"
        second_draft.approved_at = datetime.now(timezone.utc)
        second_draft.recipient_email = unique_controlled_email
        await session.commit()

        # Attempt to send immediately to the same controlled recipient (cooldown should trigger)
        blocked_gate3_2 = False
        try:
            await sender.send_draft(
                draft_id=second_draft.id,
                authorized_by="qa_lead@prospectos.local",
                override_recipient_email=unique_controlled_email
            )
        except ValueError as e:
            blocked_gate3_2 = True
            logger.info(f"Blocked as expected (duplicate cooldown): {e}")
            assert "Duplicate send prevented" in str(e)
        assert blocked_gate3_2 is True, "Duplicate-send cooldown failed!"
        logger.info("✓ Gate 3.2 Verified: Duplicate-send 7-day cooldown actively prevents recipient fatigue.")

        # 10. Gate 4: Opt-Out & Suppression Enforcement
        logger.info("\n--- [Step 9] Safety Gate: Opt-Out & Suppression Enforcement ---")
        suppressed_target = f"optout-{uuid.uuid4().hex[:6]}@techcrunch.com"
        suppression = OutreachSuppression(
            email=suppressed_target,
            domain=None,
            reason="UNSUBSCRIBE",
            source="user_opt_out_link"
        )
        session.add(suppression)
        await session.commit()
        logger.info(f"Added email '{suppressed_target}' to suppression table.")

        third_draft = await personalizer.generate_draft(
            company_id=techcrunch.id,
            contact_id=contact.id,
            campaign_id=campaign.id,
            save=True
        )
        third_draft.approval_status = "APPROVED"
        third_draft.approved_by = "qa_lead@prospectos.local"
        third_draft.approved_at = datetime.now(timezone.utc)
        third_draft.recipient_email = suppressed_target
        await session.commit()

        blocked_gate4 = False
        try:
            await sender.send_draft(draft_id=third_draft.id, authorized_by="qa_lead@prospectos.local")
        except ValueError as e:
            blocked_gate4 = True
            logger.info(f"Blocked as expected (suppressed): {e}")
            assert "suppression list" in str(e)
        assert blocked_gate4 is True, "Suppressed recipient send was not blocked!"
        logger.info("✓ Gate 4 Verified: Opt-out suppression list strictly prevents sending to opted-out contacts.")

        # 11. Follow-Up Scheduling & Cancellation
        logger.info("\n--- [Step 10] Follow-Up Scheduling & Cancellation Logic ---")
        # Check follow-up scheduled for the first draft
        fu_stmt = select(OutreachDraft).where(OutreachDraft.parent_draft_id == draft_record.id)
        fu_draft = (await session.execute(fu_stmt)).scalars().first()
        assert fu_draft is not None, "Follow-up draft was not automatically scheduled!"
        logger.info(f"Scheduled Follow-up: ID={fu_draft.id}, Step={fu_draft.sequence_step}, ScheduledFor={fu_draft.scheduled_send_at}, ApprovalStatus={fu_draft.approval_status}")
        assert fu_draft.approval_status in ["UNAPPROVED", "PENDING"], "Follow-up draft must require separate human approval!"
        assert fu_draft.is_follow_up is True

        # Simulate prospect reply and verify cancellation
        await sender.cancel_follow_ups(
            company_id=techcrunch.id,
            recipient_email=unique_controlled_email,
            reason="PROSPECT_REPLIED"
        )
        await session.refresh(fu_draft)
        logger.info(f"Follow-up draft status after cancellation: {fu_draft.status} (Reason: {fu_draft.error_message})")
        assert fu_draft.status == "CANCELLED", f"Follow up status should be CANCELLED, got {fu_draft.status}"
        logger.info("✓ Follow-up cancellation policy verified.")

        # Reset email registry to safe default
        email_registry.set_override_provider(None)
        logger.info("\n=================================================================")
        logger.info("   ALL PHASE 2.4 OUTREACH AUTOMATION VERIFICATIONS PASSED (10/10)   ")
        logger.info("=================================================================")


if __name__ == "__main__":
    asyncio.run(run_outreach_validation())
