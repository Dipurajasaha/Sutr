from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import logging
from app.api.endpoints import router as gateway_router
from app.core.config import settings

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


# Root-level proxy for static uploads so frontend can request /uploads/* directly
@app.get("/uploads/{file_path:path}")
async def gateway_uploads_root(file_path: str, request: Request):
    url = f"{settings.UPLOAD_SERVICE_URL}/uploads/{file_path}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=dict(request.query_params), timeout=30.0)
            resp.raise_for_status()
            headers = {}
            if resp.headers.get("content-type"):
                headers["content-type"] = resp.headers.get("content-type")
            for h in ("content-range", "accept-ranges", "content-length", "cache-control", "last-modified", "etag"):
                if resp.headers.get(h):
                    headers[h] = resp.headers.get(h)
            return StreamingResponse(resp.aiter_bytes(), status_code=resp.status_code, headers=headers)
        except httpx.HTTPStatusError as e:
            return StreamingResponse(e.response.aiter_bytes() if e.response is not None else iter(()), status_code=e.response.status_code if e.response is not None else 502)
        except httpx.RequestError as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Upload service unavailable: {str(e)}")

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}