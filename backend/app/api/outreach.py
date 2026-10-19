import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models import (
    CompanyContact, OutreachCampaign, OutreachDraft,
    OutreachMessage, OutreachSuppression, Company
)
from app.schemas.outreach import (
    ContactCreate, ContactUpdate, ContactResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    DraftCreate, DraftUpdate, DraftResponse,
    DraftGenerateRequest, DraftPreviewResponse,
    DraftApproveRequest, DraftRejectRequest,
    SendDraftRequest, SendDraftResult,
    SuppressionCreate, SuppressionResponse,
    OutreachMessageResponse, EmailProviderStatusResponse
)
from app.services.outreach.contacts import ContactResearcher
from app.services.outreach.personalization import OutreachPersonalizationEngine
from app.services.outreach.sender import OutreachSenderService
from app.services.outreach.providers.registry import email_registry

router = APIRouter(prefix="/outreach", tags=["outreach"])


# ============================================================================
# CONTACTS ENDPOINTS
# ============================================================================

@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    company_id: Optional[uuid.UUID] = None,
    verification_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CompanyContact)
    if company_id:
        stmt = stmt.where(CompanyContact.company_id == company_id)
    if verification_status:
        stmt = stmt.where(CompanyContact.verification_status == verification_status)
    stmt = stmt.order_by(CompanyContact.created_at.desc())
    results = await db.execute(stmt)
    return results.scalars().all()


