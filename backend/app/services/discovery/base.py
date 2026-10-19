from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult

class DiscoveryProvider(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    async def discover(self, request: DiscoveryRequest) -> AsyncGenerator[List[DiscoveryResult], None]:
        """
        Yields batches of DiscoveryResult.
        Continues yielding until no more results are available.
        """
        yield []
