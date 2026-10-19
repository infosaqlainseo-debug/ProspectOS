import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine, async_session_maker
from app.models import Base, Company, Job
from app.core.config import settings

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        # For tests, we'll just ensure tables exist. They were already created by alembic upgrade head.
        pass
    yield

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoints(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    response = await client.get("/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    
    response = await client.get("/health/queue")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "queue": "connected"}

@pytest.mark.asyncio
async def test_config():
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None

@pytest.mark.asyncio
async def test_canonical_domain_uniqueness():
    async with async_session_maker() as session:
        c1 = Company(canonical_domain="test.com")
        session.add(c1)
        await session.commit()
        
        from sqlalchemy.exc import IntegrityError
        c2 = Company(canonical_domain="test.com")
        session.add(c2)
        with pytest.raises(IntegrityError):
            await session.commit()
            
        await session.rollback()
        
        # Cleanup
        await session.delete(c1)
        await session.commit()

@pytest.mark.asyncio
async def test_job_creation_and_worker(client):
    response = await client.post("/jobs", json={"job_type": "system_test"})
    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]
    assert data["status"] == "QUEUED"
    
    # We call the worker function directly to simulate ARQ executing it
    from app.workers.worker import health_check_job
    await health_check_job(None, job_id)
    
    # Check status transitions
    response = await client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
