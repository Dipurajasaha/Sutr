from fastapi import FastAPI
import logging
from app.api.endpoints import router as chat_router

# -- configure logging --
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- initialize the FastAPI app --
app = FastAPI(title="Sutr Chat Service", description="Agentic RAG Pipeline with Temporary Memory")

# -- include the chat router --
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])

# -- simple health check endpoint --
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "chat-service"}