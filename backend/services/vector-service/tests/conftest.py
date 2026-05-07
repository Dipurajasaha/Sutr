import os
import sys
from unittest.mock import MagicMock

# -- MOCK HEAVY ML LIBRARIES BEFORE THE APP IMPORTS THEM --
# This prevents pytest from downloading the all-MiniLM-L6-v2 model!
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faiss'] = MagicMock()

import pytest
import pytest_asyncio
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base, get_db
from app.main import app

# -- Use a persistent local file for SQLite tests --
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_vector.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

##########################################################################################
# -- session-scoped fixture to create tables once before all tests --
##########################################################################################
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once per test session"""
    def run_setup():
        async def _setup():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(_setup())
    
    run_setup()
    yield
    
    # -- cleanup after all tests --
    def run_cleanup():
        async def _cleanup():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()
        asyncio.run(_cleanup())
    
    run_cleanup()
    if os.path.exists("./test_vector.db"):
        try:
            os.remove("./test_vector.db")
        except Exception:
            pass

##########################################################################################
# -- function-scoped fixture to clean data between tests --
##########################################################################################
@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_between_tests():
    """Clean up data between each test"""
    yield
    # -- delete all data from each table after test --
    async with TestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"DELETE FROM {table.name}"))
        await session.commit()