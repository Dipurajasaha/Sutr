from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# -- create async for high-performance db operations -- 
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# -- create a session factory --
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# -- dependency to get db session in FastAPI endpoints --
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session