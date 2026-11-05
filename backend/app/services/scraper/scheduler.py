import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.scraper import ScraperTask, ScraperTaskRun, ExtractedRecord

logger = logging.getLogger(__name__)

def calculate_next_run(
    schedule_type: str,
    from_time: Optional[datetime] = None,
    schedule_cron: Optional[str] = None
) -> Optional[datetime]:
    """Calculates next execution time based on schedule type."""
    now = from_time or datetime.now(timezone.utc)
    st = schedule_type.upper().strip()

    if st == "NONE":
        return None
    elif st == "HOURLY":
        return now + timedelta(hours=1)
    elif st == "DAILY":
        return now + timedelta(days=1)
    elif st == "WEEKLY":
        return now + timedelta(weeks=1)
    elif st == "MONTHLY":
        return now + timedelta(days=30)
    elif st == "CUSTOM":
        # Default custom interval 6 hours if cron parsing not specified
        return now + timedelta(hours=6)
    return None

async def check_and_trigger_scheduled_tasks(session: AsyncSession) -> int:
    """
    Scans for active scheduled tasks where next_run_at <= now,
    and returns list of triggered task IDs.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(ScraperTask)
        .where(
            ScraperTask.is_schedule_active == True,
            ScraperTask.next_run_at <= now,
            ScraperTask.status.in_(["DRAFT", "COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"])
        )
    )
    res = await session.execute(stmt)
    due_tasks = res.scalars().all()
    
    triggered_count = 0
    for task in due_tasks:
        logger.info(f"Triggering scheduled run for task: {task.name} ({task.id})")
        task.status = "QUEUED"
        task.next_run_at = calculate_next_run(task.schedule_type, from_time=now)
        triggered_count += 1

    if triggered_count > 0:
        await session.commit()

    return triggered_count

