import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("Starting discovery job...")
        payload = {
            "industry": "Artificial Intelligence",
            "target_count": 5
        }
        response = await ac.post("/jobs", json={
            "job_type": "company_discovery",
            "payload": payload
        })
        job_data = response.json()
        print("Job Data:", job_data)
        job_id = job_data.get("job_id")
        
        from app.workers.worker import company_discovery_job
        
        print("Executing worker job...")
        await company_discovery_job(None, job_id, payload)
        
        print("Job completed. Checking status...")
        response = await ac.get(f"/jobs/{job_id}")
        print("Final Status:", response.json())

if __name__ == "__main__":
    asyncio.run(main())
