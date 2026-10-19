import httpx
from typing import Optional
import base64
from app.services.providers.base import SEOProvider, ProviderResponse, MetricResult
from app.core.config import settings

class MozProvider(SEOProvider):
    provider_name = "Moz"
    base_url = "https://lsapi.seomoz.com/v2"
    
    def __init__(self):
        self.api_key = settings.MOZ_API_KEY
        self.access_id = getattr(settings, "MOZ_ACCESS_ID", None) or "moz_id"
        
    def _get_auth(self):
        if not self.api_key:
            return None
        # Moz v2 Links API uses HTTP Basic Authentication (Access ID : Secret Key)
        return httpx.BasicAuth(username=self.access_id, password=self.api_key)

    async def get_authority_metrics(self, domain: str) -> ProviderResponse:
        auth = self._get_auth()
        endpoint = "/url_metrics"
        if not auth:
            return ProviderResponse(
                provider_name=self.provider_name, 
                error="PROVIDER_NOT_CONFIGURED",
                endpoint=endpoint
            )
            
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, auth=auth, json={"targets": [domain]})
                
                if resp.status_code in (401, 403):
                    return ProviderResponse(provider_name=self.provider_name, error="AUTHENTICATION_ERROR", endpoint=endpoint)
                if resp.status_code == 429:
                    return ProviderResponse(provider_name=self.provider_name, error="RATE_LIMITED", endpoint=endpoint)
                    
                resp.raise_for_status()
                data = resp.json()
                
                results = data.get("results", [])
                if not results:
                    return ProviderResponse(provider_name=self.provider_name, error="PROVIDER_ERROR", endpoint=endpoint)
                    
                metric_data = results[0]
                da = metric_data.get("domain_authority")
                spam_score = metric_data.get("spam_score")
                
                metrics = []
                
                # Domain Authority
                if da is not None:
                    metrics.append(MetricResult(
                        metric_name="domain_authority",
                        value=float(da),
                        provider_metric_name="domain_authority",
                        provider_endpoint=endpoint,
                        status="VERIFIED_PROVIDER_RESPONSE",
                        raw_reference=metric_data
                    ))
                else:
                    metrics.append(MetricResult(
                        metric_name="domain_authority",
                        value=None,
                        provider_metric_name="domain_authority",
                        provider_endpoint=endpoint,
                        status="NOT_AVAILABLE",
                        raw_reference=metric_data
                    ))
                
                # Spam Score
                if spam_score is not None:
                    metrics.append(MetricResult(
                        metric_name="spam_score",
                        value=float(spam_score),
                        provider_metric_name="spam_score",
                        provider_endpoint=endpoint,
                        status="VERIFIED_PROVIDER_RESPONSE",
                        raw_reference=metric_data
                    ))
                    
                return ProviderResponse(
                    provider_name=self.provider_name,
                    metrics=metrics,
                    usage_units=1.0, # 1 row
                    endpoint=endpoint
                )
                
        except httpx.RequestError as e:
            return ProviderResponse(provider_name=self.provider_name, error="PROVIDER_ERROR", endpoint=endpoint)
        except Exception as e:
            return ProviderResponse(provider_name=self.provider_name, error="VALIDATION_ERROR", endpoint=endpoint)

    async def get_domain_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    async def get_backlink_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")

    async def get_traffic_metrics(self, domain: str) -> ProviderResponse:
        return ProviderResponse(provider_name=self.provider_name, error="UNSUPPORTED")
