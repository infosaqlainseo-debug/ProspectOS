import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Company, WebsiteScan, CompanyContact, Discovery
from app.schemas.outreach import ContactCreate

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

# Standard non-business or file extensions to ignore
IGNORE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf', '.css', '.js')
IGNORE_DOMAINS = ('example.com', 'yourdomain.com', 'email.com', 'sentry.io', 'domain.com')


class ContactResearcher:
    """Discovers, validates, and records legitimate public business contacts for companies."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def is_valid_email(email: str) -> bool:
        if not email or len(email) > 254:
            return False
        if any(email.lower().endswith(ext) for ext in IGNORE_EXTENSIONS):
            return False
        parts = email.split('@')
        if len(parts) != 2:
            return False
        domain = parts[1].lower()
        if domain in IGNORE_DOMAINS or '.' not in domain:
            return False
        return bool(EMAIL_REGEX.match(email))

    async def discover_company_contacts(self, company_id: uuid.UUID) -> List[CompanyContact]:
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        canonical_domain = (company.canonical_domain or "").lower()
        discovered_contacts: List[Dict[str, Any]] = []

        # 1. Inspect existing WebsiteScans for mailto: or text emails
        stmt_scans = (
            select(WebsiteScan)
            .where(WebsiteScan.company_id == company_id)
            .order_by(WebsiteScan.scanned_at.desc())
            .limit(3)
        )
        scans = (await self.session.execute(stmt_scans)).scalars().all()

        for scan in scans:
            scan_url = scan.url or f"https://{canonical_domain}"
            # Check meta tags, descriptions, open_graph, twitter_card
            text_blocks = [
                scan.meta_description or "",
                scan.title or "",
            ]
            if scan.open_graph and isinstance(scan.open_graph, dict):
                text_blocks.extend(str(v) for v in scan.open_graph.values())
            if scan.twitter_card and isinstance(scan.twitter_card, dict):
                text_blocks.extend(str(v) for v in scan.twitter_card.values())

            full_text = " ".join(text_blocks)
            found_emails = EMAIL_REGEX.findall(full_text)
            for raw_email in found_emails:
                clean_email = raw_email.lower().strip()
                if self.is_valid_email(clean_email):
                    email_domain = clean_email.split('@')[1]
                    is_match = canonical_domain and (canonical_domain in email_domain or email_domain in canonical_domain)
                    discovered_contacts.append({
                        "email": clean_email,
                        "source_type": "WEBSITE_PAGE",
                        "source_url": scan_url,
                        "verification_status": "VERIFIED" if is_match else "UNVERIFIED",
                        "confidence": 0.85 if is_match else 0.50,
                        "notes": "Extracted from website metadata scan."
                    })

        # 2. Check security.txt if canonical domain is available
        if canonical_domain:
            security_urls = [
                f"https://{canonical_domain}/.well-known/security.txt",
                f"https://{canonical_domain}/security.txt"
            ]
            for sec_url in security_urls:
                try:
                    async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                        resp = await client.get(sec_url)
                        if resp.status_code == 200 and "Contact:" in resp.text:
                            for line in resp.text.splitlines():
                                if line.lower().startswith("contact:"):
                                    sec_emails = EMAIL_REGEX.findall(line)
                                    for se in sec_emails:
                                        clean_se = se.lower().strip()
                                        if self.is_valid_email(clean_se):
                                            discovered_contacts.append({
                                                "email": clean_se,
                                                "source_type": "SECURITY_TXT",
                                                "source_url": sec_url,
                                                "verification_status": "VERIFIED",
                                                "confidence": 0.95,
                                                "job_title": "Security & Operations Team",
                                                "notes": "Verified from public security.txt standard file."
                                            })
                            break
                except Exception:
                    pass

        # 3. Check GitHub Organizations discovery source
        stmt_disc = select(Discovery).where(Discovery.company_id == company_id).limit(1)
        discovery = (await self.session.execute(stmt_disc)).scalars().first()
        if discovery and discovery.source_url:
            disc_emails = EMAIL_REGEX.findall(discovery.source_url)
            for de in disc_emails:
                clean_de = de.lower().strip()
                if self.is_valid_email(clean_de):
                    discovered_contacts.append({
                        "email": clean_de,
                        "source_type": "GITHUB_PUBLIC",
                        "source_url": discovery.source_url,
                        "verification_status": "VERIFIED",
                        "confidence": 0.90,
                        "notes": "Discovered via public GitHub Organization profile."
                    })

        # 4. If no contacts discovered at all, create an inferred official contact
        # clearly marked as INFERRED with low confidence so nothing is fabricated
        if not discovered_contacts and canonical_domain:
            inferred_email = f"contact@{canonical_domain}"
            discovered_contacts.append({
                "email": inferred_email,
                "source_type": "INFERRED_ROLE",
                "source_url": f"https://{canonical_domain}",
                "verification_status": "INFERRED",
                "confidence": 0.40,
                "job_title": "General Inquiries",
                "notes": f"Standard public role contact inferred from canonical domain {canonical_domain}."
            })

        # Deduplicate and persist in database
        persisted_contacts: List[CompanyContact] = []
        seen_emails = set()

        for contact_data in discovered_contacts:
            email_addr = contact_data["email"]
            if email_addr in seen_emails:
                continue
            seen_emails.add(email_addr)

            # Check if contact already exists in database
            stmt_existing = select(CompanyContact).where(
                CompanyContact.company_id == company_id,
                CompanyContact.email == email_addr
            )
            existing = (await self.session.execute(stmt_existing)).scalars().first()
            if existing:
                persisted_contacts.append(existing)
                continue

            new_contact = CompanyContact(
                company_id=company_id,
                email=email_addr,
                full_name=contact_data.get("full_name"),
                job_title=contact_data.get("job_title"),
                source_type=contact_data["source_type"],
                source_url=contact_data.get("source_url"),
                retrieval_timestamp=datetime.now(timezone.utc),
                verification_status=contact_data.get("verification_status", "UNVERIFIED"),
                confidence=contact_data.get("confidence", 0.5),
                is_primary=(len(persisted_contacts) == 0),
                notes=contact_data.get("notes")
            )
            self.session.add(new_contact)
            persisted_contacts.append(new_contact)

        await self.session.commit()
        for c in persisted_contacts:
            await self.session.refresh(c)

        return persisted_contacts
