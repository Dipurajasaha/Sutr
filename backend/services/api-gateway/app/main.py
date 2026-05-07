from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.endpoints import router as gateway_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr API Gateway", description="Unified entry point for Sutr Microservices")

# -- enable CORS for frontend integration later --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- register all routed endpoints under a unified /api prefix --
app.include_router(gateway_router, prefix="/api", tags=["Gateway"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}