import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.main import app

# -- use a local file so data persists across multiple requests in the same test --
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

##########################################################################################
# -- override the dependency to use the test database instead of production --
##########################################################################################
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # -- setup: create tables --
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield  # -- run the test --
    
    # -- teardown: drop tables and close engine --
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    # -- clean up the physical test file --
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass