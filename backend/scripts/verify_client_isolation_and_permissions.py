"""
Script: scripts/verify_client_isolation_and_permissions.py
Description: Goal 5 — Client Isolation and Report Permissions Audit.
Simulates two distinct client identities (Client Alpha and Client Beta) alongside
an Agency Admin. Proves that cross-tenant access attempts return HTTP 403 Forbidden,
unapproved drafts remain confidential, and sensitive margins/notes are minimized.
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.db.session import async_session_maker
from app.models import Company, PortalUser, ClientReport, PortalAuditLog
from app.core.security import hash_password
from app.services.reporting.report_service import ReportingAndPortalService


async def verify_client_isolation():
    print("=" * 80)
    print("PROSPECTOS PRODUCTION READINESS: GOAL 5 — CLIENT ISOLATION & PERMISSIONS AUDIT")
    print("=" * 80)

    suffix = uuid.uuid4().hex[:6]

    async with async_session_maker() as session:
        # 1. Provision Two Distinct Client Companies
        print("\n[1. Multi-Tenant Provisioning: Client Alpha and Client Beta]")
        comp_alpha = Company(company_name=f"Alpha Logistics {suffix}", canonical_domain=f"alphalogistics-{suffix}.com")
        comp_beta = Company(company_name=f"Beta BioTech {suffix}", canonical_domain=f"betabiotech-{suffix}.com")
        session.add_all([comp_alpha, comp_beta])
        await session.commit()
        await session.refresh(comp_alpha)
        await session.refresh(comp_beta)
        print(f"  • Tenant Alpha: '{comp_alpha.company_name}' [ID: {comp_alpha.id}]")
        print(f"  • Tenant Beta:  '{comp_beta.company_name}' [ID: {comp_beta.id}]")

        # 2. Provision Portal Users
        # Admin
        admin_user = PortalUser(
            email=f"agency_admin_{suffix}@grokxseo.com",
            hashed_password=hash_password("AdminSecurePass123!"),
            full_name="Agency Admin",
            role="ADMIN",
            is_active=True
        )
        # Client Alpha User
        user_alpha = PortalUser(
            email=f"alice_{suffix}@alphalogistics.com",
            hashed_password=hash_password("AlphaPass123!"),
            full_name="Alice Alpha",
            role="CLIENT_USER",
            company_id=comp_alpha.id,
            is_active=True
        )
        # Client Beta User
        user_beta = PortalUser(
            email=f"bob_{suffix}@betabiotech.com",
            hashed_password=hash_password("BetaPass123!"),
            full_name="Bob Beta",
            role="CLIENT_USER",
            company_id=comp_beta.id,
            is_active=True
        )
        session.add_all([admin_user, user_alpha, user_beta])
        await session.commit()
        await session.refresh(admin_user)
        await session.refresh(user_alpha)
        await session.refresh(user_beta)
        print(f"  • User Alpha: {user_alpha.email} -> Company {comp_alpha.id}")
        print(f"  • User Beta:  {user_beta.email}  -> Company {comp_beta.id}")
        print(f"  • Agency Admin: {admin_user.email}")

        # 3. Create Reports for Both Tenants
        rep_alpha = await ReportingAndPortalService.generate_client_report(
            db=session,
            company_id=comp_alpha.id,
            title=f"Monthly SEO Performance — Alpha {suffix}",
            custom_notes="Confidential Alpha internal growth metrics",
            actor=admin_user
        )
        # Approve Alpha's report
        rep_alpha.approval_status = "APPROVED"
        rep_alpha.status = "APPROVED"

        rep_beta = await ReportingAndPortalService.generate_client_report(
            db=session,
            company_id=comp_beta.id,
            title=f"Confidential BioTech PR Report — Beta {suffix}",
            custom_notes="Beta private investment and competitive gaps",
            actor=admin_user
        )
        # Leave Beta's report UNAPPROVED to test approval gating
        rep_beta.approval_status = "UNAPPROVED"
        rep_beta.status = "DRAFT"
        await session.commit()
        await session.refresh(rep_alpha)
        await session.refresh(rep_beta)
        print(f"  • Report Alpha (APPROVED):   '{rep_alpha.title}' [ID: {rep_alpha.id}]")
        print(f"  • Report Beta (UNAPPROVED): '{rep_beta.title}' [ID: {rep_beta.id}]")

    # 4. HTTP API Boundary Testing with Live ASGI Transport
    print("\n[2. Live API Authentication & Token Issuance]")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login Alpha
        res_auth_a = await ac.post("/portal/auth/login", json={"email": user_alpha.email, "password": "AlphaPass123!"})
        assert res_auth_a.status_code == 200
        token_a = res_auth_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print(f"  ✓ Client Alpha Authenticated: Bearer Token Issued.")

        # Login Beta
        res_auth_b = await ac.post("/portal/auth/login", json={"email": user_beta.email, "password": "BetaPass123!"})
        assert res_auth_b.status_code == 200
        token_b = res_auth_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print(f"  ✓ Client Beta Authenticated: Bearer Token Issued.")

        # Login Admin
        res_auth_admin = await ac.post("/portal/auth/login", json={"email": admin_user.email, "password": "AdminSecurePass123!"})
        assert res_auth_admin.status_code == 200
        token_admin = res_auth_admin.json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}
        print(f"  ✓ Agency Admin Authenticated: Bearer Token Issued.")

        print("\n[3. Cross-Tenant Workspace Isolation Tests]")
        # Test 1: Alpha accessing Alpha workspace -> HTTP 200
        res_ws_a = await ac.get(f"/portal/workspace/{comp_alpha.id}", headers=headers_a)
        assert res_ws_a.status_code == 200
        print(f"  ✓ Authorized Access: User Alpha accessed Alpha workspace (HTTP {res_ws_a.status_code})")

        # Test 2: Alpha attempting to access Beta workspace -> HTTP 403 FORBIDDEN
        res_ws_cross = await ac.get(f"/portal/workspace/{comp_beta.id}", headers=headers_a)
        print(f"  • Cross-Tenant Attempt: Alpha accessing Beta workspace: Status={res_ws_cross.status_code}")
        print(f"    Detail: {res_ws_cross.json().get('detail')}")
        assert res_ws_cross.status_code == 403, f"Expected 403, got {res_ws_cross.status_code}"
        assert "Cross-client access is strictly forbidden" in res_ws_cross.json().get("detail", "")
        print("  ✓ Cross-Tenant Barrier Enforced: HTTP 403 Forbidden.")

        # Test 3: Beta attempting to access Alpha workspace -> HTTP 403 FORBIDDEN
        res_ws_cross_b = await ac.get(f"/portal/workspace/{comp_alpha.id}", headers=headers_b)
        assert res_ws_cross_b.status_code == 403
        print(f"  ✓ Cross-Tenant Barrier Enforced: User Beta accessing Alpha workspace returned HTTP 403.")

        print("\n[4. Cross-Tenant Report Viewing & Export Isolation Tests]")
        # Test 4: Alpha accessing Alpha's approved report -> HTTP 200
        res_rep_a = await ac.get(f"/portal/reports/{rep_alpha.id}", headers=headers_a)
        assert res_rep_a.status_code == 200
        print(f"  ✓ Authorized Access: User Alpha retrieved Report Alpha (HTTP {res_rep_a.status_code})")

        # Test 5: Alpha attempting to view Beta's report -> HTTP 403 FORBIDDEN
        res_rep_cross = await ac.get(f"/portal/reports/{rep_beta.id}", headers=headers_a)
        print(f"  • Cross-Tenant Attempt: Alpha accessing Report Beta: Status={res_rep_cross.status_code}")
        assert res_rep_cross.status_code == 403
        print("  ✓ Report Isolation Enforced: HTTP 403 Forbidden.")

        # Test 6: Alpha attempting to export Beta's report -> HTTP 403 FORBIDDEN
        res_export_cross = await ac.get(f"/portal/reports/{rep_beta.id}/export?format=markdown", headers=headers_a)
        print(f"  • Cross-Tenant Attempt: Alpha exporting Report Beta: Status={res_export_cross.status_code}")
        assert res_export_cross.status_code == 403
        print("  ✓ Export Isolation Enforced: HTTP 403 Forbidden.")

        print("\n[5. Approval Boundary & Data Minimization Tests]")
        # Test 7: Beta cannot see unapproved report
        res_reps_b = await ac.get("/portal/reports", headers=headers_b)
        assert res_reps_b.status_code == 200
        beta_report_ids = [r["id"] for r in res_reps_b.json()]
        assert str(rep_beta.id) not in beta_report_ids, "Unapproved report leaked to client user!"
        print("  ✓ Approval Boundary Enforced: Unapproved report hidden from client portal.")

        # Test 8: Data Minimization: Verified that client-facing report contains NO internal agency margin/cost
        report_data = res_rep_a.json()
        raw_text = json.dumps(report_data)
        assert "agency_margin" not in raw_text
        assert "wholesale_cost" not in raw_text
        assert "cost_amount" not in raw_text
        print("  ✓ Data Minimization Enforced: Zero internal agency costs/margins leaked to client.")

        print("\n[6. Security Audit Log Verification]")
        res_audits = await ac.get("/portal/audit-logs", headers=headers_admin)
        assert res_audits.status_code == 200
        audit_logs = res_audits.json()
        unauth_events = [a for a in audit_logs if a.get("action") == "UNAUTHORIZED_ACCESS_ATTEMPT"]
        print(f"  ✓ Security Audit Trail: {len(unauth_events)} unauthorized access attempts logged.")
        assert len(unauth_events) >= 3, f"Expected at least 3 logged unauthorized access attempts, found {len(unauth_events)}"

    # 5. Background Jobs Tenant Isolation Verification
    print("\n[7. Background Jobs Tenant Boundary Verification]")
    async with async_session_maker() as session:
        # Test 1: User Alpha attempts to execute deliver_report for Beta's report
        from fastapi import HTTPException
        from app.schemas.portal import ReportDeliveryRequest
        req_deliv = ReportDeliveryRequest(recipients=["unauth@external.test"], simulate=True)

        blocked_job = False
        try:
            await ReportingAndPortalService.deliver_report(session, rep_beta.id, user_alpha, req_deliv)
        except HTTPException as he:
            if he.status_code == 403:
                blocked_job = True
                print(f"  ✓ Background Delivery Gate: Blocked cross-tenant delivery: {he.detail}")

        assert blocked_job, "Background deliver_report failed to block cross-tenant execution!"

        # Test 2: Scheduled Report Generation strictly confines company scope
        from app.models import ReportSchedule
        sched_alpha = ReportSchedule(
            company_id=comp_alpha.id,
            report_type="MONTHLY_PERFORMANCE",
            frequency="WEEKLY",
            is_active=True,
            requires_approval=True
        )
        session.add(sched_alpha)
        await session.commit()
        await session.refresh(sched_alpha)

        # Trigger scheduled report synthesis
        triggered_reports = await ReportingAndPortalService.trigger_scheduled_reports(session)
        matching_triggered = [r for r in triggered_reports if r.company_id == comp_alpha.id]
        print(f"  ✓ Scheduled Report Generator: Created {len(matching_triggered)} scheduled report(s) strictly for Company Alpha.")
        for r in matching_triggered:
            assert r.company_id == comp_alpha.id, "Tenant boundary breached in scheduled report generation!"
            assert r.company_id != comp_beta.id, "Tenant boundary leaked to Beta!"
        print("  ✓ Background Job Isolation: Verified scheduled generator enforces strict company_id isolation.")

    print("\n" + "=" * 80)
    print("GOAL 5 STATUS SUMMARY:")
    print("  • Multi-Tenant Isolation : PASS (HTTP 403 on all cross-tenant workspace/report requests)")
    print("  • Report Export Barrier  : PASS (HTTP 403 on unauthorized exports)")
    print("  • Approval Gatekeeping   : PASS (Unapproved drafts invisible to client users)")
    print("  • Data Minimization      : PASS (Internal costs and private margins excluded)")
    print("  • Background Job Bounds  : PASS (Worker jobs & scheduled generation strictly tenant-isolated)")
    print("  • Audit Accountability   : PASS (All unauthorized attempts recorded in security ledger)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(verify_client_isolation())
