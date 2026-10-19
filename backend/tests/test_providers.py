import pytest
from app.services.providers.ahrefs import AhrefsProvider
from app.services.providers.moz import MozProvider
from app.services.providers.semrush import SemrushProvider
from app.services.providers.base import ProviderResponse
import httpx
import respx

@pytest.mark.asyncio
async def test_ahrefs_provider():
    provider = AhrefsProvider()
    provider.api_key = "test_key"
    
    domain = "example.com"
    with respx.mock:
        # Mock Ahrefs Domain Rating endpoint
        mock_route = respx.get(f"{provider.base_url}/site-explorer/domain-rating").mock(
            return_value=httpx.Response(200, json={
                "domain_rating": {"domain_rating": 89.5},
                "cost": 1.5
            })
        )
        
        resp = await provider.get_authority_metrics(domain)
        assert resp.error is None
        assert resp.provider_name == "Ahrefs"
        assert resp.usage_units == 1.5
        assert len(resp.metrics) == 1
        
        dr_metric = resp.metrics[0]
        assert dr_metric.metric_name == "domain_rating"
        assert dr_metric.value == 89.5
        assert dr_metric.status == "VERIFIED_PROVIDER_RESPONSE"

@pytest.mark.asyncio
async def test_ahrefs_provider_public_fallback():
    provider = AhrefsProvider()
    provider.api_key = "test_free_key"
    
    domain = "example.com"
    with respx.mock:
        # Mock 401 on paid site-explorer endpoint
        respx.get(f"{provider.base_url}/site-explorer/domain-rating").mock(
            return_value=httpx.Response(401, json=["Error", "Unauthorized"])
        )
        # Mock 200 on public domain-rating-free endpoint
        respx.get(f"{provider.base_url}/public/domain-rating-free").mock(
            return_value=httpx.Response(200, json={
                "domain_rating": {"domain_rating": 77.0, "license": "license_url"}
            })
        )
        
        resp = await provider.get_authority_metrics(domain)
        assert resp.error is None
        assert resp.provider_name == "Ahrefs"
        assert resp.endpoint == "/public/domain-rating-free"
        assert resp.usage_units == 0.0
        assert len(resp.metrics) == 1
        
        dr_metric = resp.metrics[0]
        assert dr_metric.metric_name == "domain_rating"
        assert dr_metric.value == 77.0
        assert dr_metric.status == "VERIFIED_PROVIDER_RESPONSE"

@pytest.mark.asyncio
async def test_moz_provider():
    provider = MozProvider()
    provider.api_key = "test_moz_key"
    
    domain = "example.com"
    with respx.mock:
        # Mock Moz API
        mock_route = respx.post(f"{provider.base_url}/url_metrics").mock(
            return_value=httpx.Response(200, json={
                "results": [{
                    "domain_authority": 92.1,
                    "spam_score": 1
                }]
            })
        )
        
        resp = await provider.get_authority_metrics(domain)
        assert resp.error is None
        assert resp.provider_name == "Moz"
        assert len(resp.metrics) == 2
        
        metrics = {m.metric_name: m.value for m in resp.metrics}
        assert metrics["domain_authority"] == 92.1
        assert metrics["spam_score"] == 1.0

@pytest.mark.asyncio
async def test_semrush_provider():
    provider = SemrushProvider()
    provider.api_key = "test_semrush_key"
    
    domain = "example.com"
    with respx.mock:
        # Mock Semrush API (returns text/csv format)
        csv_response = "Domain;Organic Traffic;Authority Score\nexample.com;150000;85\n"
        mock_route = respx.get(f"{provider.base_url}").mock(
            return_value=httpx.Response(200, text=csv_response)
        )
        
        resp = await provider.get_domain_metrics(domain)
        assert resp.error is None
        assert resp.provider_name == "Semrush"
        assert len(resp.metrics) == 2
        
        metrics = {m.metric_name: m.value for m in resp.metrics}
        assert metrics["organic_traffic"] == 150000.0
        assert metrics["authority_score"] == 85.0

@pytest.mark.asyncio
async def test_provider_not_configured():
    provider = AhrefsProvider()
    provider.api_key = None # Clear key
    
    resp = await provider.get_authority_metrics("example.com")
    assert resp.error == "PROVIDER_NOT_CONFIGURED"
