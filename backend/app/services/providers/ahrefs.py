import httpx
from typing import Optional
from app.services.providers.base import SEOProvider, ProviderResponse, MetricResult
from app.core.config import settings

class AhrefsProvider(SEOProvider):
    provider_name = "Ahrefs"
    base_url = "https://api.ahrefs.com/v3"
    
    def __init__(self):
        self.api_key = settings.AHREFS_API_KEY
        
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    async def get_authority_metrics(self, domain: str) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                provider_name=self.provider_name, 
                error="PROVIDER_NOT_CONFIGURED",
                endpoint="/site-explorer/domain-rating"
            )
            
        endpoint = "/site-explorer/domain-rating"
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # In real scenario: limit=1, target=domain
                resp = await client.get(url, headers=self._get_headers(), params={"target": domain, "date": "today"})
                
                if resp.status_code in (401, 403):
                    # Check if API key has access to public domain-rating-free endpoint
                    free_endpoint = "/public/domain-rating-free"
                    free_url = f"{self.base_url}{free_endpoint}"
                    resp_free = await client.get(free_url, headers=self._get_headers(), params={"target": domain})
                    if resp_free.status_code == 200:
                        resp = resp_free
                        endpoint = free_endpoint
                    elif resp_free.status_code == 429:
                        return ProviderResponse(provider_name=self.provider_name, error="RATE_LIMITED", endpoint=free_endpoint)
                    else:
                        return ProviderResponse(provider_name=self.provider_name, error="AUTHENTICATION_ERROR", endpoint=endpoint)
                elif resp.status_code == 429:
                    return ProviderResponse(provider_name=self.provider_name, error="RATE_LIMITED", endpoint=endpoint)
                    
                resp.raise_for_status()
                data = resp.json()
                
                # Ahrefs returns domain_rating in an array under "domain_rating"
                dr_data = data.get("domain_rating", {})
                dr_val = dr_data.get("domain_rating")
                
                metrics = []
                if dr_val is not None:
                    metrics.append(MetricResult(
                        metric_name="domain_rating",
                        value=float(dr_val),
                        provider_metric_name="domain_rating",
                        provider_endpoint=endpoint,
                        status="VERIFIED_PROVIDER_RESPONSE",
                        raw_reference=data
                    ))
                else:
                    metrics.append(MetricResult(
                        metric_name="domain_rating",
                        value=None,
                        provider_metric_name="domain_rating",
                        provider_endpoint=endpoint,
                        status="NOT_AVAILABLE",
                        raw_reference=data
                    ))
                    
                # Ahrefs charges cost per row; free public endpoint consumes 0 units
                cost = float(data.get("cost", 0.0 if endpoint == "/public/domain-rating-free" else 1.0))
                
                return ProviderResponse(
                    provider_name=self.provider_name,
                    metrics=metrics,
                    usage_units=cost,
                    endpoint=endpoint
                )
                
        except httpx.RequestError as e:
            return ProviderResponse(provider_name=self.provider_name, error="PROVIDER_ERROR", endpoint=endpoint)
        except Exception as e:
            return ProviderResponse(provider_name=self.provider_name, error="VALIDATION_ERROR", endpoint=endpoint)

    async def get_domain_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    async def get_backlink_metrics(self, domain: str) -> ProviderResponse:
        # Ahrefs API v3 /site-explorer/metrics
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    async def get_traffic_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")
