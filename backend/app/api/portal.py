import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.db.session import get_db
from app.models import (
    Company,
    PortalUser,
    ClientInvitation,
    ClientReport,
    ReportSchedule,
    ReportDeliveryLog,
    PortalAuditLog,
)
from app.core.security import (
    get_current_user,
    require_roles,
    enforce_client_isolation,
)
from app.schemas.portal import (
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    InviteCreateRequest,
    InviteAcceptRequest,
    InviteResponse,
    ReportCreateRequest,
    ReportUpdateRequest,
    ReportApprovalRequest,
    ReportDeliveryRequest,
    ClientReportResponse,
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    DeliveryLogResponse,
    PortalWorkspaceResponse,
    PortalAuditLogResponse,
)
from app.services.reporting.report_service import ReportingAndPortalService

router = APIRouter(prefix="/portal", tags=["Client Portals & Automated Reporting"])


# =========================================================================
# 1. Authentication & Session Endpoints
# =========================================================================

@router.post("/auth/register", response_model=UserResponse)
async def register(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[PortalUser] = Depends(lambda: None) # Allow self-registration or admin provision
):
    """Registers a new portal user or client account."""
    user = await ReportingAndPortalService.register_user(db, req, actor=current_user)
    company_name = None
    if user.company_id:
        comp = await db.get(Company, user.company_id)
        if comp:
            company_name = comp.company_name

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        company_name=company_name,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    req: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates portal user and returns JWT bearer token."""
    ip_addr = request.client.host if request.client else None
    user, token = await ReportingAndPortalService.login_user(db, req, ip_address=ip_addr)

    company_name = None
    if user.company_id:
        comp = await db.get(Company, user.company_id)
        if comp:
            company_name = comp.company_name

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        company_name=company_name,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: PortalUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns profile for currently authenticated user."""
    company_name = None
    if current_user.company_id:
        comp = await db.get(Company, current_user.company_id)
        if comp:
            company_name = comp.company_name

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        company_id=current_user.company_id,
        company_name=company_name,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
    )


# =========================================================================
# 2. Client Invitation Management
# =========================================================================

