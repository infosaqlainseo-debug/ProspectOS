from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseEmailProvider(ABC):
    """Abstract base class for all outreach email providers."""

    provider_name: str = "Base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True only if all required credentials and settings are present."""
        pass

    @abstractmethod
    def get_missing_configuration(self) -> list[str]:
        """Returns a list of missing required configuration environment variables."""
        pass

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        sender_email: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an email message.
        Returns a dict:
          {
            "success": bool,
            "provider_message_id": Optional[str],
            "provider_thread_id": Optional[str],
            "error": Optional[str]
          }
        """
        pass

    @abstractmethod
    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Checks delivery/reply status of a sent message."""
        pass
