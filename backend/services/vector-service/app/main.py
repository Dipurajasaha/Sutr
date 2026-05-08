from fastapi import FastAPI
import logging
from sqlalchemy import text

from app.api.endpoints import router as vector_router
from app.core.database import engine, Base

# -- configure basic logging to output at the INFO level --
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sutr Vector Service", description="Embedding and Semantic Search using FAISS")

# -- initialize database on startup --
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE vector_metadata ADD COLUMN IF NOT EXISTS start_time DOUBLE PRECISION"))
        await conn.execute(text("ALTER TABLE vector_metadata ADD COLUMN IF NOT EXISTS end_time DOUBLE PRECISION"))
    logger.info("Database initialized for Vector Service.")

# -- register the vector router under the specified API prefix --
app.include_router(vector_router, prefix="/api/v1/vectors", tags=["Vectors"])