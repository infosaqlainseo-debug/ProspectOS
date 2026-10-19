import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.services.outreach.providers.base import BaseEmailProvider
from app.services.outreach.providers.mock import MockEmailProvider
from app.services.outreach.providers.gmail import GmailProvider
from app.services.outreach.providers.smtp import SMTPProvider

logger = logging.getLogger(__name__)


class UnconfiguredEmailProvider(BaseEmailProvider):
    provider_name: str = "None (Unconfigured)"

    def is_configured(self) -> bool:
        return False

    def get_missing_configuration(self) -> List[str]:
        return ["EMAIL_PROVIDER"]

    async def send_email(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "success": False,
            "provider_message_id": None,
            "provider_thread_id": None,
            "error": "PROVIDER_NOT_CONFIGURED: No email provider is configured in environment. Set EMAIL_PROVIDER to 'gmail', 'smtp', or 'mock'."
        }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        return {"status": "UNCONFIGURED", "error": "PROVIDER_NOT_CONFIGURED"}


class EmailProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, BaseEmailProvider] = {
            "mock": MockEmailProvider(),
            "gmail": GmailProvider(),
            "smtp": SMTPProvider(),
            "none": UnconfiguredEmailProvider()
        }
        self._override_provider: Optional[str] = None

    def register(self, name: str, provider: BaseEmailProvider):
        self._providers[name.lower()] = provider

    def set_override_provider(self, name: Optional[str]):
        self._override_provider = name.lower() if name else None

    def get_provider(self, name: str) -> BaseEmailProvider:
        return self._providers.get(name.lower(), self._providers["none"])

    def get_active_provider(self) -> BaseEmailProvider:
        if self._override_provider:
            return self.get_provider(self._override_provider)
        configured_name = (settings.EMAIL_PROVIDER or "none").lower()
        return self.get_provider(configured_name)

    def get_status(self) -> Dict[str, Any]:
        active = self.get_active_provider()
        missing = active.get_missing_configuration()
        sender = None
        if isinstance(active, GmailProvider):
            sender = active.sender_email
        elif isinstance(active, SMTPProvider):
            sender = active.from_email
        elif isinstance(active, MockEmailProvider):
            sender = "outreach@prospectos.local"

        return {
            "configured_provider": active.provider_name,
            "is_ready_to_send": active.is_configured(),
            "sender_email": sender,
            "missing_configuration": missing,
            "supported_providers": ["gmail", "smtp", "mock", "none"]
        }


email_registry = EmailProviderRegistry()
