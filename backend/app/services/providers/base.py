from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class MetricResult(BaseModel):
    metric_name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    provider_metric_name: str
    provider_endpoint: str
    status: str # VERIFIED_PROVIDER_RESPONSE, NOT_AVAILABLE, ERROR, UNSUPPORTED
    error_message: Optional[str] = None
    raw_reference: Optional[Dict[str, Any]] = None

class ProviderResponse(BaseModel):
    provider_name: str
    metrics: List[MetricResult] = Field(default_factory=list)
    usage_units: Optional[float] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    error: Optional[str] = None

class SEOProvider(ABC):
    provider_name: str
    
    @abstractmethod
    async def get_domain_metrics(self, domain: str) -> ProviderResponse:
        """Fetch general domain level metrics."""
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    @abstractmethod
    async def get_backlink_metrics(self, domain: str) -> ProviderResponse:
        """Fetch backlink and referring domain metrics."""
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    @abstractmethod
    async def get_traffic_metrics(self, domain: str) -> ProviderResponse:
        """Fetch organic traffic and keyword metrics."""
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    @abstractmethod
    async def get_authority_metrics(self, domain: str) -> ProviderResponse:
        """Fetch authority and spam score metrics."""
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")
