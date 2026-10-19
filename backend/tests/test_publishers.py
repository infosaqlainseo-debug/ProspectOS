import pytest
import uuid
import httpx
from httpx import ASGITransport
from app.main import app
from app.models import PublisherRecord, Company, ImportBatch

@pytest.mark.asyncio
async def test_publisher_preview():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        csv_content = """Publisher Name,Website,Price
TechCrunch,techcrunch.com,1500
Local News,localnews.com,500"""
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = await client.post("/publishers/import/preview", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["headers"] == ["Publisher Name", "Website", "Price"]
        assert len(data["preview_rows"]) == 2
        assert data["preview_rows"][0]["Website"] == "techcrunch.com"

@pytest.mark.asyncio
async def test_publisher_commit(db_session):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        batch_id = uuid.uuid4()
        payload = {
            "batch_id": str(batch_id),
            "mapping": {
                "url_column": "Website",
                "publisher_name_column": "Publisher Name",
                "price_column": "Price"
            },
            "rows": [
                {"Publisher Name": "TestCrunch", "Website": f"testcrunch-{batch_id}.com", "Price": "1500"},
                {"Publisher Name": "Invalid", "Website": "", "Price": "500"},
                {"Publisher Name": "Duplicate", "Website": f"http://testcrunch-{batch_id}.com/path", "Price": "2000"},
            ]
        }
        response = await client.post("/publishers/import/commit", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["total_rows"] == 3
        # 1 created (TechCrunch), 1 failed (Empty URL), 1 updated (techcrunch.com deduplicated)
        assert data["created_records"] == 1
        assert data["updated_records"] == 1
        assert data["invalid_rows"] == 1
        assert data["failed_rows"] == 1

        # Check DB
        from sqlalchemy import select
        result = await db_session.execute(select(PublisherRecord).where(PublisherRecord.publisher_name == "TestCrunch"))
        records = result.scalars().all()
        assert len(records) >= 1
        assert records[0].publisher_name == "TestCrunch"
