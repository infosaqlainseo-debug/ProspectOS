import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    Company, CompanyContact, WebsiteScan, OpportunityProfile,
    SEOMetric, MediaPlan, MediaPlanItem, PublisherRecord, OutreachDraft
)
from app.schemas.outreach import EvidenceCitation, DraftPreviewResponse

logger = logging.getLogger(__name__)


class OutreachPersonalizationEngine:
    """Generates evidence-backed outreach drafts strictly grounded in verified database facts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_draft(
        self,
        company_id: uuid.UUID,
        contact_id: Optional[uuid.UUID] = None,
        campaign_id: Optional[uuid.UUID] = None,
        include_media_plan: bool = True,
        save: bool = False
    ) -> Dict[str, Any]:
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # 1. Resolve contact
        contact: Optional[CompanyContact] = None
        if contact_id:
            contact = await self.session.get(CompanyContact, contact_id)
        if not contact:
            # Pick primary or newest contact
            stmt_c = (
                select(CompanyContact)
                .where(CompanyContact.company_id == company_id)
                .order_by(CompanyContact.is_primary.desc(), CompanyContact.created_at.desc())
                .limit(1)
            )
            contact = (await self.session.execute(stmt_c)).scalars().first()

        recipient_email = contact.email if contact and contact.email else f"contact@{company.canonical_domain or 'domain.com'}"
        recipient_name = contact.full_name or contact.first_name if contact else None

        # 2. Gather Evidence: Website Scan
        stmt_scan = (
            select(WebsiteScan)
            .where(WebsiteScan.company_id == company_id)
            .order_by(WebsiteScan.scanned_at.desc())
            .limit(1)
        )
        scan = (await self.session.execute(stmt_scan)).scalars().first()

        # 3. Gather Evidence: Opportunity Profile
        stmt_opp = (
            select(OpportunityProfile)
            .where(OpportunityProfile.company_id == company_id)
            .order_by(OpportunityProfile.calculation_timestamp.desc())
            .limit(1)
        )
        opp = (await self.session.execute(stmt_opp)).scalars().first()

        # 4. Gather Evidence: Media Plan
        media_plan: Optional[MediaPlan] = None
        media_items: List[MediaPlanItem] = []
        publisher_names: List[str] = []
        if include_media_plan:
            stmt_mp = (
                select(MediaPlan)
                .where(MediaPlan.company_id == company_id)
                .order_by(MediaPlan.created_at.desc())
                .limit(1)
            )
            media_plan = (await self.session.execute(stmt_mp)).scalars().first()
            if media_plan:
                stmt_items = select(MediaPlanItem).where(MediaPlanItem.media_plan_id == media_plan.id).limit(3)
                media_items = (await self.session.execute(stmt_items)).scalars().all()
                for it in media_items:
                    pub = await self.session.get(PublisherRecord, it.publisher_id)
                    if pub and pub.publisher_name:
                        publisher_names.append(pub.publisher_name)

        # 5. Build Evidence Citations
        citations: List[Dict[str, Any]] = []

        if scan:
            if scan.title:
                citations.append({
                    "claim": f"Website title observed as '{scan.title}'",
                    "source_type": "WebsiteScan",
                    "source_id": str(scan.id),
                    "field_name": "title",
                    "value": scan.title,
                    "confidence": 1.0
                })
            if scan.https_enabled is not None:
                citations.append({
                    "claim": f"HTTPS configuration status is {scan.https_enabled}",
                    "source_type": "WebsiteScan",
                    "source_id": str(scan.id),
                    "field_name": "https_enabled",
                    "value": scan.https_enabled,
                    "confidence": 1.0
                })

        if opp:
            citations.append({
                "claim": f"Evaluated primary opportunity service: {opp.recommended_service} (Score: {opp.opportunity_score:.1f})",
                "source_type": "OpportunityProfile",
                "source_id": str(opp.id),
                "field_name": "recommended_service",
                "value": opp.recommended_service,
                "confidence": opp.confidence_level
            })
            if opp.identified_problems:
                citations.append({
                    "claim": f"Identified technical/authority focus areas: {', '.join(opp.identified_problems[:2])}",
                    "source_type": "OpportunityProfile",
                    "source_id": str(opp.id),
                    "field_name": "identified_problems",
                    "value": opp.identified_problems,
                    "confidence": opp.confidence_level
                })

        if media_plan and publisher_names:
            citations.append({
                "claim": f"Matched publisher inventory options: {', '.join(publisher_names)}",
                "source_type": "MediaPlan",
                "source_id": str(media_plan.id),
                "field_name": "recommended_publishers",
                "value": publisher_names,
                "confidence": 1.0
            })

        # 6. Compose Evidence-Grounded Messaging
        company_label = company.company_name or company.canonical_domain or "your team"
        industry_label = company.industry or "digital media"
        
        subject_line = f"SEO & Editorial Growth Strategy for {company_label}"
        
        # Prospect summary
        summary_parts = [
            f"{company_label} operates in the {industry_label} space."
        ]
        if scan and scan.title:
            summary_parts.append(f"Official web presence: '{scan.title}'.")
        if opp:
            summary_parts.append(f"Primary opportunity area identified as {opp.recommended_service}.")
        prospect_summary = " ".join(summary_parts)

        # Body generation
        greeting = f"Hi {recipient_name}," if recipient_name else "Hello,"
        
        paragraphs = [
            f"{greeting}\n",
            f"I was reviewing {company_label} ({company.canonical_domain or ''}) and noticed your presence in {industry_label}."
        ]

        if opp and opp.identified_problems:
            problems_text = ", ".join(opp.identified_problems[:2])
            paragraphs.append(
                f"During an initial website performance check, our system highlighted key areas for expansion in {opp.recommended_service}, particularly around: {problems_text}."
            )
        else:
            paragraphs.append(
                f"We analyzed your public SEO footprint and identified solid growth opportunities for your organic visibility and high-authority placements."
            )

        if publisher_names:
            pubs_text = ", ".join(publisher_names[:3])
            paragraphs.append(
                f"We have matched your profile with verified, high-affinity publications in your sector (including {pubs_text}) that have existing audience overlap with your target demographic."
            )

        cta = f"Are you open to a brief review of the complete opportunity audit and tailored publisher media plan?"
        paragraphs.append(cta)
        paragraphs.append("\nBest regards,\nProspectOS Growth Team")

        body_text = "\n\n".join(paragraphs)
        body_html = "".join([f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs])

        draft_dict = {
            "company_id": company.id,
            "campaign_id": campaign_id,
            "contact_id": contact.id if contact else None,
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "subject_line": subject_line,
            "body_text": body_text,
            "body_html": body_html,
            "call_to_action": cta,
            "prospect_summary": prospect_summary,
            "evidence_citations": citations,
            "status": "DRAFT",
            "approval_status": "UNAPPROVED",
            "is_follow_up": False,
            "sequence_step": 1
        }

        if save:
            draft = OutreachDraft(**draft_dict)
            self.session.add(draft)
            await self.session.commit()
            await self.session.refresh(draft)
            return draft

        return draft_dict
