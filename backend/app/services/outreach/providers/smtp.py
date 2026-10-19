import asyncio
import smtplib
import uuid
import logging
from email.message import EmailMessage
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.services.outreach.providers.base import BaseEmailProvider

logger = logging.getLogger(__name__)


class SMTPProvider(BaseEmailProvider):
    """Standard SMTP email delivery provider."""

    provider_name: str = "SMTP"

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.use_tls = settings.SMTP_USE_TLS

    def is_configured(self) -> bool:
        return bool(self.host and self.port and self.username and self.password and self.from_email)

    def get_missing_configuration(self) -> List[str]:
        missing = []
        if not self.host:
            missing.append("SMTP_HOST")
        if not self.port:
            missing.append("SMTP_PORT")
        if not self.username:
            missing.append("SMTP_USERNAME")
        if not self.password:
            missing.append("SMTP_PASSWORD")
        if not self.from_email:
            missing.append("SMTP_FROM_EMAIL")
        return missing

    def _sync_send(self, msg: EmailMessage) -> None:
        if self.use_tls:
            server = smtplib.SMTP(self.host, self.port, timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
        
        server.login(self.username, self.password)
        server.send_message(msg)
        server.quit()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        sender_email: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "provider_message_id": None,
                "provider_thread_id": None,
                "error": "PROVIDER_NOT_CONFIGURED"
            }

        msg = EmailMessage()
        msg["From"] = sender_email or self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg_id = f"<{uuid.uuid4()}@{self.host}>"
        msg["Message-ID"] = msg_id

        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to

        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        try:
            await asyncio.to_thread(self._sync_send, msg)
            return {
                "success": True,
                "provider_message_id": msg_id,
                "provider_thread_id": in_reply_to or msg_id,
                "error": None
            }
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return {
                "success": False,
                "provider_message_id": None,
                "provider_thread_id": None,
                "error": str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        return {"status": "SENT", "error": None}
