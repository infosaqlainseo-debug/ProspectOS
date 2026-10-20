from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult

class DiscoveryProvider(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    def source_type(self) -> str:
        return "public_search"

    @property
    def rate_limit_rpm(self) -> int:
        return 30

    @property
    def availability_status(self) -> str:
        return "AVAILABLE"

    @property
    def supported_fields(self) -> List[str]:
        return ["company_name", "website_url", "canonical_domain", "industry", "source_url"]

    @property
    def config_requirements(self) -> str:
        return "No API key required; respects public rate limits."

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "rate_limit_rpm": self.rate_limit_rpm,
            "availability_status": self.availability_status,
            "supported_fields": self.supported_fields,
            "config_requirements": self.config_requirements,
        }

    @abstractmethod
    async def discover(self, request: DiscoveryRequest) -> AsyncGenerator[List[DiscoveryResult], None]:
        """
        Yields batches of DiscoveryResult.
        Continues yielding until no more results are available or target reached.
        """
        yield []
