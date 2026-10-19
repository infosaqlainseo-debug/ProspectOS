import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models import (
    OutreachDraft, OutreachCampaign, OutreachMessage,
    OutreachSuppression, CompanyContact, Company
)
from app.schemas.outreach import SendDraftResult
from app.services.outreach.providers.registry import email_registry
from app.services.outreach.contacts import ContactResearcher

logger = logging.getLogger(__name__)


class OutreachSenderService:
    """
    Enforces strict safety rules, human authorization gates, opt-out suppression,
    rate limiting, and duplicate prevention before dispatching any outreach message.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_draft(
        self,
        draft_id: uuid.UUID,
        authorized_by: str = "human_reviewer",
        override_recipient_email: Optional[str] = None
    ) -> SendDraftResult:
        draft = await self.session.get(OutreachDraft, draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        # GATE 1: Explicit Human Approval Check
        if draft.approval_status != "APPROVED":
            raise ValueError(
                f"Draft {draft_id} cannot be sent: approval_status is '{draft.approval_status}'. "
                "Explicit human approval (approval_status == 'APPROVED') is mandatory before sending."
            )

        # GATE 2: Not Already Sent Check
        if draft.status == "SENT":
            raise ValueError(f"Draft {draft_id} has already been sent at {draft.sent_at}. Duplicate sends are blocked.")

        target_email = (override_recipient_email or draft.recipient_email or "").strip().lower()

        # GATE 3: Valid Recipient Email Check
        if not ContactResearcher.is_valid_email(target_email):
            raise ValueError(f"Recipient email '{target_email}' is invalid.")

        target_domain = target_email.split('@')[1] if '@' in target_email else ""

        # GATE 4: Opt-Out / Suppression Check
        stmt_supp = select(OutreachSuppression).where(
            (OutreachSuppression.email == target_email) | (OutreachSuppression.domain == target_domain)
        )
        suppression = (await self.session.execute(stmt_supp)).scalars().first()
        if suppression:
            draft.status = "CANCELLED"
            draft.error_message = f"Suppressed: Recipient or domain is on suppression list (Reason: {suppression.reason})."
            await self.session.commit()
            raise ValueError(f"Send blocked: '{target_email}' is on the opt-out / suppression list ({suppression.reason}).")

        # GATE 5: Contact Record Opt-Out Check
        if draft.contact_id:
            contact = await self.session.get(CompanyContact, draft.contact_id)
            if contact and contact.opt_out:
                draft.status = "CANCELLED"
                draft.error_message = "Suppressed: Contact has opted out."
                await self.session.commit()
                raise ValueError(f"Send blocked: Contact {contact.id} has opted out.")

        # GATE 6: Duplicate Send Prevention Cooldown
        # Check if any outreach message was sent to this recipient in the last 7 days
        cooldown_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        stmt_dup = select(OutreachMessage).where(
            OutreachMessage.recipient_email == target_email,
            OutreachMessage.sent_at >= cooldown_cutoff,
            OutreachMessage.status.in_(["SENT", "DELIVERED"])
        )
        recent_msg = (await self.session.execute(stmt_dup)).scalars().first()
        if recent_msg and not draft.is_follow_up:
            raise ValueError(
                f"Duplicate send prevented: An email was already sent to '{target_email}' "
                f"on {recent_msg.sent_at}. Minimum cooldown between initial cold outreaches is 7 days."
            )

        # GATE 7: Campaign Daily Send Limit
        campaign: Optional[OutreachCampaign] = None
        if draft.campaign_id:
            campaign = await self.session.get(OutreachCampaign, draft.campaign_id)
            if campaign:
                today_midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                stmt_cnt = select(func.count(OutreachMessage.id)).where(
                    OutreachMessage.campaign_id == campaign.id,
                    OutreachMessage.sent_at >= today_midnight
                )
                sent_today = (await self.session.execute(stmt_cnt)).scalar() or 0
                if sent_today >= campaign.daily_send_limit:
                    raise ValueError(
                        f"Campaign '{campaign.name}' daily limit reached ({sent_today}/{campaign.daily_send_limit} sent today). "
                        "Send aborted to respect rate limits."
                    )

        # GATE 8: Email Provider Configuration
        provider = email_registry.get_active_provider()
        if not provider.is_configured():
            missing = provider.get_missing_configuration()
            err_msg = (
                f"PROVIDER_NOT_CONFIGURED: Email provider '{provider.provider_name}' is not configured. "
                f"Missing environment settings: {', '.join(missing)}. "
                "Please configure an authorized email provider before attempting live sends."
            )
            draft.status = "FAILED"
            draft.error_message = err_msg
            await self.session.commit()
            return SendDraftResult(
                success=False,
                draft_id=draft.id,
                message_id=None,
                provider=provider.provider_name,
                provider_message_id=None,
                recipient_email=target_email,
                status="FAILED",
                error=err_msg
            )

        # EXECUTION: Transmit email via provider
        logger.info(f"Transmitting approved draft {draft.id} to {target_email} via provider {provider.provider_name}...")
        send_res = await provider.send_email(
            to_email=target_email,
            subject=draft.subject_line,
            body_text=draft.body_text,
            body_html=draft.body_html
        )

        if not send_res.get("success"):
            err = send_res.get("error", "Unknown transmission error")
            draft.status = "FAILED"
            draft.error_message = err
            await self.session.commit()
            return SendDraftResult(
                success=False,
                draft_id=draft.id,
                message_id=None,
                provider=provider.provider_name,
                provider_message_id=None,
                recipient_email=target_email,
                status="FAILED",
                error=err
            )

        # POST-SEND RECORDING: Record immutable OutreachMessage and update draft status
        now_utc = datetime.now(timezone.utc)
        sender_email = (
            getattr(provider, "sender_email", None)
            or getattr(provider, "from_email", None)
            or "outreach@prospectos.local"
        )

        message = OutreachMessage(
            draft_id=draft.id,
            campaign_id=draft.campaign_id,
            company_id=draft.company_id,
            contact_id=draft.contact_id,
            provider=provider.provider_name,
            provider_message_id=send_res.get("provider_message_id"),
            provider_thread_id=send_res.get("provider_thread_id"),
            sender_email=sender_email,
            recipient_email=target_email,
            subject_line=draft.subject_line,
            body_text=draft.body_text,
            status="SENT",
            sent_at=now_utc
        )
        self.session.add(message)

        draft.status = "SENT"
        draft.sent_at = now_utc
        draft.error_message = None

        # GATE 9: Automatic Follow-Up Sequence Scheduling (if campaign configured)
        if campaign and not draft.is_follow_up and campaign.max_follow_ups > 0:
            follow_up_draft = OutreachDraft(
                campaign_id=campaign.id,
                company_id=draft.company_id,
                contact_id=draft.contact_id,
                recipient_email=target_email,
                recipient_name=draft.recipient_name,
                subject_line=f"Following up: {draft.subject_line}",
                body_text=(
                    f"Hi {draft.recipient_name or 'there'},\n\n"
                    f"I wanted to follow up on my previous note regarding {draft.subject_line}. "
                    "Did you have an opportunity to review our tailored media plan and opportunity findings?\n\n"
                    "Best regards,\nProspectOS Growth Team"
                ),
                call_to_action=draft.call_to_action,
                prospect_summary=draft.prospect_summary,
                evidence_citations=draft.evidence_citations,
                status="PENDING_APPROVAL",
                approval_status="UNAPPROVED", # Strictly requires review before follow-up send!
                is_follow_up=True,
                sequence_step=2,
                parent_draft_id=draft.id,
                scheduled_send_at=now_utc + timedelta(days=campaign.follow_up_delay_days)
            )
            self.session.add(follow_up_draft)
            logger.info(f"Scheduled follow-up draft for {target_email} in {campaign.follow_up_delay_days} days.")

        await self.session.commit()
        await self.session.refresh(message)
        await self.session.refresh(draft)

        return SendDraftResult(
            success=True,
            draft_id=draft.id,
            message_id=message.id,
            provider=provider.provider_name,
            provider_message_id=message.provider_message_id,
            recipient_email=target_email,
            status="SENT",
            error=None
        )

    async def cancel_follow_ups(self, company_id: uuid.UUID, recipient_email: str, reason: str):
        """Cancels all pending or scheduled follow-ups upon reply, bounce, unsubscribe, or cancellation."""
        target_email = recipient_email.strip().lower()
        stmt = select(OutreachDraft).where(
            OutreachDraft.company_id == company_id,
            OutreachDraft.recipient_email == target_email,
            OutreachDraft.is_follow_up == True,
            OutreachDraft.status.in_(["DRAFT", "PENDING_APPROVAL", "APPROVED", "QUEUED"])
        )
        follow_ups = (await self.session.execute(stmt)).scalars().all()
        for f in follow_ups:
            f.status = "CANCELLED"
            f.error_message = f"Sequence stopped: {reason}"
        await self.session.commit()
        logger.info(f"Cancelled {len(follow_ups)} follow-up drafts for {target_email} (Reason: {reason})")

    async def handle_opt_out(self, email: str, domain: Optional[str] = None, reason: str = "MANUAL_OPTOUT"):
        """Suppresses email and domain, flags contacts, and cancels all pending drafts."""
        clean_email = email.strip().lower()
        clean_domain = (domain or clean_email.split('@')[1] if '@' in clean_email else "").lower()

        # 1. Add to suppression table
        stmt_supp = select(OutreachSuppression).where(OutreachSuppression.email == clean_email)
        existing_supp = (await self.session.execute(stmt_supp)).scalars().first()
        if not existing_supp:
            supp = OutreachSuppression(
                email=clean_email,
                domain=clean_domain,
                reason=reason,
                source="outreach_engine",
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(supp)

        # 2. Update contacts
        stmt_contacts = select(CompanyContact).where(CompanyContact.email == clean_email)
        contacts = (await self.session.execute(stmt_contacts)).scalars().all()
        for c in contacts:
            c.opt_out = True
            c.opt_out_at = datetime.now(timezone.utc)

        # 3. Cancel all pending drafts
        stmt_drafts = select(OutreachDraft).where(
            OutreachDraft.recipient_email == clean_email,
            OutreachDraft.status.in_(["DRAFT", "PENDING_APPROVAL", "APPROVED", "QUEUED"])
        )
        drafts = (await self.session.execute(stmt_drafts)).scalars().all()
        for d in drafts:
            d.status = "CANCELLED"
            d.error_message = f"Suppressed due to opt-out: {reason}"

        await self.session.commit()
        logger.info(f"Suppressed {clean_email} and cancelled {len(drafts)} pending drafts.")
