from fastapi import FastAPI
import logging

from app.api.endpoints import router as process_router
from app.core.database import engine, Base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr Processing Service", description="Content Extraction and Chunking")

#####################################################################################
# -- initialize database tables on startup --
#####################################################################################
@app.on_event("startup")
async def startup_event():
    # -- Open an asynchronous connection to the PostgreSQL database --
    async with engine.begin() as conn:
        # -- Create all tables defined in the SQLAlchemy models (if they don't exist) --
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized for Processing Service.")

# -- register the processing routes under the "/api/v1" prefix --
app.include_router(process_router, prefix="/api/v1", tags=["Processing"])