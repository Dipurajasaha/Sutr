from fastapi import FastAPI
import logging

from app.api.endpoints import router as upload_router
from app.core.database import engine, Base

# -- initialize logging --
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- create FastAPI app instance --
app = FastAPI(title="Sutr Upload Service", description="Handles file ingestion and metadata")


##########################################################################
# Initializes the database tables on startup
##########################################################################
@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to database and verifying tables...")
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])

# -- basic health check endpoint --
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "upload-service"}