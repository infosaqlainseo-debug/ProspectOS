import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import Workflow, WorkflowRun, Job

async def trigger():
    async with async_session_maker() as session:
        # Create a test workflow
        wf = Workflow(
            name="Test Pipeline",
            description="A minimal test pipeline",
            enabled_stages=["discovery", "website_analysis", "opportunity_scoring"],
            max_companies_per_run=1,
            batch_size=1
        )
        session.add(wf)
        await session.commit()
        await session.refresh(wf)
        print(f"Created workflow: {wf.id}")

        # Start run
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://127.0.0.1:8000/workflows/{wf.id}/runs")
            print("Run Response:", resp.status_code, resp.json())
            
        return wf.id

if __name__ == "__main__":
    import sys
    sys.path.append("backend")
    # need to run inside the right path