@router.post("/invitations", response_model=InviteResponse)
async def create_invitation(
    req: InviteCreateRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new client invitation token."""
    invitation = await ReportingAndPortalService.create_invitation(db, current_user, req)
    comp = await db.get(Company, invitation.company_id)
    return InviteResponse(
        id=invitation.id,
        company_id=invitation.company_id,
        company_name=comp.company_name if comp else None,
        email=invitation.email,
        invitation_token=invitation.invitation_token,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.post("/invitations/accept", response_model=UserResponse)
async def accept_invitation(
    req: InviteAcceptRequest,
    db: AsyncSession = Depends(get_db)
):
    """Accepts an invitation token and provisions a client user account."""
    user = await ReportingAndPortalService.accept_invitation(db, req)
    comp = await db.get(Company, user.company_id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        company_name=comp.company_name if comp else None,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.delete("/invitations/{id}", response_model=InviteResponse)
async def revoke_invitation(
    id: uuid.UUID,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Revokes a pending client invitation."""
    invitation = await ReportingAndPortalService.revoke_invitation(db, current_user, id)
    comp = await db.get(Company, invitation.company_id)
    return InviteResponse(
        id=invitation.id,
        company_id=invitation.company_id,
        company_name=comp.company_name if comp else None,
        email=invitation.email,
        invitation_token=invitation.invitation_token,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


# =========================================================================
# 3. Client Reports Management
# =========================================================================

async def _format_report_response(db: AsyncSession, r: ClientReport) -> ClientReportResponse:
    comp = await db.get(Company, r.company_id)
    return ClientReportResponse(
        id=r.id,
        company_id=r.company_id,
        company_name=comp.company_name if comp else "Client",
        title=r.title,
        report_type=r.report_type,
        reporting_period_start=r.reporting_period_start,
        reporting_period_end=r.reporting_period_end,
        status=r.status,
        approval_status=r.approval_status,
        approved_by_user_id=r.approved_by_user_id,
        approved_at=r.approved_at,
        branding=r.branding or {},
        sections=r.sections or [],
        summary_metrics=r.summary_metrics or {},
        delivery_status=r.delivery_status,
        generated_by=r.generated_by,
        data_limitations=r.data_limitations or [],
        export_formats=r.export_formats or {},
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.post("/reports", response_model=ClientReportResponse)
async def generate_report(
    req: ReportCreateRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Generates an automated, evidence-backed client report."""
    report = await ReportingAndPortalService.generate_client_report(
        db=db,
        company_id=req.company_id,
        title=req.title,
        report_type=req.report_type,
        period_start=req.reporting_period_start,
        period_end=req.reporting_period_end,
        branding=req.branding,
        custom_notes=req.custom_notes,
        actor=current_user,
        generated_by="manual_operator"
    )
    return await _format_report_response(db, report)


@router.get("/reports", response_model=List[ClientReportResponse])
async def list_reports(
    company_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    approval_filter: Optional[str] = Query(None),
    current_user: PortalUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists client reports.
    If CLIENT_USER, strictly limited to their own company_id.
    """
    stmt = select(ClientReport)

    if current_user.role == "CLIENT_USER":
        # Force strict tenant filter
        stmt = stmt.where(
            and_(
                ClientReport.company_id == current_user.company_id,
                ClientReport.approval_status == "APPROVED" # Clients only see approved reports
            )
        )
    else:
        if company_id:
            stmt = stmt.where(ClientReport.company_id == company_id)

    if status_filter:
        stmt = stmt.where(ClientReport.status == status_filter)
    if approval_filter:
        stmt = stmt.where(ClientReport.approval_status == approval_filter)

    stmt = stmt.order_by(desc(ClientReport.created_at)).limit(50)
    reports = (await db.execute(stmt)).scalars().all()

    results = []
    for r in reports:
        results.append(await _format_report_response(db, r))
    return results


@router.get("/reports/{id}", response_model=ClientReportResponse)
async def get_report(
    id: uuid.UUID,
    current_user: PortalUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a specific client report with tenant isolation check."""
    report = await db.get(ClientReport, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    await enforce_client_isolation(current_user, report.company_id, db, action="VIEW_REPORT")

    if current_user.role == "CLIENT_USER" and report.approval_status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report is currently under review by your agency account team and has not yet been approved."
        )

    return await _format_report_response(db, report)


@router.put("/reports/{id}", response_model=ClientReportResponse)
async def update_report(
    id: uuid.UUID,
    req: ReportUpdateRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Updates report title, branding, or sections."""
    report = await db.get(ClientReport, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if req.title is not None:
        report.title = req.title
    if req.branding is not None:
        report.branding = req.branding
    if req.sections is not None:
        report.sections = req.sections
    if req.status is not None:
        report.status = req.status

    await db.commit()
    await db.refresh(report)
    return await _format_report_response(db, report)


@router.post("/reports/{id}/approve", response_model=ClientReportResponse)
async def approve_report(
    id: uuid.UUID,
    req: ReportApprovalRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Approves or rejects a report for client presentation."""
    report = await ReportingAndPortalService.approve_report(db, id, current_user, req)
    return await _format_report_response(db, report)


@router.post("/reports/{id}/deliver", response_model=List[DeliveryLogResponse])
async def deliver_report(
    id: uuid.UUID,
    req: ReportDeliveryRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Dispatches report to external client recipients.
    Enforces approval boundary and idempotency to prevent duplicate sends.
    """
    logs = await ReportingAndPortalService.deliver_report(db, id, current_user, req)
    return [
        DeliveryLogResponse(
            id=l.id,
            report_id=l.report_id,
            recipient_email=l.recipient_email,
            delivery_channel=l.delivery_channel,
            idempotency_key=l.idempotency_key,
            status=l.status,
            sent_at=l.sent_at,
            error_message=l.error_message,
            created_at=l.created_at,
        ) for l in logs
    ]


@router.get("/reports/{id}/export")
async def export_report(
    id: uuid.UUID,
    format: str = Query("markdown", pattern="^(markdown|html|pdf)$"),
    current_user: PortalUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exports report to Markdown or print-ready HTML with client isolation check."""
    if format == "html" or format == "pdf":
        html_content = await ReportingAndPortalService.export_report_html(db, id, current_user)
        return Response(content=html_content, media_type="text/html")
    else:
        md_content = await ReportingAndPortalService.export_report_markdown(db, id, current_user)
        return Response(content=md_content, media_type="text/markdown")


# =========================================================================
# 4. Report Scheduling
# =========================================================================

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    req: ScheduleCreateRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Creates a recurring report generation schedule."""
    schedule = await ReportingAndPortalService.create_schedule(db, current_user, req)
    comp = await db.get(Company, schedule.company_id)
    return ScheduleResponse(
        id=schedule.id,
        company_id=schedule.company_id,
        company_name=comp.company_name if comp else None,
        report_type=schedule.report_type,
        frequency=schedule.frequency,
        day_of_month=schedule.day_of_month,
        day_of_week=schedule.day_of_week,
        time_of_day=schedule.time_of_day,
        time_zone=schedule.time_zone,
        recipients=schedule.recipients or [],
        is_active=schedule.is_active,
        requires_approval=schedule.requires_approval,
        last_generated_at=schedule.last_generated_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
    )


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    company_id: Optional[uuid.UUID] = Query(None),
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Lists reporting schedules."""
    stmt = select(ReportSchedule)
    if company_id:
        stmt = stmt.where(ReportSchedule.company_id == company_id)
    stmt = stmt.order_by(desc(ReportSchedule.created_at))
    schedules = (await db.execute(stmt)).scalars().all()

    results = []
    for s in schedules:
        comp = await db.get(Company, s.company_id)
        results.append(
            ScheduleResponse(
                id=s.id,
                company_id=s.company_id,
                company_name=comp.company_name if comp else None,
                report_type=s.report_type,
                frequency=s.frequency,
                day_of_month=s.day_of_month,
                day_of_week=s.day_of_week,
                time_of_day=s.time_of_day,
                time_zone=s.time_zone,
                recipients=s.recipients or [],
                is_active=s.is_active,
                requires_approval=s.requires_approval,
                last_generated_at=s.last_generated_at,
                next_run_at=s.next_run_at,
                created_at=s.created_at,
            )
        )
    return results


@router.put("/schedules/{id}", response_model=ScheduleResponse)
async def update_schedule(
    id: uuid.UUID,
    req: ScheduleUpdateRequest,
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Updates reporting schedule properties."""
    s = await ReportingAndPortalService.update_schedule(db, current_user, id, req)
    comp = await db.get(Company, s.company_id)
    return ScheduleResponse(
        id=s.id,
        company_id=s.company_id,
        company_name=comp.company_name if comp else None,
        report_type=s.report_type,
        frequency=s.frequency,
        day_of_month=s.day_of_month,
        day_of_week=s.day_of_week,
        time_of_day=s.time_of_day,
        time_zone=s.time_zone,
        recipients=s.recipients or [],
        is_active=s.is_active,
        requires_approval=s.requires_approval,
        last_generated_at=s.last_generated_at,
        next_run_at=s.next_run_at,
        created_at=s.created_at,
    )


@router.post("/schedules/trigger", response_model=List[ClientReportResponse])
async def trigger_schedules(
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Manually triggers due scheduled report jobs."""
    reports = await ReportingAndPortalService.trigger_scheduled_reports(db)
    results = []
    for r in reports:
        results.append(await _format_report_response(db, r))
    return results


# =========================================================================
# 5. Client Workspace Portal
# =========================================================================

@router.get("/workspace/{company_id}", response_model=PortalWorkspaceResponse)
async def get_workspace(
    company_id: uuid.UUID,
    current_user: PortalUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the secure client workspace overview.
    Enforces server-side cross-client isolation.
    """
    data = await ReportingAndPortalService.get_client_workspace(db, company_id, current_user)
    latest_rep = None
    if data.get("latest_approved_report"):
        latest_rep = await _format_report_response(db, data["latest_approved_report"])

    comp = await db.get(Company, company_id)

    return PortalWorkspaceResponse(
        company_id=data["company_id"],
        company_name=data["company_name"],
        canonical_domain=data["canonical_domain"],
        industry=data["industry"],
        client_user=UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            company_id=current_user.company_id,
            company_name=comp.company_name if comp else None,
            is_active=current_user.is_active,
            last_login_at=current_user.last_login_at,
            created_at=current_user.created_at,
        ),
        latest_approved_report=latest_rep,
        available_reports_count=data["available_reports_count"],
        active_campaigns_count=data["active_campaigns_count"],
        approved_media_plans_count=data["approved_media_plans_count"],
        verified_seo_health=data["verified_seo_health"],
        client_visible_opportunities=data["client_visible_opportunities"],
        branding=data["branding"],
        data_freshness=data["data_freshness"],
    )


# =========================================================================
# 6. Portal Security & Access Audit Logs
# =========================================================================

@router.get("/audit-logs", response_model=List[PortalAuditLogResponse])
async def list_audit_logs(
    company_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_user: PortalUser = Depends(require_roles(["ADMIN", "AGENCY_STAFF"])),
    db: AsyncSession = Depends(get_db)
):
    """Lists administrative, authentication, and access audit events."""
    stmt = select(PortalAuditLog)
    if company_id:
        stmt = stmt.where(PortalAuditLog.company_id == company_id)
    if action:
        stmt = stmt.where(PortalAuditLog.action == action)
    stmt = stmt.order_by(desc(PortalAuditLog.timestamp)).limit(limit)

    logs = (await db.execute(stmt)).scalars().all()
    results = []
    for l in logs:
        user_email = None
        if l.user_id:
            u = await db.get(PortalUser, l.user_id)
            if u:
                user_email = u.email

        results.append(
            PortalAuditLogResponse(
                id=l.id,
                user_id=l.user_id,
                user_email=user_email,
                company_id=l.company_id,
                action=l.action,
                resource_type=l.resource_type,
                resource_id=l.resource_id,
                details=l.details or {},
                ip_address=l.ip_address,
                timestamp=l.timestamp,
            )
        )
    return results
