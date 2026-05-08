from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.endpoints import router as summary_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr Summary Service", description="Summarization engine for documents and media")

# -- enable CORS for direct frontend calls during local dev --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- register summary routes --
app.include_router(summary_router, prefix="/api/v1/summary", tags=["Summary"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "summary-service"}