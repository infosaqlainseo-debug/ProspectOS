import pytest
import uuid
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_matching_lifecycle(db_session):
    from app.models import Company, PublisherRecord, PublisherObservation
    from app.main import app
    from httpx import ASGITransport
    
    import uuid
    suffix = uuid.uuid4().hex[:8]
    
    # 1. Create a test company
    comp = Company(canonical_domain=f"test-prospect-{suffix}.com", company_name="Test Prospect")
    db_session.add(comp)
    await db_session.commit()
    
    # 2. Create some publishers
    pub1 = Company(canonical_domain=f"pub1-{suffix}.com")
    pub2 = Company(canonical_domain=f"pub2-{suffix}.com")
    db_session.add_all([pub1, pub2])
    await db_session.commit()
    
    pr1 = PublisherRecord(company_id=pub1.id, audience_focus="Tech")
    pr2 = PublisherRecord(company_id=pub2.id, audience_focus="Health")
    db_session.add_all([pr1, pr2])
    await db_session.commit()
    
    obs1 = PublisherObservation(publisher_id=pr1.id, price=100.0, metric_da=80.0)
    obs2 = PublisherObservation(publisher_id=pr2.id, price=500.0, metric_da=60.0)
    db_session.add_all([obs1, obs2])
    await db_session.commit()
    
    # 3. Create campaign profile
    payload = {
        "target_industry": "Tech",
        "max_budget": 200.0
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        resp = await async_client.put(f"/matching/campaigns/prospect/{comp.id}/profile", json=payload)
        assert resp.status_code == 200
        assert resp.json()["target_industry"] == "Tech"
        
        # 4. Run matching
        resp = await async_client.post(f"/matching/runs/{comp.id}")
        assert resp.status_code == 200
        run_id = resp.json()["id"]
        assert resp.json()["status"] == "COMPLETED"
        assert resp.json()["total_eligible"] >= 1 # pub1 fits budget, others might too
        assert resp.json()["total_excluded"] >= 1 # pub2 is too expensive, others might be too
        
        # 5. Check results
        resp = await async_client.get(f"/matching/runs/{run_id}/results")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1
        
        # Find our test publisher in results
        my_pub = next((r for r in results if r["publisher_id"] == str(pr1.id)), None)
        assert my_pub is not None
        assert my_pub["component_scores"]["topical_relevance"] == 35.0
