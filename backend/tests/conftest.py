import os
import pytest
import pytest_asyncio
from sqlalchemy import text

# CRITICAL ISOLATION: Automated testing MUST use the dedicated test database 'prospectos_test'.
# Never point test runs to the production database 'prospectos'.
current_db = os.getenv("DATABASE_URL", "")
if "@db:5432" in current_db:
    TEST_DB = "postgresql+asyncpg://user:password@db:5432/prospectos_test"
else:
    TEST_DB = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/prospectos_test")

os.environ["DATABASE_URL"] = TEST_DB

from app.core.config import settings
settings.DATABASE_URL = TEST_DB

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

test_engine = create_async_engine(TEST_DB, echo=False, future=True)
test_async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Monkey-patch app.db.session so any code calling async_session_maker in tests uses prospectos_test
import app.db.session
app.db.session.engine = test_engine
app.db.session.async_session_maker = test_async_session_maker

@pytest_asyncio.fixture(autouse=True)
async def enforce_test_database_isolation():
    """
    CRITICAL SAFETY GUARD:
    Verifies on every test run that the active connection is strictly 'prospectos_test'.
    Fails immediately with RuntimeError if connected to 'prospectos'.
    """
    async with test_engine.connect() as conn:
        res = await conn.execute(text("SELECT current_database();"))
        active_db = res.scalar()
        if active_db != "prospectos_test":
            raise RuntimeError(
                f"FATAL SAFETY VIOLATION: Test suite attempted to connect to database '{active_db}'. "
                "Automated tests are strictly forbidden from connecting to 'prospectos'."
            )

@pytest_asyncio.fixture
async def db_session():
    async with test_async_session_maker() as session:
        yield session
