import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base, get_db
from app.main import app

# -- use a local file for the summary service test database --
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_summary.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

##########################################################################################
# -- override database dependency for isolation --
##########################################################################################
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # -- setup: create local tables --
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # -- teardown: cleanup --
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    if os.path.exists("./test_summary.db"):
        try:
            os.remove("./test_summary.db")
        except Exception:
            pass