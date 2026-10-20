import pytest
import uuid
from app.services.discovery.nl_parser import parse_with_heuristics
from app.services.discovery.templates import PROSPECTING_TEMPLATES, get_template_by_id
from app.services.discovery.directory import BusinessDirectoryProvider
from app.services.discovery.duckduckgo import DuckDuckGoProvider
from app.services.discovery.manager import source_manager
from app.services.discovery.pipeline import calculate_transparent_lead_score
from app.schemas.discovery import DiscoveryRequest
from app.models import Company, WebsiteScan

@pytest.mark.asyncio
async def test_nl_query_parser_mexico_ecommerce():
    query = "Find 50 new companies in Mexico that have weak SEO, operate in the e-commerce industry, have an accessible website, and could benefit from technical SEO, link building, and Digital PR."
    config = parse_with_heuristics(query)
    
    assert config.target_count == 50
    assert config.country == "Mexico"
    assert "E-commerce" in config.industry
    assert config.max_seo_score == 65.0
    assert "Technical SEO" in config.desired_service_opportunity
    assert "Link Building" in config.desired_service_opportunity
    assert "Digital PR" in config.desired_service_opportunity
    assert "50 target companies" in config.interpreted_summary

@pytest.mark.asyncio
async def test_prospecting_templates():
    assert len(PROSPECTING_TEMPLATES) >= 6
    mex_t = get_template_by_id("mexico-ecommerce")
    assert mex_t is not None
    assert mex_t.country == "Mexico"
    assert mex_t.target_count == 50
    assert "Technical SEO" in mex_t.desired_services

    usa_t = get_template_by_id("usa-ecommerce-seo")
    assert usa_t is not None
    assert usa_t.country == "United States"

@pytest.mark.asyncio
async def test_source_adapters_metadata():
    sources = source_manager.list_sources()
    keys = [s["key"] for s in sources]
    assert "duckduckgo" in keys
    assert "directory" in keys
    assert "github" in keys

    for s in sources:
        assert "rate_limit_rpm" in s
        assert "availability_status" in s
        assert "config_requirements" in s

@pytest.mark.asyncio
async def test_directory_provider_mexico():
    provider = BusinessDirectoryProvider()
    req = DiscoveryRequest(target_count=10, country="Mexico", industry="E-commerce")
    
    results = []
    async for batch in provider.discover(req):
        results.extend(batch)
        if len(results) >= 10:
            break

    assert len(results) >= 10
    first = results[0]
    assert first.country == "Mexico"
    assert first.website_url.startswith("http")
    assert first.source_name == "Public Verified Business Directory"

@pytest.mark.asyncio
async def test_transparent_lead_scoring():
    company = Company(
        id=uuid.uuid4(),
        company_name="Test Retail MX",
        canonical_domain="testretail.com.mx",
        country="Mexico",
        industry="E-commerce / Retail"
    )
    scan = WebsiteScan(
        url="https://testretail.com.mx",
        http_status=200,
        https_enabled=True,
        title="Test", # Short title -> gap
        meta_description=None, # Missing meta -> gap
        h1=[] # Missing H1 -> gap
    )
    
    scoring = calculate_transparent_lead_score(scan, company, requested_industry="E-commerce")
    assert 0 <= scoring["score"] <= 100
    comp = scoring["components"]
    assert "seo_opportunity" in comp
    assert "business_fit" in comp
    assert "evidence_quality" in comp
    assert "website_potential" in comp
    assert len(scoring["findings"]) >= 2
