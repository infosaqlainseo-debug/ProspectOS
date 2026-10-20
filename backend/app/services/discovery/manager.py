import logging
from typing import List, Dict, Any, AsyncGenerator
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult
from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.duckduckgo import DuckDuckGoProvider
from app.services.discovery.directory import BusinessDirectoryProvider
from app.services.discovery.github import GitHubOrgProvider

logger = logging.getLogger(__name__)

class DiscoverySourceManager:
    """Orchestrates multi-source adapters for lead discovery."""

    def __init__(self):
        self.providers: Dict[str, DiscoveryProvider] = {
            "duckduckgo": DuckDuckGoProvider(),
            "directory": BusinessDirectoryProvider(),
            "github": GitHubOrgProvider(),
        }

    def list_sources(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available source adapters."""
        return [
            {
                "key": key,
                **provider.get_metadata()
            }
            for key, provider in self.providers.items()
        ]

    def get_provider(self, key: str) -> DiscoveryProvider:
        return self.providers.get(key, self.providers["duckduckgo"])

    async def discover_across_sources(
        self,
        request: DiscoveryRequest
    ) -> AsyncGenerator[List[DiscoveryResult], None]:
        """Discovers prospects across requested sources in priority order."""
        selected_sources = request.source_preferences or ["directory", "duckduckgo"]
        
        # If specific country/industry like Mexico e-commerce, directory provides instant high-quality verified leads
        # while duckduckgo provides broad search coverage
        for source_key in selected_sources:
            provider = self.providers.get(source_key.lower())
            if not provider:
                continue

            logger.info(f"Executing discovery with source adapter: {provider.source_name}")
            try:
                async for batch in provider.discover(request):
                    if batch:
                        yield batch
            except Exception as e:
                logger.error(f"Source adapter {provider.source_name} failed: {e}")
                continue

source_manager = DiscoverySourceManager()
