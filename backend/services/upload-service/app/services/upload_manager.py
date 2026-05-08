import os 
import shutil 
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import FileMetadata
from app.core.config import settings


##########################################################################
# Save File to Disk
##########################################################################
async def save_file_to_disk(upload_file: UploadFile, file_id: str) -> str:
    # -- ensure upload directory exists --
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # -- extract extension and create collision-free filename --
    extension = os.path.splitext(upload_file.filename)[1]
    safe_filename = f"{file_id}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # -- write uploaded file stream to disk --
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


##########################################################################
# Create File Metadata
##########################################################################
async def create_file_metadata(db: AsyncSession, filename: str, file_type: str, file_path: str) -> FileMetadata:
    # -- save file record to database with initial uploaded status --
    db_file = FileMetadata(
        filename=filename,
        file_type=file_type,
        file_path=file_path,
        status="uploaded"
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file


##########################################################################
# Delete File from Disk
##########################################################################
async def delete_file_from_disk(file_path: str) -> None:
    # -- remove physical file from uploads directory --
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        raise FileNotFoundError(f"File not found at path: {file_path}")