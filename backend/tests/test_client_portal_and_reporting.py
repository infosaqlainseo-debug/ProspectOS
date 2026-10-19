import uuid
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models import (
    Company,
    WebsiteScan,
    OpportunityProfile,
    MediaPlan,
    MediaPlanItem,
    PublisherRecord,
    OutreachDraft,
    PortalUser,
    ClientInvitation,
    ClientReport,
    ReportSchedule,
    ReportDeliveryLog,
    PortalAuditLog,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.schemas.portal import (
    UserRegisterRequest,
    UserLoginRequest,
    InviteCreateRequest,
    InviteAcceptRequest,
    ReportApprovalRequest,
    ReportDeliveryRequest,
)
from app.services.reporting.report_service import ReportingAndPortalService


@pytest.mark.asyncio
async def test_password_hashing_and_token_generation():
    """Verifies salted PBKDF2 password hashing, verification, and JWT session handling."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert "$" in hashed # salt$hash format
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

    # JWT generation & decoding
    user_id = uuid.uuid4()
    payload = {"sub": str(user_id), "role": "ADMIN", "email": "admin@example.com"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert decoded["role"] == "ADMIN"
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_user_registration_and_login(db_session):
    """Verifies portal user provisioning, login authentication, and JWT issuance."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Create target company
    company = Company(
        company_name=f"Acme Corp {suffix}",
        canonical_domain=f"acme-{suffix}.com",
        sales_stage="WON"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # 2. Register Client User
    reg_req = UserRegisterRequest(
        email=f"client_{suffix}@acme.com",
        password="SecureClientPass123!",
        full_name=f"Alice Acme {suffix}",
        company_id=company.id,
        role="CLIENT_USER"
    )
    user = await ReportingAndPortalService.register_user(db_session, reg_req)
    assert user.id is not None
    assert user.email == f"client_{suffix}@acme.com"
    assert user.company_id == company.id

    # 3. Authenticate
    login_req = UserLoginRequest(
        email=f"client_{suffix}@acme.com",
        password="SecureClientPass123!"
    )
    authenticated_user, token = await ReportingAndPortalService.login_user(db_session, login_req)
    assert authenticated_user.id == user.id
    assert token is not None

    # Verify invalid password raises 401
    with pytest.raises(Exception):
        bad_req = UserLoginRequest(
            email=f"client_{suffix}@acme.com",
            password="IncorrectPassword"
        )
        await ReportingAndPortalService.login_user(db_session, bad_req)


@pytest.mark.asyncio
async def test_client_invitation_lifecycle(db_session):
    """Tests client invitation creation, acceptance, and revocation."""
    suffix = uuid.uuid4().hex[:6]

    company = Company(
        company_name=f"TechCorp {suffix}",
        canonical_domain=f"techcorp-{suffix}.com",
        sales_stage="WON"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    admin_user = PortalUser(
        email=f"admin_{suffix}@agency.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Agency Admin",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # 1. Create invitation
    invite_req = InviteCreateRequest(
        company_id=company.id,
        email=f"invitee_{suffix}@techcorp.com",
        role="CLIENT_USER"
    )
    invitation = await ReportingAndPortalService.create_invitation(db_session, admin_user, invite_req)
    assert invitation.status == "PENDING"
    assert invitation.invitation_token is not None

    # 2. Accept invitation
    accept_req = InviteAcceptRequest(
        invitation_token=invitation.invitation_token,
        password="NewClientPass123!",
        full_name="Bob TechCorp"
    )
    new_user = await ReportingAndPortalService.accept_invitation(db_session, accept_req)
    assert new_user.email == f"invitee_{suffix}@techcorp.com"
    assert new_user.company_id == company.id

    await db_session.refresh(invitation)
    assert invitation.status == "ACCEPTED"


@pytest.mark.asyncio
async def test_cross_client_isolation_and_authorization(db_session):
    """
    CRITICAL SECURITY TEST:
    Enforces that Client A cannot access, view, or export Client B's workspace or reports.
    Any cross-tenant access attempt must be rejected with 403 Forbidden and audited.
    """
    suffix = uuid.uuid4().hex[:6]

    # Create Company A and Client User A
    comp_a = Company(company_name=f"Company A {suffix}", canonical_domain=f"compa-{suffix}.com")
    db_session.add(comp_a)
    await db_session.commit()
    await db_session.refresh(comp_a)

    user_a = PortalUser(
        email=f"user_a_{suffix}@compa.com",
        hashed_password=hash_password("PassA123!"),
        full_name="User A",
        role="CLIENT_USER",
        company_id=comp_a.id,
        is_active=True
    )
    db_session.add(user_a)

    # Create Company B and Client User B
    comp_b = Company(company_name=f"Company B {suffix}", canonical_domain=f"compb-{suffix}.com")
    db_session.add(comp_b)
    await db_session.commit()
    await db_session.refresh(comp_b)

    user_b = PortalUser(
        email=f"user_b_{suffix}@compb.com",
        hashed_password=hash_password("PassB123!"),
        full_name="User B",
        role="CLIENT_USER",
        company_id=comp_b.id,
        is_active=True
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    # Generate Report for Company B
    report_b = ClientReport(
        company_id=comp_b.id,
        title=f"Confidential Performance Report for B {suffix}",
        report_type="MONTHLY_PERFORMANCE",
        status="APPROVED",
        approval_status="APPROVED",
        sections=[],
        summary_metrics={},
        delivery_status="NOT_DELIVERED",
        generated_by="manual_operator"
    )
    db_session.add(report_b)
    await db_session.commit()
    await db_session.refresh(report_b)

    # User A tries to view Company B workspace -> MUST RAISE 403
    with pytest.raises(Exception) as exc_info:
        await ReportingAndPortalService.get_client_workspace(db_session, comp_b.id, user_a)
    assert "403" in str(exc_info.value) or "Access denied" in str(exc_info.value)

    # User A tries to export Company B report -> MUST RAISE 403
    with pytest.raises(Exception) as exc_info:
        await ReportingAndPortalService.export_report_markdown(db_session, report_b.id, user_a)
    assert "403" in str(exc_info.value) or "Access denied" in str(exc_info.value)

    # Check audit log recorded UNAUTHORIZED_ACCESS_ATTEMPT
    stmt = select(PortalAuditLog).where(
        PortalAuditLog.action == "UNAUTHORIZED_ACCESS_ATTEMPT",
        PortalAuditLog.user_id == user_a.id
    )
    audits = (await db_session.execute(stmt)).scalars().all()
    assert len(audits) >= 2
    assert any(a.resource_id == str(comp_b.id) for a in audits)


@pytest.mark.asyncio
async def test_report_synthesis_with_stored_records(db_session):
    """
    Tests automated report generation from stored records.
    Verifies section compilation, data minimization (no internal agency margins/costs),
    and non-fabrication disclosure.
    """
    suffix = uuid.uuid4().hex[:6]

    company = Company(
        company_name=f"E-Commerce Solutions {suffix}",
        canonical_domain=f"ecom-{suffix}.com",
        industry="Retail Technology",
        sales_stage="WON"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # Real website scan
    scan = WebsiteScan(
        company_id=company.id,
        url=f"https://ecom-{suffix}.com",
        http_status=200,
        https_enabled=True,
        title=f"E-Commerce Platform Solutions {suffix}",
        meta_description=f"Premier online shopping platform technology {suffix}",
        canonical_url=f"https://ecom-{suffix}.com",
        scan_status="COMPLETED"
    )
    # Opportunity profile
    opp = OpportunityProfile(
        company_id=company.id,
        recommended_service="GrokxSEO High-Intent Pillar Expansion",
        opportunity_score=85.0,
        supporting_evidence=[{"topic": "mobile retail categories", "intent": "commercial"}],
        confidence_level=0.9,
        data_freshness="CURRENT",
        methodology_version="1.0"
    )
    # Publisher Company & Record
    pub_company = Company(
        company_name=f"Tech Daily News {suffix}",
        canonical_domain=f"techdaily-{suffix}.com"
    )
    db_session.add(pub_company)
    await db_session.commit()
    await db_session.refresh(pub_company)

    publisher = PublisherRecord(
        company_id=pub_company.id,
        publisher_name=f"Tech Daily News {suffix}",
        audience_focus="Technology & Gadgets",
        status="VERIFIED"
    )
    db_session.add_all([scan, opp, publisher])
    await db_session.commit()
    await db_session.refresh(publisher)

    media_plan = MediaPlan(
        company_id=company.id,
        name=f"Q4 Digital PR Plan {suffix}",
        status="FINAL"
    )
    db_session.add(media_plan)
    await db_session.commit()
    await db_session.refresh(media_plan)

    plan_item = MediaPlanItem(
        media_plan_id=media_plan.id,
        publisher_id=publisher.id,
        proposed_price=750.0,
        proposed_currency="USD",
        notes="High-authority thought leadership feature"
    )
    db_session.add(plan_item)
    await db_session.commit()

    # Generate report
    report = await ReportingAndPortalService.generate_client_report(
        db=db_session,
        company_id=company.id,
        title=f"Monthly SEO & Media Review ({suffix})",
        report_type="MONTHLY_PERFORMANCE",
        custom_notes="Excellent momentum observed across digital PR initiatives."
    )

    assert report.id is not None
    assert report.approval_status == "UNAPPROVED" # Default safety boundary
    assert len(report.sections) >= 6

    # Verify sections content
    section_ids = [s["section_id"] for s in report.sections]
    assert "executive_summary" in section_ids
    assert "technical_seo" in section_ids
    assert "content_opportunities" in section_ids
    assert "backlinks_and_authority" in section_ids
    assert "publisher_placements" in section_ids
    assert "strategic_recommendations" in section_ids

    # Verify non-fabrication caveat is present
    limitations = report.data_limitations
    assert any("Non-Fabrication Policy" in lim for lim in limitations)


@pytest.mark.asyncio
async def test_report_approval_and_delivery_safety_gate(db_session):
    """
    CRITICAL DELIVERY SAFETY TEST:
    Reports cannot be dispatched to clients unless explicitly approved.
    """
    suffix = uuid.uuid4().hex[:6]

    company = Company(company_name=f"Logistics Co {suffix}", canonical_domain=f"logistics-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    admin_user = PortalUser(
        email=f"director_{suffix}@agency.com",
        hashed_password=hash_password("DirectorPass123!"),
        full_name="Agency Director",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Generate unapproved draft report
    report = await ReportingAndPortalService.generate_client_report(
        db=db_session,
        company_id=company.id,
        title=f"Quarterly Business Review {suffix}",
        actor=admin_user
    )
    assert report.approval_status == "UNAPPROVED"

    # Attempt delivery before approval -> MUST FAIL WITH 400
    with pytest.raises(Exception) as exc_info:
        await ReportingAndPortalService.deliver_report(
            db=db_session,
            report_id=report.id,
            actor=admin_user,
            req=ReportDeliveryRequest(recipients=[f"client_{suffix}@logistics.com"], simulate=True)
        )
    assert "approval_status == 'APPROVED'" in str(exc_info.value) or "Approval required" in str(exc_info.value)

    # Approve report
    approved_report = await ReportingAndPortalService.approve_report(
        db=db_session,
        report_id=report.id,
        actor=admin_user,
        req=ReportApprovalRequest(approval_status="APPROVED", notes="Reviewed and approved by Agency Director")
    )
    assert approved_report.approval_status == "APPROVED"
    assert approved_report.approved_by_user_id == admin_user.id

    # Now delivery must succeed
    logs = await ReportingAndPortalService.deliver_report(
        db=db_session,
        report_id=report.id,
        actor=admin_user,
        req=ReportDeliveryRequest(recipients=[f"client_{suffix}@logistics.com"], simulate=True)
    )
    assert len(logs) == 1
    assert logs[0].status == "SIMULATED" or logs[0].status == "SENT"


@pytest.mark.asyncio
async def test_duplicate_send_prevention_idempotency(db_session):
    """
    Verifies that re-triggering report delivery does NOT send duplicate emails,
    using unique deterministic idempotency keys.
    """
    suffix = uuid.uuid4().hex[:6]

    company = Company(company_name=f"FinTech Group {suffix}", canonical_domain=f"fintech-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    admin_user = PortalUser(
        email=f"account_manager_{suffix}@agency.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Account Manager",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    report = await ReportingAndPortalService.generate_client_report(
        db=db_session,
        company_id=company.id,
        title=f"SEO Performance Report {suffix}",
        actor=admin_user
    )
    await ReportingAndPortalService.approve_report(
        db=db_session,
        report_id=report.id,
        actor=admin_user,
        req=ReportApprovalRequest(approval_status="APPROVED")
    )

    # First delivery
    recipient = f"cfo_{suffix}@fintech.com"
    req = ReportDeliveryRequest(recipients=[recipient], simulate=True)
    first_logs = await ReportingAndPortalService.deliver_report(db_session, report.id, admin_user, req)
    assert len(first_logs) == 1
    first_log_id = first_logs[0].id

    # Retry delivery on same day
    second_logs = await ReportingAndPortalService.deliver_report(db_session, report.id, admin_user, req)
    assert len(second_logs) == 1
    # MUST return existing log or prevent new dispatch
    assert second_logs[0].id == first_log_id


@pytest.mark.asyncio
async def test_report_export_markdown_and_html(db_session):
    """Verifies that approved reports can be cleanly exported to Markdown and HTML."""
    suffix = uuid.uuid4().hex[:6]

    company = Company(company_name=f"Global Health {suffix}", canonical_domain=f"gh-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    admin_user = PortalUser(
        email=f"admin_{suffix}@agency.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    report = await ReportingAndPortalService.generate_client_report(
        db=db_session,
        company_id=company.id,
        title=f"Health SEO Audit {suffix}",
        actor=admin_user
    )
    await ReportingAndPortalService.approve_report(
        db=db_session,
        report_id=report.id,
        actor=admin_user,
        req=ReportApprovalRequest(approval_status="APPROVED")
    )

    # Export Markdown
    md = await ReportingAndPortalService.export_report_markdown(db_session, report.id, admin_user)
    assert "# Health SEO Audit" in md
    assert company.company_name in md
    assert "Data Limitations & Integrity Notice" in md

    # Export HTML
    html = await ReportingAndPortalService.export_report_html(db_session, report.id, admin_user)
    assert "<!DOCTYPE html>" in html
    assert f"Health SEO Audit {suffix}" in html


@pytest.mark.asyncio
async def test_report_scheduling_and_trigger(db_session):
    """Verifies recurring report schedules, time zones, and automated worker trigger."""
    from app.schemas.portal import ScheduleCreateRequest
    suffix = uuid.uuid4().hex[:6]

    company = Company(company_name=f"SaaS Hub {suffix}", canonical_domain=f"saashub-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    admin_user = PortalUser(
        email=f"scheduler_admin_{suffix}@agency.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Scheduler Admin",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    sched_req = ScheduleCreateRequest(
        company_id=company.id,
        report_type="MONTHLY_PERFORMANCE",
        frequency="MONTHLY",
        time_of_day="09:00",
        time_zone="America/New_York",
        recipients=[f"ops_{suffix}@saashub.com"],
        requires_approval=True
    )
    schedule = await ReportingAndPortalService.create_schedule(db_session, admin_user, sched_req)
    assert schedule.id is not None
    assert schedule.time_zone == "America/New_York"
    assert schedule.is_active is True

    # Artificially set next_run_at to past to test trigger
    schedule.next_run_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.commit()

    # Trigger scheduled reports
    generated = await ReportingAndPortalService.trigger_scheduled_reports(db_session)
    assert len(generated) >= 1
    assert any(g.company_id == company.id for g in generated)

    # Verify next_run_at was advanced into the future
    await db_session.refresh(schedule)
    assert schedule.next_run_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_portal_api_routes_and_authorization(db_session):
    """
    Tests complete FastAPI HTTP route stack with JWT bearer tokens:
    - Login & /auth/me
    - Report generation, review, approval & delivery
    - Tenant isolation: client user attempting to access another company rejected with 403
    - Export format handling
    - Security audit log inspection
    """
    suffix = uuid.uuid4().hex[:6]

    # Setup Company A and Company B
    comp_a = Company(company_name=f"API Client A {suffix}", canonical_domain=f"apiclienta-{suffix}.com")
    comp_b = Company(company_name=f"API Client B {suffix}", canonical_domain=f"apiclientb-{suffix}.com")
    db_session.add_all([comp_a, comp_b])
    await db_session.commit()
    await db_session.refresh(comp_a)
    await db_session.refresh(comp_b)

    # Setup Admin user
    admin_user = PortalUser(
        email=f"admin_api_{suffix}@agency.com",
        hashed_password=hash_password("AdminSecure123!"),
        full_name="API Admin",
        role="ADMIN",
        is_active=True
    )
    # Setup Client User A
    client_a = PortalUser(
        email=f"client_a_{suffix}@clienta.com",
        hashed_password=hash_password("ClientSecure123!"),
        full_name="Client A User",
        role="CLIENT_USER",
        company_id=comp_a.id,
        is_active=True
    )
    db_session.add_all([admin_user, client_a])
    await db_session.commit()
    await db_session.refresh(admin_user)
    await db_session.refresh(client_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login Admin
        login_res = await ac.post("/portal/auth/login", json={
            "email": f"admin_api_{suffix}@agency.com",
            "password": "AdminSecure123!"
        })
        assert login_res.status_code == 200
        admin_token = login_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Login Client A
        client_res = await ac.post("/portal/auth/login", json={
            "email": f"client_a_{suffix}@clienta.com",
            "password": "ClientSecure123!"
        })
        assert client_res.status_code == 200
        client_token = client_res.json()["access_token"]
        client_headers = {"Authorization": f"Bearer {client_token}"}

        # 3. Verify /auth/me
        me_res = await ac.get("/portal/auth/me", headers=client_headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == f"client_a_{suffix}@clienta.com"
        assert me_res.json()["company_id"] == str(comp_a.id)

        # 4. Admin generates report for Company A
        gen_res = await ac.post("/portal/reports", headers=admin_headers, json={
            "company_id": str(comp_a.id),
            "title": f"Monthly Performance Review ({suffix})",
            "report_type": "MONTHLY_PERFORMANCE",
            "custom_notes": "Steady growth in top-tier organic keywords"
        })
        assert gen_res.status_code == 200
        report_data = gen_res.json()
        report_id = report_data["id"]
        assert report_data["approval_status"] == "UNAPPROVED"

        # 5. Client A cannot see unapproved report
        list_client_res = await ac.get("/portal/reports", headers=client_headers)
        assert list_client_res.status_code == 200
        # Should be empty because approval_status != "APPROVED"
        assert not any(r["id"] == report_id for r in list_client_res.json())

        # 6. Admin approves report
        appr_res = await ac.post(f"/portal/reports/{report_id}/approve", headers=admin_headers, json={
            "approval_status": "APPROVED",
            "notes": "Verified all data points"
        })
        assert appr_res.status_code == 200
        assert appr_res.json()["approval_status"] == "APPROVED"

        # 7. Now Client A can view approved report
        list_client_res2 = await ac.get("/portal/reports", headers=client_headers)
        assert any(r["id"] == report_id for r in list_client_res2.json())

        # 8. Client A can view workspace for Company A
        ws_res = await ac.get(f"/portal/workspace/{comp_a.id}", headers=client_headers)
        assert ws_res.status_code == 200
        assert ws_res.json()["company_name"] == comp_a.company_name
        assert ws_res.json()["available_reports_count"] >= 1

        # 9. CROSS-TENANT ISOLATION: Client A attempts to access Company B workspace -> 403 FORBIDDEN
        cross_res = await ac.get(f"/portal/workspace/{comp_b.id}", headers=client_headers)
        assert cross_res.status_code == 403
        assert "Cross-client access is strictly forbidden" in cross_res.json()["detail"]

        # 10. Client A exports approved report in HTML
        export_res = await ac.get(f"/portal/reports/{report_id}/export?format=html", headers=client_headers)
        assert export_res.status_code == 200
        assert "<!DOCTYPE html>" in export_res.text

        # 11. Admin delivers report
        deliver_res = await ac.post(f"/portal/reports/{report_id}/deliver", headers=admin_headers, json={
            "recipients": [f"exec_{suffix}@clienta.com"],
            "simulate": True
        })
        assert deliver_res.status_code == 200
        assert len(deliver_res.json()) == 1
        assert deliver_res.json()[0]["status"] == "SIMULATED"

        # 12. Admin checks audit logs
        audit_res = await ac.get("/portal/audit-logs", headers=admin_headers)
        assert audit_res.status_code == 200
        assert len(audit_res.json()) > 0
        actions = [a["action"] for a in audit_res.json()]
        assert "UNAUTHORIZED_ACCESS_ATTEMPT" in actions
        assert "CREATE_REPORT" in actions
        assert "APPROVE_REPORT" in actions
