import os 
import shutil 
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import FileMetadata
from app.core.config import settings


##########################################################################
# -- saves the uploaded file to local directory with a unique name --
##########################################################################
async def save_file_to_disk(upload_file: UploadFile, file_id: str) -> str:

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # -- extract extension and create a safe, collision-free filename --
    extension = os.path.splitext(upload_file.filename)[1]
    safe_filename = f"{file_id}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # -- save filestream to disk --
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


##########################################################################
# -- creates a new record in the database for the uploaded file --
##########################################################################
async def create_file_metadata(db: AsyncSession, filename: str, file_type: str, file_path: str) -> FileMetadata:

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