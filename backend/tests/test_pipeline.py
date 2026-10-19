import pytest
import uuid
import pytest_asyncio
from sqlalchemy import select
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult
from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.pipeline import run_discovery_pipeline
from app.models import Job, Company, Domain
from app.db.session import async_session_maker

class MockProvider(DiscoveryProvider):
    @property
    def source_name(self) -> str:
        return "Mock Provider"

    async def discover(self, request: DiscoveryRequest):
        suffix = uuid.uuid4().hex[:6]
        yield [
            DiscoveryResult(company_name=f"Company A {suffix}", website_url=f"https://companya-{suffix}.com", source_name="Mock", discovery_method="mock"),
            DiscoveryResult(company_name=f"Company B {suffix}", website_url=f"http://companyb-{suffix}.com", source_name="Mock", discovery_method="mock"),
            DiscoveryResult(company_name=f"Company A Duplicate {suffix}", website_url=f"companya-{suffix}.com", source_name="Mock", discovery_method="mock"),
            DiscoveryResult(company_name=f"No Website {suffix}", website_url=None, source_name="Mock", discovery_method="mock"),
        ]

@pytest_asyncio.fixture
async def mock_http_validate(monkeypatch):
    import app.services.discovery.pipeline
    async def always_true(*args, **kwargs):
        return True
    monkeypatch.setattr(app.services.discovery.pipeline, "validate_website", always_true)

@pytest.mark.asyncio
async def test_discovery_pipeline(mock_http_validate):
    async with async_session_maker() as db_session:
        # Setup job
        job = Job(job_type="company_discovery", status="QUEUED", requested_count=2)
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        request = DiscoveryRequest(target_count=2, industry="Tech")
        provider = MockProvider()

        await run_discovery_pipeline(job.id, request, provider, db_session)

        # Refresh job
        await db_session.refresh(job)

        assert job.status == "COMPLETED"
        assert job.discovered_count == 2
        assert job.failed_count == 0
        assert job.duplicate_count == 0
        assert job.stored_count == 2
        
        # Check DB
        companies = (await db_session.execute(select(Company))).scalars().all()
        # Find companies matching Company A and Company B
        names = [c.company_name for c in companies]
        assert any(n.startswith("Company A") for n in names)
        assert any(n.startswith("Company B") for n in names)

        domains = (await db_session.execute(select(Domain))).scalars().all()
        # Ensure we have domains for those companies
        domain_names = [d.domain for d in domains]
        assert any("companya-" in d for d in domain_names)
        assert any("companyb-" in d for d in domain_names)
        
