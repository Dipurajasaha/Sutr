from fastapi import APIRouter, File, UploadFile, Request
from app.services.proxy import forward_request, forward_upload
from app.core.config import settings

router = APIRouter()

# ==========================================
# 1. UPLOAD ROUTES
# ==========================================
@router.post("/upload/")
async def gateway_upload_file(file: UploadFile = File(...)):
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/upload/"
    return await forward_upload(url, file)

@router.get("/files/{file_id}")
async def gateway_get_file(file_id: str):
    url = f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/{file_id}"
    return await forward_request("GET", url)

# ==========================================
# 2. PROCESSING ROUTES
# ==========================================
@router.post("/process/")
async def gateway_process_file(request: Request):
    payload = await request.json()
    url = f"{settings.PROCESS_SERVICE_URL}/api/v1/process/"
    return await forward_request("POST", url, payload=payload)

# ==========================================
# 3. CHAT ROUTES
# ==========================================
@router.post("/chat/query/")
async def gateway_chat_query(request: Request):
    payload = await request.json()
    url = f"{settings.CHAT_SERVICE_URL}/api/v1/chat/query/"
    return await forward_request("POST", url, payload=payload)

# ==========================================
# 4. SUMMARY ROUTES
# ==========================================
@router.post("/summary/generate/")
async def gateway_generate_summary(request: Request):
    payload = await request.json()
    url = f"{settings.SUMMARY_SERVICE_URL}/api/v1/summary/generate/"
    return await forward_request("POST", url, payload=payload)

# ==========================================
# 5. MEDIA ROUTES
# ==========================================
@router.get("/media/playback/{file_id}")
async def gateway_media_playback(file_id: str, request: Request):
    # -- extract query params like chunk_ids --
    params = dict(request.query_params)
    url = f"{settings.MEDIA_SERVICE_URL}/api/v1/media/playback/{file_id}"
    return await forward_request("GET", url, params=params)