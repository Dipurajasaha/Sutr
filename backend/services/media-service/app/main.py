from fastapi import FastAPI
import logging
from app.api.endpoints import router as media_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr Media Service", description="Handles media timestamp mapping and playback segments")

# -- register media routes --
app.include_router(media_router, prefix="/api/v1/media", tags=["Media"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "media-service"}