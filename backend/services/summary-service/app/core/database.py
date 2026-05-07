from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# #########################################################################################
# -- creates the async engine for the summary service --
# #########################################################################################
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# -- session factory for creating database connections --
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# -- base class for the isolated textchunk model --
Base = declarative_base()

##########################################################################################
# -- dependency to provide a database session to endpoints --
##########################################################################################
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session