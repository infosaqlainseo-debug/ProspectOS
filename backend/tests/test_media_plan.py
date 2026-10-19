import pytest
from httpx import ASGITransport, AsyncClient
import uuid
from sqlalchemy import select

from app.main import app
from app.db.session import async_session_maker
from app.models import Company, MediaPlan, MediaPlanItem, PublisherRecord, PublisherObservation

@pytest.mark.asyncio
async def test_media_plan_lifecycle():
    async with async_session_maker() as session:
        # 1. Create a Company and Publisher
        suffix = uuid.uuid4().hex[:8]
        comp = Company(
            canonical_domain=f"prospect-{suffix}.com", 
            company_name="Test Client",
            industry="Technology",
            country="United States"
        )
        session.add(comp)
        
        pub_company = Company(
            canonical_domain=f"publisher-{suffix}.com", 
            company_name="Tech Blog"
        )
        session.add(pub_company)
        await session.commit()
        await session.refresh(pub_company)
        
        pub = PublisherRecord(
            company_id=pub_company.id,
            publisher_name="Tech Blog"
        )
        session.add(pub)
        await session.commit()
        await session.refresh(comp)
        await session.refresh(pub)
        
        # Create an observation for price
        obs = PublisherObservation(
            publisher_id=pub.id,
            price=150.0,
            currency="USD",
            metric_da=45.0
        )
        session.add(obs)
        await session.commit()
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a media plan
        resp = await client.post(f"/media-plans/company/{comp.id}", json={"name": "Test Plan"})
        assert resp.status_code == 200, resp.text
        plan_data = resp.json()
        assert plan_data["name"] == "Test Plan"
        assert plan_data["company_id"] == str(comp.id)
        plan_id = plan_data["id"]
        
        # Add item
        item_resp = await client.post(f"/media-plans/{plan_id}/items", json={"publisher_id": str(pub.id)})
        assert item_resp.status_code == 200, item_resp.text
        updated_plan = item_resp.json()
        assert len(updated_plan["items"]) == 1
        assert updated_plan["items"][0]["publisher_id"] == str(pub.id)
        assert updated_plan["items"][0]["proposed_price"] == 150.0
        assert updated_plan["total_price"] == 150.0
        assert updated_plan["can_calculate_totals"] is True
        
        item_id = updated_plan["items"][0]["id"]
        
        # Update plan
        put_resp = await client.put(f"/media-plans/{plan_id}", json={"status": "FINAL"})
        assert put_resp.status_code == 200, put_resp.text
        assert put_resp.json()["status"] == "FINAL"
        
        # Export Excel
        excel_resp = await client.get(f"/media-plans/{plan_id}/export/excel")
        assert excel_resp.status_code == 200
        assert "spreadsheetml" in excel_resp.headers["content-type"]
        
        # Remove item
        del_resp = await client.delete(f"/media-plans/{plan_id}/items/{item_id}")
        assert del_resp.status_code == 200
        assert len(del_resp.json()["items"]) == 0
        assert del_resp.json()["total_price"] == 0.0
