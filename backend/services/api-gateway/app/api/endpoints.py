from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx

from app.services.proxy import forward_request, forward_upload, forward_process_request
from app.core.config import settings

router = APIRouter()

##########################################################################
# -- 1. UPLOAD ROUTES --
##########################################################################

# -- proxy upload requests to the upload service --
@router.post("/upload/")
async def gateway_upload_file(file: UploadFile = File(...)):
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/upload/"
    return await forward_upload(url, file)

# -- proxy file listing and metadata requests to the upload service --
@router.get("/files/")
async def gateway_list_files():
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/"
    return await forward_request("GET", url)

# -- proxy file detail requests to the upload service --
@router.get("/files/{file_id}")
async def gateway_get_file(file_id: str):
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/{file_id}"
    return await forward_request("GET", url)

# -- proxy file deletion requests to the upload service --
@router.delete("/files/{file_id}")
async def gateway_delete_file(file_id: str):
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/{file_id}"
    return await forward_request("DELETE", url)

# -- proxy file renaming requests to the upload service --
@router.patch("/files/{file_id}")
async def gateway_rename_file(file_id: str, request: Request):
    payload = await request.json()
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/{file_id}"
    return await forward_request("PATCH", url, payload=payload)


##########################################################################
# -- 2. PROCESSING ROUTES (with extended timeout for long Whisper jobs) --
##########################################################################
@router.post("/process/")
async def gateway_process_file(request: Request):
    payload = await request.json()
    url = f"{settings.PROCESS_SERVICE_URL}/api/v1/process/"
    return await forward_process_request("POST", url, payload=payload)


##########################################################################
# -- 3. CHAT ROUTES --
##########################################################################
# -- proxy chat query requests to the chat service --
@router.post("/chat/query/")
async def gateway_chat_query(request: Request):
    payload = await request.json()
    url = f"{settings.CHAT_SERVICE_URL}/api/v1/chat/query/"
    return await forward_request("POST", url, payload=payload)
# -- proxy chat history requests to the chat service --
@router.get("/chat/history/{session_id}")
async def gateway_chat_history(session_id: str):
    url = f"{settings.CHAT_SERVICE_URL}/api/v1/chat/history/{session_id}"
    return await forward_request("GET", url)


##########################################################################
# -- 4. VECTOR ROUTES --
##########################################################################
# -- proxy vector indexing requests to the vector service --
@router.post("/vectors/index/")
async def gateway_index_vectors(request: Request):
    payload = await request.json()
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/index/"
    return await forward_request("POST", url, payload=payload)

# -- proxy vector search requests to the vector service --
@router.post("/vectors/search/")
async def gateway_search_vectors(request: Request):
    payload = await request.json()
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/search/"
    return await forward_request("POST", url, payload=payload)

# -- proxy file chunk retrieval requests to the vector service --
@router.get("/vectors/chunks/{file_id}")
async def gateway_get_file_chunks(file_id: str, request: Request):
    params = dict(request.query_params)
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/files/{file_id}/chunks/"
    return await forward_request("GET", url, params=params)

# -- proxy file chunk deletion requests to the vector service --
@router.delete("/vectors/chunks/{file_id}")
async def gateway_delete_file_vectors(file_id: str):
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/files/{file_id}/chunks/"
    return await forward_request("DELETE", url)


##########################################################################
# -- 5. SUMMARY ROUTES --
##########################################################################
@router.post("/summary/generate")
@router.post("/summary/generate/")
async def gateway_generate_summary(request: Request):
    payload = await request.json()
    primary_url = f"{settings.SUMMARY_SERVICE_URL}/api/v1/summary/generate"
    print(f"[gateway-summary] primary_url={primary_url}")
    try:
        return await forward_request("POST", primary_url, payload=payload)
    except HTTPException as e:
        # -- fallback for stale SUMMARY_SERVICE_URL values in long-lived environments --
        if e.status_code != 404:
            raise
        fallback_url = "http://localhost:8006/api/v1/summary/generate"
        print(f"[gateway-summary] fallback_url={fallback_url}")
        return await forward_request("POST", fallback_url, payload=payload)


##########################################################################
# -- 6. MEDIA ROUTES --
##########################################################################
# -- proxy media playback requests to the media service --
@router.get("/media/playback/{file_id}")
async def gateway_media_playback(file_id: str, request: Request):
    params = dict(request.query_params)
    url = f"{settings.MEDIA_SERVICE_URL}/api/v1/media/playback/{file_id}"
    return await forward_request("GET", url, params=params)


# -- proxy static uploads from upload-service so frontend can request via gateway --
@router.get("/uploads/{file_path:path}")
async def gateway_uploads(file_path: str, request: Request):
    url = f"{settings.UPLOAD_SERVICE_URL}/uploads/{file_path}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=dict(request.query_params), timeout=30.0)
            resp.raise_for_status()
            # -- forward important headers --
            headers = {}
            if resp.headers.get("content-type"):
                headers["content-type"] = resp.headers.get("content-type")
            for h in ("content-range", "accept-ranges", "content-length", "cache-control", "last-modified", "etag"):
                if resp.headers.get(h):
                    headers[h] = resp.headers.get(h)

            return StreamingResponse(resp.aiter_bytes(), status_code=resp.status_code, headers=headers)
        
        except httpx.HTTPStatusError as e:
            # -- forward upstream HTTP errors directly to client --
            return StreamingResponse(e.response.aiter_bytes() if e.response is not None else iter(()), status_code=e.response.status_code if e.response is not None else 502)
        
        except httpx.RequestError as e:
            # -- handle network errors contacting upload-service --
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Upload service unavailable: {str(e)}")