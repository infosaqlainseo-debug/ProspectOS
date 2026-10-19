import httpx
from typing import Optional
from app.services.providers.base import SEOProvider, ProviderResponse, MetricResult
from app.core.config import settings

class SemrushProvider(SEOProvider):
    provider_name = "Semrush"
    base_url = "https://api.semrush.com"
    
    def __init__(self):
        self.api_key = settings.SEMRUSH_API_KEY
        
    async def get_domain_metrics(self, domain: str) -> ProviderResponse:
        endpoint = "/"
        if not self.api_key:
            return ProviderResponse(
                provider_name=self.provider_name, 
                error="PROVIDER_NOT_CONFIGURED",
                endpoint=endpoint
            )
            
        # Domain Overview - domain_ranks
        params = {
            "type": "domain_ranks",
            "key": self.api_key,
            "domain": domain,
            "database": "us"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.base_url, params=params)
                
                if resp.status_code in (401, 403):
                    return ProviderResponse(provider_name=self.provider_name, error="AUTHENTICATION_ERROR", endpoint=endpoint)
                if resp.status_code == 429:
                    return ProviderResponse(provider_name=self.provider_name, error="RATE_LIMITED", endpoint=endpoint)
                
                # Semrush returns simple text CSV by default
                resp.raise_for_status()
                text = resp.text.strip().split('\n')
                
                if len(text) < 2:
                    return ProviderResponse(provider_name=self.provider_name, error="PROVIDER_ERROR", endpoint=endpoint)
                    
                headers = text[0].split(';')
                values = text[1].split(';')
                
                data = dict(zip(headers, values))
                
                metrics = []
                
                # Organic Traffic
                organic_traffic = data.get("Organic Traffic")
                if organic_traffic is not None and organic_traffic != "":
                    metrics.append(MetricResult(
                        metric_name="organic_traffic",
                        value=float(organic_traffic),
                        provider_metric_name="Organic Traffic",
                        provider_endpoint=endpoint,
                        status="VERIFIED_PROVIDER_RESPONSE",
                        raw_reference=data
                    ))
                else:
                    metrics.append(MetricResult(
                        metric_name="organic_traffic",
                        value=None,
                        provider_metric_name="Organic Traffic",
                        provider_endpoint=endpoint,
                        status="NOT_AVAILABLE",
                        raw_reference=data
                    ))

                # Authority Score
                authority = data.get("Authority Score")
                if authority is not None and authority != "":
                    metrics.append(MetricResult(
                        metric_name="authority_score",
                        value=float(authority),
                        provider_metric_name="Authority Score",
                        provider_endpoint=endpoint,
                        status="VERIFIED_PROVIDER_RESPONSE",
                        raw_reference=data
                    ))
                    
                return ProviderResponse(
                    provider_name=self.provider_name,
                    metrics=metrics,
                    usage_units=10.0, # Approximate API units cost
                    endpoint=endpoint
                )
                
        except httpx.RequestError as e:
            return ProviderResponse(provider_name=self.provider_name, error="PROVIDER_ERROR", endpoint=endpoint)
        except Exception as e:
            return ProviderResponse(provider_name=self.provider_name, error="VALIDATION_ERROR", endpoint=endpoint)

    async def get_backlink_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    async def get_traffic_metrics(self, domain: str) -> ProviderResponse:
        return await self.get_domain_metrics(domain)

    async def get_authority_metrics(self, domain: str) -> ProviderResponse:
        return await self.get_domain_metrics(domain)
