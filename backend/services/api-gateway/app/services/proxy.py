import httpx
from fastapi import HTTPException, UploadFile

##########################################################################################
# -- generic forwarder for JSON payloads --
##########################################################################################
async def forward_request(method: str, url: str, payload: dict = None, params: dict = None):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, json=payload, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

##########################################################################################
# -- specialized forwarder for multipart file uploads --
##########################################################################################
async def forward_upload(url: str, file: UploadFile):
    async with httpx.AsyncClient() as client:
        try:
            # -- read file into memory to forward --
            file_content = await file.read()
            files = {"file": (file.filename, file_content, file.content_type)}
            
            response = await client.post(url, files=files, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")