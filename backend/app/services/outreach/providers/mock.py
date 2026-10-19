import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.services.outreach.providers.base import BaseEmailProvider

logger = logging.getLogger(__name__)


class MockEmailProvider(BaseEmailProvider):
    """
    Mock Email Provider strictly used in automated testing and controlled local dry-runs.
    Never transmits external network packets.
    """

    provider_name: str = "Mock"

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    def is_configured(self) -> bool:
        return True

    def get_missing_configuration(self) -> list[str]:
        return []

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        sender_email: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        msg_id = f"mock-msg-{uuid.uuid4()}"
        thread_id = in_reply_to or f"mock-thread-{uuid.uuid4()}"
        record = {
            "provider_message_id": msg_id,
            "provider_thread_id": thread_id,
            "to_email": to_email,
            "sender_email": sender_email or "outreach@prospectos.local",
            "subject": subject,
            "body_text": body_text,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "SENT"
        }
        self.sent_messages.append(record)
        logger.info(f"[MOCK EMAIL SENT] To: {to_email} | Subject: {subject} | ID: {msg_id}")
        return {
            "success": True,
            "provider_message_id": msg_id,
            "provider_thread_id": thread_id,
            "error": None
        }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        for msg in self.sent_messages:
            if msg["provider_message_id"] == provider_message_id:
                return {"status": msg["status"], "error": None}
        return {"status": "DELIVERED", "error": None}

    def clear(self):
        self.sent_messages.clear()
