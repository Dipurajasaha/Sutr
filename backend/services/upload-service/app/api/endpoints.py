from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os

from app.core.database import get_db
from app.schemas.file import FileResponse
from app.models.file import FileMetadata
from app.services.upload_manager import save_file_to_disk, create_file_metadata


router = APIRouter()

# -- restrict allowed formats based on requirements --
ALLOWED_EXTENSIONS = {
    ".pdf", 
    ".mp3", ".wav", ".flac", ".m4a",  # Audio
    ".mp4", ".mkv", ".avi", ".mov"    # Video
}


##########################################################################
# -- endpoint to access files, save them locally, and store metadata --
##########################################################################
@router.post("/upload/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not supported. Please upload PDF, MP3, WAV, MP4, or MKV.")

    # -- determine internally file category --
    if ext == ".pdf":
        file_type = "document"
    elif ext in [".mp3", ".wav", ".flac", ".m4a"]:
        file_type = "audio"
    else:
        file_type = "video"

    # -- pre-generate a UUID to use for the safe filename --
    temp_id = str(uuid.uuid4())

    # -- save file path --
    file_path = await save_file_to_disk(file, temp_id)

    # -- save metadata to DB --
    db_file = await create_file_metadata(db, file.filename, file_type, file_path)

    return db_file


##########################################################################
# -- endpoint to retrieve file metadata and processing status --
##########################################################################
@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file_status(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return db_file