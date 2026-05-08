from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import uuid
import os
import httpx

from app.core.database import get_db
from app.schemas.file import FileResponse
from app.models.file import FileMetadata
from app.services.upload_manager import save_file_to_disk, create_file_metadata, delete_file_from_disk
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


router = APIRouter()

# -- supported file formats for upload --
ALLOWED_EXTENSIONS = {
    ".pdf", 
    ".mp3", ".wav", ".flac", ".m4a",
    ".mp4", ".mkv", ".avi", ".mov"
}

# -- request schema for file update endpoint --
class RenameFileRequest(BaseModel):
    filename: str = None
    summary_quick: str = None
    summary_detailed: str = None


##########################################################################
# Upload File
##########################################################################
@router.post("/upload/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # -- validate file extension --
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not supported. Please upload PDF, MP3, WAV, MP4, or MKV.")

    # -- determine file category --
    if ext == ".pdf":
        file_type = "document"
    elif ext in [".mp3", ".wav", ".flac", ".m4a"]:
        file_type = "audio"
    else:
        file_type = "video"

    # -- generate UUID for safe filename --
    temp_id = str(uuid.uuid4())

    # -- save file to disk --
    file_path = await save_file_to_disk(file, temp_id)

    # -- save metadata to database --
    db_file = await create_file_metadata(db, file.filename, file_type, file_path)

    # return the ORM object directly so callers (and tests) receive the
    # same object instance created by the service layer
    return db_file


##########################################################################
# List All Files
##########################################################################
@router.get("/files/", response_model=list[FileResponse])
async def list_all_files(db: AsyncSession = Depends(get_db)):
    # -- retrieve all files ordered by creation date --
    result = await db.execute(select(FileMetadata).order_by(FileMetadata.created_at.desc()))
    files = result.scalars().all()
    
    # return the list of ORM objects directly so FastAPI / tests receive
    # the model instances (and keep behavior consistent with other endpoints)
    return files


##########################################################################
# Get File Status
##########################################################################
@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file_status(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # -- retrieve file metadata and processing status --
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # return the ORM object so callers get the same instance from the DB
    return db_file


##########################################################################
# Delete File
##########################################################################
@router.delete("/files/{file_id}")
async def delete_file(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # -- retrieve file record --
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"[DELETE] Starting file deletion for file_id={file_id}, filename={db_file.filename}")

    # -- delete the physical file from disk --
    try:
        await delete_file_from_disk(db_file.file_path)
        logger.info(f"[DELETE] Physical file deleted: {db_file.file_path}")
    except Exception as e:
        logger.warning(f"[DELETE] Failed to delete physical file {db_file.file_path}: {str(e)}")

    # -- delete vector records via vector-service --
    logger.info(f"[DELETE] Attempting to delete vectors for file_id={file_id}")
    logger.info(f"[DELETE] VECTOR_SERVICE_URL={settings.VECTOR_SERVICE_URL}")
    try:
        async with httpx.AsyncClient() as client:
            vector_url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/files/{file_id}/chunks/"
            logger.info(f"[DELETE] Calling vector-service DELETE: {vector_url}")
            vector_response = await client.delete(vector_url, timeout=30.0)
            logger.info(f"[DELETE] Vector-service response: status={vector_response.status_code}, body={vector_response.text}")
    except Exception as e:
        logger.error(f"[DELETE] Failed to delete vector records for file_id={file_id}: {str(e)}")

    # -- delete database record --
    logger.info(f"[DELETE] Deleting file record from database...")
    await db.delete(db_file)
    await db.commit()
    logger.info(f"[DELETE] File deletion completed for file_id={file_id}")

    return {"detail": f"File {db_file.filename} deleted successfully"}


##########################################################################
# Update File
##########################################################################
@router.patch("/files/{file_id}", response_model=FileResponse)
async def rename_file(file_id: uuid.UUID, request: RenameFileRequest, db: AsyncSession = Depends(get_db)):
    # -- retrieve file record --
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # -- update filename if provided --
    if request.filename:
        if not request.filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        db_file.filename = request.filename.strip()

    # -- update summaries if provided --
    if request.summary_quick is not None:
        db_file.summary_quick = request.summary_quick
    if request.summary_detailed is not None:
        db_file.summary_detailed = request.summary_detailed

    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    # return the updated ORM object
    return db_file