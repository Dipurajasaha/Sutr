from fastapi import FastAPI
import logging
from app.api.endpoints import router as summary_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr Summary Service", description="Summarization engine for documents and media")

# -- register summary routes --
app.include_router(summary_router, prefix="/api/v1/summary", tags=["Summary"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "summary-service"}