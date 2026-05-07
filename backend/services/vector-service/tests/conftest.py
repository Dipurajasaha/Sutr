import os
import sys
from unittest.mock import MagicMock

# -- MOCK HEAVY ML LIBRARIES BEFORE THE APP IMPORTS THEM --
# This prevents pytest from downloading the all-MiniLM-L6-v2 model!
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faiss'] = MagicMock()

import pytest
import pytest_asyncio
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

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    if os.path.exists("./test_vector.db"):
        try:
            os.remove("./test_vector.db")
        except Exception:
            pass