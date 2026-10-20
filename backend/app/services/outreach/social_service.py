import uuid
import re
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import (
    SocialConnection, SocialMessageLog, Company, CompanyContact,
    WebsiteScan, OpportunityProfile, SEOMetric, CRMActivity
)
from app.services.gdrive.service import _encrypt_token, _decrypt_token
from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_CHANNELS = ["FACEBOOK", "INSTAGRAM", "WHATSAPP"]

def clean_phone_for_whatsapp(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    # Strip non-digits
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return digits
    return None


class SocialOutreachService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_connections(self) -> List[Dict[str, Any]]:
        stmt = select(SocialConnection)
        existing = {conn.channel: conn for conn in (await self.db.execute(stmt)).scalars().all()}
        
        result = []
        for channel in SUPPORTED_CHANNELS:
            conn = existing.get(channel)
            if conn:
                result.append({
                    "channel": conn.channel,
                    "account_name": conn.account_name,
                    "account_id": conn.account_id,
                    "phone_number": conn.phone_number,
                    "is_connected": conn.is_connected,
                    "permissions": conn.permissions or [],
                    "messaging_enabled": conn.messaging_enabled,
                    "token_valid": bool(conn.access_token_encrypted),
                    "token_expires_at": conn.token_expires_at.isoformat() if conn.token_expires_at else None,
                    "last_successful_operation_at": conn.last_successful_operation_at.isoformat() if conn.last_successful_operation_at else None,
                    "configuration_error": conn.configuration_error,
                    "settings_data": conn.settings_data or {}
                })
            else:
                result.append({
                    "channel": channel,
                    "account_name": None,
                    "account_id": None,
                    "phone_number": None,
                    "is_connected": False,
                    "permissions": [],
                    "messaging_enabled": False,
                    "token_valid": False,
                    "token_expires_at": None,
                    "last_successful_operation_at": None,
                    "configuration_error": "Not configured",
                    "settings_data": {}
                })
        return result

    async def update_connection(
        self,
        channel: str,
        account_name: Optional[str],
        account_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        access_token: Optional[str] = None,
        messaging_enabled: bool = False,
        settings_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ch_upper = channel.upper()
        if ch_upper not in SUPPORTED_CHANNELS:
            raise ValueError(f"Unsupported channel {channel}. Must be one of {SUPPORTED_CHANNELS}")

        stmt = select(SocialConnection).where(SocialConnection.channel == ch_upper)
        conn = (await self.db.execute(stmt)).scalars().first()

        if not conn:
            conn = SocialConnection(channel=ch_upper)
            self.db.add(conn)

        conn.account_name = account_name
        conn.account_id = account_id
        conn.phone_number = phone_number
        conn.is_connected = True
        conn.messaging_enabled = messaging_enabled
        if access_token:
            conn.access_token_encrypted = _encrypt_token(access_token)
            conn.token_expires_at = datetime.now(timezone.utc) + timedelta(days=60)
        conn.configuration_error = None
        conn.last_successful_operation_at = datetime.now(timezone.utc)
        if settings_data:
            conn.settings_data = settings_data

        await self.db.commit()
        await self.db.refresh(conn)
        return {"status": "connected", "channel": ch_upper, "account_name": account_name}

    async def disconnect_connection(self, channel: str) -> Dict[str, Any]:
        ch_upper = channel.upper()
        stmt = select(SocialConnection).where(SocialConnection.channel == ch_upper)
        conn = (await self.db.execute(stmt)).scalars().first()
        if conn:
            conn.is_connected = False
            conn.messaging_enabled = False
            conn.access_token_encrypted = None
            conn.configuration_error = "Disconnected by user."
            await self.db.commit()
        return {"status": "disconnected", "channel": ch_upper}

    async def generate_multi_channel_drafts(self, company_id: uuid.UUID) -> Dict[str, Any]:
        """Generates evidence-grounded drafts across Facebook, Instagram, WhatsApp, and Email."""
        company = await self.db.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # 1. Fetch website scan
        stmt_scan = select(WebsiteScan).where(WebsiteScan.company_id == company.id).order_by(desc(WebsiteScan.scanned_at)).limit(1)
        scan = (await self.db.execute(stmt_scan)).scalars().first()

        # 2. Fetch Opportunity Profile
        stmt_opp = select(OpportunityProfile).where(OpportunityProfile.company_id == company.id).order_by(desc(OpportunityProfile.calculation_timestamp)).limit(1)
        opp = (await self.db.execute(stmt_opp)).scalars().first()

        # 3. Fetch Ahrefs metrics
        stmt_m = select(SEOMetric).where(SEOMetric.company_id == company.id).order_by(desc(SEOMetric.retrieved_at)).limit(5)
        metrics = (await self.db.execute(stmt_m)).scalars().all()
        dr_metric = next((m for m in metrics if m.metric_name.lower() in ["domain_rating", "dr"]), None)

        company_name = company.company_name or company.canonical_domain or "your company"
        industry = company.industry or "commercial e-commerce"
        domain = company.canonical_domain or (scan.final_url if scan else "your website")

        # Verified Evidence
        evidence_items = []
        if scan:
            if scan.title:
                evidence_items.append(f"Public website title: '{scan.title}'")
            if not scan.h1 or len(scan.h1) == 0:
                evidence_items.append("H1 headings are currently missing from the homepage")
            if not scan.https_enabled:
                evidence_items.append("HTTPS security certificate is not properly configured")
            if scan.robots_txt_status and scan.robots_txt_status.upper() not in ["OK", "FOUND"]:
                evidence_items.append(f"Robots.txt status indicates indexing constraints ({scan.robots_txt_status})")
        
        if dr_metric and dr_metric.metric_value is not None:
            evidence_items.append(f"Current measured Ahrefs Domain Rating: {dr_metric.metric_value:.1f}/100")

        if opp and opp.identified_problems:
            evidence_items.extend(opp.identified_problems[:2])

        if not evidence_items:
            evidence_items.append("High expansion opportunity for organic search visibility and Tier-1 editorial backlinks")

        primary_service = opp.recommended_service if opp else "Technical SEO and Link Building"
        recommended_services = company.recommended_services or [primary_service, "Digital PR", "Publisher Placements"]

        # Company Summary
        company_summary = f"{company_name} is an active brand in the {industry} sector operating at {domain}. An analysis of its public web presence shows solid baseline infrastructure with strategic opportunities in {primary_service}."

        # WhatsApp draft
        whatsapp_body = (
            f"Hello {company_name} team,\n\n"
            f"I was reviewing {domain} and noticed your strong presence in {industry}. "
            f"During a recent technical SEO review, our system identified significant growth potential in {primary_service}. "
            f"We have matched your profile with relevant publisher publications in our network that could expand your organic visibility. "
            f"Would you be open to a quick look at the custom audit findings?"
        )
        clean_phone = clean_phone_for_whatsapp(company.whatsapp_number or company.phone_number)
        encoded_wa_text = urllib.parse.quote(whatsapp_body)
        whatsapp_click_url = f"https://wa.me/{clean_phone}?text={encoded_wa_text}" if clean_phone else None

        # Instagram draft (concise direct DM style)
        instagram_body = (
            f"Hey {company_name}! Love what you're doing in {industry}. "
            f"We ran a quick SEO and backlink audit on {domain} and found key opportunities to boost your organic reach through {primary_service}. "
            f"Can we send over a brief report and publisher match preview?"
        )

        # Facebook draft (Page Messenger style)
        facebook_body = (
            f"Hi {company_name} team,\n\n"
            f"We recently analyzed the public search performance of {domain} in the {industry} space. "
            f"We noted actionable areas to enhance your search rankings and high-authority placements ({', '.join(evidence_items[:2])}).\n\n"
            f"Our team at GrokxSEO specializes in verified backlink acquisition and technical audits. Would you like us to share our full audit brief?"
        )

        # Email draft
        email_subject = f"SEO & Editorial Growth Strategy for {company_name}"
        email_body = (
            f"Hi {company_name} team,\n\n"
            f"I was reviewing {company_name} ({domain}) and noticed your presence in the {industry} sector.\n\n"
            f"During an initial website performance check, our system highlighted key areas for expansion in {primary_service}, particularly around:\n"
            + "\n".join([f"• {item}" for item in evidence_items[:3]]) + "\n\n"
            f"We have matched your profile with verified, high-affinity publications in your sector that have audience overlap with your target demographic.\n\n"
            f"Are you open to a brief review of the complete opportunity audit and tailored publisher media plan?\n\n"
            f"Best regards,\nProspectOS Growth Team"
        )

        # Follow-up draft
        followup_body = (
            f"Hi {company_name} team,\n\n"
            f"Following up on our earlier note regarding {domain}. "
            f"We've prepared a concise media plan outline and technical SEO recommendations for your team. "
            f"Let us know if you'd like us to forward the summary."
        )

        return {
            "company_id": str(company.id),
            "company_name": company_name,
            "canonical_domain": domain,
            "industry": industry,
            "company_summary": company_summary,
            "verified_seo_opportunities": evidence_items,
            "recommended_services": recommended_services,
            "drafts": {
                "whatsapp": {
                    "channel": "WHATSAPP",
                    "text": whatsapp_body,
                    "recipient_phone": clean_phone,
                    "click_to_chat_url": whatsapp_click_url,
                    "is_eligible_for_click_to_chat": bool(clean_phone)
                },
                "instagram": {
                    "channel": "INSTAGRAM",
                    "text": instagram_body,
                    "profile_url": company.instagram_url,
                    "is_eligible_for_profile_link": bool(company.instagram_url)
                },
                "facebook": {
                    "channel": "FACEBOOK",
                    "text": facebook_body,
                    "page_url": company.facebook_url,
                    "is_eligible_for_page_link": bool(company.facebook_url)
                },
                "email": {
                    "channel": "EMAIL",
                    "subject": email_subject,
                    "text": email_body,
                    "recipient_email": company.public_email or f"contact@{domain}"
                },
                "follow_up": {
                    "text": followup_body,
                    "recommended_delay_days": 4
                }
            },
            "recommended_next_action": (
                "Open lead WhatsApp click-to-chat link or Facebook Page to send initial introduction" 
                if clean_phone or company.facebook_url else 
                "Review website scan findings and conduct manual social profile discovery"
            )
        }

    async def record_or_send_social_message(
        self,
        company_id: uuid.UUID,
        channel: str,
        message_text: str,
        recipient_identifier: str,
        explicit_user_confirmed: bool = False,
        contact_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Records social outreach touchpoint with user confirmation gates."""
        ch_upper = channel.upper()
        if ch_upper not in SUPPORTED_CHANNELS:
            raise ValueError(f"Unsupported channel {channel}")

        company = await self.db.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # Determine dispatch mode
        # If explicit confirmation is false, status remains PREPARED
        status = "CLICK_TO_CHAT" if ch_upper == "WHATSAPP" else "PREPARED"
        if explicit_user_confirmed:
            status = "SENT"

        click_url = None
        if ch_upper == "WHATSAPP":
            clean_p = clean_phone_for_whatsapp(recipient_identifier)
            if clean_p:
                click_url = f"https://wa.me/{clean_p}?text={urllib.parse.quote(message_text)}"

        log = SocialMessageLog(
            company_id=company.id,
            contact_id=contact_id,
            channel=ch_upper,
            direction="OUTBOUND",
            recipient_identifier=recipient_identifier,
            message_text=message_text,
            status=status,
            click_to_chat_url=click_url,
            explicit_user_confirmed=explicit_user_confirmed
        )
        self.db.add(log)

        # Update CRM Activity
        activity = CRMActivity(
            company_id=company.id,
            activity_type=f"SOCIAL_{ch_upper}_OUTREACH",
            actor="human_reviewer",
            title=f"{ch_upper} outreach {status.lower()}",
            details={
                "channel": ch_upper,
                "recipient": recipient_identifier,
                "status": status,
                "user_confirmed": explicit_user_confirmed
            }
        )
        self.db.add(activity)

        # Progress CRM stage if NEW or QUALIFIED
        if company.sales_stage in ["NEW", "QUALIFIED", "READY_FOR_OUTREACH"]:
            company.sales_stage = "CONTACTED"
            company.stage_updated_at = datetime.now(timezone.utc)
            company.stage_reason = f"Outreach initiated via {ch_upper}"

        await self.db.commit()
        await self.db.refresh(log)

        return {
            "success": True,
            "message_id": str(log.id),
            "status": log.status,
            "channel": ch_upper,
            "click_to_chat_url": click_url,
            "sales_stage": company.sales_stage
        }

    async def list_company_messages(self, company_id: uuid.UUID) -> List[Dict[str, Any]]:
        stmt = (
            select(SocialMessageLog)
            .where(SocialMessageLog.company_id == company_id)
            .order_by(desc(SocialMessageLog.created_at))
        )
        logs = (await self.db.execute(stmt)).scalars().all()
        return [
            {
                "id": str(l.id),
                "channel": l.channel,
                "direction": l.direction,
                "recipient_identifier": l.recipient_identifier,
                "message_text": l.message_text,
                "status": l.status,
                "click_to_chat_url": l.click_to_chat_url,
                "explicit_user_confirmed": l.explicit_user_confirmed,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
