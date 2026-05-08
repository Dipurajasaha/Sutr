from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from app.api.endpoints import router as upload_router
from app.core.database import engine, Base
from app.core.config import settings

# -- initialize logging --
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- create FastAPI app instance --
app = FastAPI(title="Sutr Upload Service", description="Handles file ingestion and metadata")

# -- Add CORS middleware for media streaming --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


##########################################################################
# -- initializes the database tables on startup --
##########################################################################
@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to database and verifying tables...")
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])

# -- mount static files for media playback --
uploads_dir = Path(settings.UPLOAD_DIR).resolve()
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# -- basic health check endpoint --
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "upload-service"}