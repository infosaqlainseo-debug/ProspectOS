import base64
import logging
from email.message import EmailMessage
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings
from app.services.outreach.providers.base import BaseEmailProvider

logger = logging.getLogger(__name__)


class GmailProvider(BaseEmailProvider):
    """Google Workspace / Gmail API v1 email delivery provider."""

    provider_name: str = "Gmail"

    def __init__(self):
        self.client_id = settings.GMAIL_CLIENT_ID
        self.client_secret = settings.GMAIL_CLIENT_SECRET
        self.refresh_token = settings.GMAIL_REFRESH_TOKEN
        self.sender_email = settings.GMAIL_SENDER_EMAIL

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token and self.sender_email)

    def get_missing_configuration(self) -> List[str]:
        missing = []
        if not self.client_id:
            missing.append("GMAIL_CLIENT_ID")
        if not self.client_secret:
            missing.append("GMAIL_CLIENT_SECRET")
        if not self.refresh_token:
            missing.append("GMAIL_REFRESH_TOKEN")
        if not self.sender_email:
            missing.append("GMAIL_SENDER_EMAIL")
        return missing

    async def _get_access_token(self) -> Optional[str]:
        if not self.is_configured():
            return None
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(token_url, data=data)
            if resp.status_code == 200:
                return resp.json().get("access_token")
            logger.error(f"Gmail token refresh failed with status {resp.status_code}: {resp.text}")
            return None

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

        access_token = await self._get_access_token()
        if not access_token:
            return {
                "success": False,
                "provider_message_id": None,
                "provider_thread_id": None,
                "error": "AUTHENTICATION_FAILED"
            }

        from_addr = sender_email or self.sender_email

        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_email
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to

        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {"raw": raw_b64}
        if in_reply_to:
            payload["threadId"] = in_reply_to

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(send_url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    return {
                        "success": True,
                        "provider_message_id": data.get("id"),
                        "provider_thread_id": data.get("threadId"),
                        "error": None
                    }
                else:
                    logger.error(f"Gmail send API error {resp.status_code}: {resp.text}")
                    return {
                        "success": False,
                        "provider_message_id": None,
                        "provider_thread_id": None,
                        "error": f"GMAIL_API_ERROR_{resp.status_code}: {resp.text[:200]}"
                    }
        except Exception as e:
            logger.error(f"Exception during Gmail send: {e}")
            return {
                "success": False,
                "provider_message_id": None,
                "provider_thread_id": None,
                "error": str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        return {"status": "SENT", "error": None}