@router.post("/contacts", response_model=ContactResponse)
async def create_contact(payload: ContactCreate, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contact = CompanyContact(
        company_id=payload.company_id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=payload.full_name or f"{payload.first_name or ''} {payload.last_name or ''}".strip() or None,
        job_title=payload.job_title,
        department=payload.department,
        phone=payload.phone,
        linkedin_url=payload.linkedin_url,
        source_type=payload.source_type,
        source_url=payload.source_url,
        retrieval_timestamp=datetime.now(timezone.utc),
        verification_status=payload.verification_status,
        confidence=payload.confidence,
        is_primary=payload.is_primary,
        opt_out=payload.opt_out,
        notes=payload.notes
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.post("/contacts/discover/{company_id}", response_model=List[ContactResponse])
async def discover_company_contacts(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    researcher = ContactResearcher(db)
    try:
        contacts = await researcher.discover_company_contacts(company_id)
        return contacts
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/contacts/{id}", response_model=ContactResponse)
async def get_contact(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contact = await db.get(CompanyContact, id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/contacts/{id}", response_model=ContactResponse)
async def update_contact(id: uuid.UUID, payload: ContactUpdate, db: AsyncSession = Depends(get_db)):
    contact = await db.get(CompanyContact, id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, val)

    if payload.opt_out is True and not contact.opt_out_at:
        contact.opt_out_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(contact)
    return contact


# ============================================================================
# CAMPAIGNS ENDPOINTS
# ============================================================================

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    stmt = select(OutreachCampaign).order_by(OutreachCampaign.created_at.desc())
    results = await db.execute(stmt)
    return results.scalars().all()


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(payload: CampaignCreate, db: AsyncSession = Depends(get_db)):
    campaign = OutreachCampaign(**payload.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/campaigns/{id}", response_model=CampaignResponse)
async def get_campaign(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(OutreachCampaign, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/campaigns/{id}", response_model=CampaignResponse)
async def update_campaign(id: uuid.UUID, payload: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(OutreachCampaign, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, val)

    await db.commit()
    await db.refresh(campaign)
    return campaign


# ============================================================================
# DRAFTS & PERSONALIZATION ENDPOINTS
# ============================================================================

@router.get("/drafts", response_model=List[DraftResponse])
async def list_drafts(
    company_id: Optional[uuid.UUID] = None,
    campaign_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OutreachDraft)
    if company_id:
        stmt = stmt.where(OutreachDraft.company_id == company_id)
    if campaign_id:
        stmt = stmt.where(OutreachDraft.campaign_id == campaign_id)
    if status:
        stmt = stmt.where(OutreachDraft.status == status)
    if approval_status:
        stmt = stmt.where(OutreachDraft.approval_status == approval_status)
    stmt = stmt.order_by(OutreachDraft.created_at.desc())
    results = await db.execute(stmt)
    return results.scalars().all()


@router.post("/drafts/generate")
async def generate_draft(payload: DraftGenerateRequest, db: AsyncSession = Depends(get_db)):
    engine = OutreachPersonalizationEngine(db)
    try:
        result = await engine.generate_draft(
            company_id=payload.company_id,
            contact_id=payload.contact_id,
            campaign_id=payload.campaign_id,
            include_media_plan=payload.include_media_plan,
            save=payload.save_draft
        )
        if payload.save_draft:
            return DraftResponse.model_validate(result)
        else:
            company = await db.get(Company, payload.company_id)
            return DraftPreviewResponse(
                company_id=payload.company_id,
                company_name=company.company_name or "Unknown",
                canonical_domain=company.canonical_domain,
                recipient_email=result["recipient_email"],
                recipient_name=result["recipient_name"],
                subject_line=result["subject_line"],
                body_text=result["body_text"],
                body_html=result["body_html"],
                call_to_action=result["call_to_action"],
                prospect_summary=result["prospect_summary"],
                evidence_citations=result["evidence_citations"]
            )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/drafts/{id}", response_model=DraftResponse)
async def get_draft(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    draft = await db.get(OutreachDraft, id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.put("/drafts/{id}", response_model=DraftResponse)
async def update_draft(id: uuid.UUID, payload: DraftUpdate, db: AsyncSession = Depends(get_db)):
    draft = await db.get(OutreachDraft, id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == "SENT":
        raise HTTPException(status_code=400, detail="Cannot edit a draft that has already been sent.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, val)

    # Editing resets approval if it was previously approved to ensure review of changes
    if draft.approval_status == "APPROVED":
        draft.approval_status = "UNAPPROVED"
        draft.status = "DRAFT"

    await db.commit()
    await db.refresh(draft)
    return draft


# ============================================================================
# HUMAN APPROVAL BOUNDARY ENDPOINTS
# ============================================================================

@router.post("/drafts/{id}/approve", response_model=DraftResponse)
async def approve_draft(id: uuid.UUID, payload: DraftApproveRequest, db: AsyncSession = Depends(get_db)):
    draft = await db.get(OutreachDraft, id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == "SENT":
        raise HTTPException(status_code=400, detail="Draft has already been sent.")

    draft.approval_status = "APPROVED"
    draft.status = "APPROVED"
    draft.approved_by = payload.approved_by
    draft.approved_at = datetime.now(timezone.utc)
    draft.rejection_reason = None

    await db.commit()
    await db.refresh(draft)
    return draft


@router.post("/drafts/{id}/reject", response_model=DraftResponse)
async def reject_draft(id: uuid.UUID, payload: DraftRejectRequest, db: AsyncSession = Depends(get_db)):
    draft = await db.get(OutreachDraft, id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.approval_status = "REJECTED"
    draft.status = "REJECTED"
    draft.rejection_reason = payload.reason

    await db.commit()
    await db.refresh(draft)
    return draft


# ============================================================================
# SENDING CONTROLS (EXPLICIT HUMAN AUTHORIZATION REQUIRED)
# ============================================================================

@router.post("/drafts/{id}/send", response_model=SendDraftResult)
async def send_draft(id: uuid.UUID, payload: SendDraftRequest, db: AsyncSession = Depends(get_db)):
    sender_svc = OutreachSenderService(db)
    try:
        result = await sender_svc.send_draft(
            draft_id=id,
            authorized_by=payload.authorized_by,
            override_recipient_email=payload.override_recipient_email
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# ============================================================================
# SUPPRESSION & AUDIT HISTORY
# ============================================================================

@router.get("/suppressions", response_model=List[SuppressionResponse])
async def list_suppressions(db: AsyncSession = Depends(get_db)):
    stmt = select(OutreachSuppression).order_by(OutreachSuppression.created_at.desc())
    results = await db.execute(stmt)
    return results.scalars().all()


@router.post("/suppressions", response_model=SuppressionResponse)
async def add_suppression(payload: SuppressionCreate, db: AsyncSession = Depends(get_db)):
    sender_svc = OutreachSenderService(db)
    await sender_svc.handle_opt_out(
        email=payload.email,
        domain=payload.domain,
        reason=payload.reason
    )
    stmt = select(OutreachSuppression).where(OutreachSuppression.email == payload.email.lower().strip())
    supp = (await db.execute(stmt)).scalars().first()
    return supp


@router.get("/messages", response_model=List[OutreachMessageResponse])
async def list_messages(
    company_id: Optional[uuid.UUID] = None,
    campaign_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OutreachMessage)
    if company_id:
        stmt = stmt.where(OutreachMessage.company_id == company_id)
    if campaign_id:
        stmt = stmt.where(OutreachMessage.campaign_id == campaign_id)
    stmt = stmt.order_by(OutreachMessage.sent_at.desc())
    results = await db.execute(stmt)
    return results.scalars().all()


@router.get("/provider/status", response_model=EmailProviderStatusResponse)
async def get_provider_status():
    return email_registry.get_status()
