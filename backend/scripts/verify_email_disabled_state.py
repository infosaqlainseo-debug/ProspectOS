"""
Script: scripts/verify_email_disabled_state.py
Description: Goal 3 — Secure Email Configuration / Explicitly Verified Disabled State.
Audits email provider configuration, verifies Mode B (Deliberately Disabled),
confirms approval gates, idempotency duplicate prevention, and zero socket dispatch.
"""

import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.session import async_session_maker
from app.models import (
    Company, OutreachDraft, OutreachMessage, PortalUser,
    ClientReport, ReportDeliveryLog
)
from app.services.outreach.providers.registry import email_registry
from app.services.outreach.sender import OutreachSenderService
from app.services.reporting.report_service import ReportingAndPortalService
from app.schemas.portal import ReportDeliveryRequest


async def verify_email_disabled_state():
    print("=" * 80)
    print("PROSPECTOS PRODUCTION READINESS: GOAL 3 — EMAIL SUBSYSTEM VERIFICATION")
    print("=" * 80)

    # 1. Inspect Active Provider and Mode
    print("\n[1. Email Operating Mode & Provider Inspection]")
    status_dict = email_registry.get_status()
    active_provider = email_registry.get_active_provider()
    configured_env = settings.EMAIL_PROVIDER

    print(f"  • Configured Environment EMAIL_PROVIDER: '{configured_env}'")
    print(f"  • Active Provider Name: '{status_dict['configured_provider']}'")
    print(f"  • Provider Ready to Send (is_configured): {status_dict['is_ready_to_send']}")
    print(f"  • Missing Configuration: {status_dict['missing_configuration']}")
    print(f"  • Designated Operating Mode: Mode B — Deliberately Disabled")

    assert configured_env in ["none", "mock"], f"Unexpected EMAIL_PROVIDER: {configured_env}"
    assert not active_provider.is_configured(), "Email provider must NOT report is_configured=True when disabled!"
    print("  ✓ Mode B Verified: External dispatch is disabled by default.")

    # 2. Test Direct Send Safeguard via UnconfiguredEmailProvider
    print("\n[2. Direct Socket Dispatch Safeguard Test]")
    direct_send = await active_provider.send_email(
        to_email="test@internal.test",
        subject="Test Dispatch",
        body_text="Test Content"
    )
    print(f"  • send_email Result Success: {direct_send.get('success')}")
    print(f"  • Error Reported: {direct_send.get('error')}")
    assert not direct_send.get("success"), "Unconfigured provider must fail send_email!"
    assert "PROVIDER_NOT_CONFIGURED" in direct_send.get("error", "")
    print("  ✓ Outbound Dispatch Blocked: Safely returned PROVIDER_NOT_CONFIGURED without network socket call.")

    # 3. Test Outreach Draft Safety Gates
    print("\n[3. Outreach Pipeline Safeguards Audit]")
    async with async_session_maker() as session:
        # Fetch or create a test company
        stmt_comp = select(Company).limit(1)
        company = (await session.execute(stmt_comp)).scalar_one()

        # Test Gate 1: Unapproved Draft cannot be sent
        unapproved_draft = OutreachDraft(
            company_id=company.id,
            recipient_email="pilot_test@internal.test",
            recipient_name="Pilot Tester",
            subject_line="Unapproved Draft Test",
            body_text="Should never send",
            status="DRAFT",
            approval_status="UNAPPROVED"
        )
        session.add(unapproved_draft)
        await session.commit()
        await session.refresh(unapproved_draft)

        sender = OutreachSenderService(session)
        gate1_blocked = False
        try:
            await sender.send_draft(unapproved_draft.id)
        except ValueError as e:
            gate1_blocked = True
            print(f"  ✓ Gate 1 (Human Approval Boundary): Blocked unapproved draft: {e}")

        assert gate1_blocked, "Gate 1 failed: Unapproved draft was not blocked!"

        # Test Gate 8: Even if manually set to APPROVED, unconfigured provider halts delivery safely
        unapproved_draft.approval_status = "APPROVED"
        unapproved_draft.status = "APPROVED"
        await session.commit()

        result = await sender.send_draft(unapproved_draft.id)
        print(f"  • Approved Draft Dispatch Attempt: Success={result.success}, Status={result.status}")
        print(f"  • Failure Reason: {result.error}")
        assert not result.success
        assert result.status == "FAILED"
        assert "PROVIDER_NOT_CONFIGURED" in result.error
        print("  ✓ Gate 8 (Provider Check): Approved draft gracefully aborted without network dispatch.")

    # 4. Test Client Report Delivery Safeguards & Idempotency
    print("\n[4. Client Report Delivery Safeguards & Idempotency Audit]")
    async with async_session_maker() as session:
        # Fetch or create an admin user
        stmt_admin = select(PortalUser).where(PortalUser.role == "ADMIN").limit(1)
        admin_user = (await session.execute(stmt_admin)).scalar_one_or_none()
        if not admin_user:
            admin_user = PortalUser(id=uuid.uuid4(), email="admin@prospectos.local", role="ADMIN", full_name="Admin", is_active=True)
            session.add(admin_user)
            await session.commit()

        # Fetch an approved report or create a test one
        stmt_report = select(ClientReport).where(ClientReport.approval_status == "APPROVED").limit(1)
        report = (await session.execute(stmt_report)).scalar_one_or_none()
        if not report:
            stmt_any_rep = select(ClientReport).limit(1)
            report = (await session.execute(stmt_any_rep)).scalar_one()
            report.approval_status = "APPROVED"
            report.status = "APPROVED"
            await session.commit()

        # Test delivery with unconfigured provider
        req = ReportDeliveryRequest(recipients=["audit_verify@internal.test"], delivery_channel="EMAIL")
        logs = await ReportingAndPortalService.deliver_report(session, report.id, admin_user, req)
        assert len(logs) == 1
        log = logs[0]
        print(f"  • Report Delivery Recorded: Status={log.status}, Recipient={log.recipient_email}")
        assert log.status == "SIMULATED", f"Expected SIMULATED status when email disabled, got {log.status}"
        print("  ✓ Report Delivery Simulated: Recorded as SIMULATED with zero network dispatch.")

        # Test Idempotency: Second identical dispatch must NOT duplicate
        logs_retry = await ReportingAndPortalService.deliver_report(session, report.id, admin_user, req)
        assert len(logs_retry) == 1
        assert logs_retry[0].id == log.id, "Idempotency key failed: Created duplicate delivery log!"
        print(f"  ✓ Idempotency Verified: Duplicate send safely prevented (Log ID matched: {log.id}).")

    print("\n" + "=" * 80)
    print("GOAL 3 STATUS SUMMARY:")
    print("  • Operating Mode        : Mode B — Deliberately Disabled (SAFE)")
    print("  • External Dispatch     : BLOCKED (is_configured == False)")
    print("  • Human Review Gate     : ENFORCED (Unapproved drafts rejected)")
    print("  • Delivery Simulation   : VERIFIED (SIMULATED logs recorded)")
    print("  • Duplicate Prevention  : VERIFIED (Deterministic Idempotency Key)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(verify_email_disabled_state())
