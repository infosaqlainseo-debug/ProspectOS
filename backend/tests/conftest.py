import pytest_asyncio
from app.db.session import async_session_maker

@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session
