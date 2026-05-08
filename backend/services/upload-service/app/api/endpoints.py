from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import uuid
import os

from app.core.database import get_db
from app.schemas.file import FileResponse
from app.models.file import FileMetadata
from app.services.upload_manager import save_file_to_disk, create_file_metadata, delete_file_from_disk
import os


router = APIRouter()

# -- restrict allowed formats based on requirements --
ALLOWED_EXTENSIONS = {
    ".pdf", 
    ".mp3", ".wav", ".flac", ".m4a",  # Audio
    ".mp4", ".mkv", ".avi", ".mov"    # Video
}

# -- Request schema for rename endpoint --
class RenameFileRequest(BaseModel):
    filename: str


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

    # Return file_path as the stored basename so frontend can construct /uploads/{stored_filename}
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "file_type": db_file.file_type,
        "file_path": os.path.basename(db_file.file_path),
        "status": db_file.status,
        "created_at": db_file.created_at,
    }


##########################################################################
# -- endpoint to retrieve all files from the database --
##########################################################################
@router.get("/files/", response_model=list[FileResponse])
async def list_all_files(db: AsyncSession = Depends(get_db)):
    """Retrieve all files from the FileMetadata table."""
    result = await db.execute(select(FileMetadata).order_by(FileMetadata.created_at.desc()))
    files = result.scalars().all()
    # Normalize file_path to basename for frontend consumption
    resp = []
    for f in files:
        stored = ""
        if f.file_path:
            stored = f.file_path.replace('\\', '/').split('/')[-1]
        resp.append({
            "id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "file_path": stored,
            "status": f.status,
            "created_at": f.created_at,
        })
    return resp


##########################################################################
# -- endpoint to retrieve file metadata and processing status --
##########################################################################
@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file_status(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    stored = db_file.file_path.replace('\\', '/').split('/')[-1] if db_file.file_path else ""
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "file_type": db_file.file_type,
        "file_path": stored,
        "status": db_file.status,
        "created_at": db_file.created_at,
    }


##########################################################################
# -- endpoint to delete a file record and physical file --
##########################################################################
@router.delete("/files/{file_id}")
async def delete_file(file_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a file record from the database and remove the physical file."""
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # -- delete the physical file from disk --
    try:
        await delete_file_from_disk(db_file.file_path)
    except Exception as e:
        # Log but don't fail if file deletion fails (record still gets deleted)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to delete physical file {db_file.file_path}: {str(e)}")

    # -- delete the database record --
    await db.delete(db_file)
    await db.commit()

    return {"detail": f"File {db_file.filename} deleted successfully"}


##########################################################################
# -- endpoint to rename a file in the database --
##########################################################################
@router.patch("/files/{file_id}", response_model=FileResponse)
async def rename_file(file_id: uuid.UUID, request: RenameFileRequest, db: AsyncSession = Depends(get_db)):
    """Update the filename of a file in the database."""
    result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    db_file = result.scalar_one_or_none()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if not request.filename or not request.filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    # -- update filename --
    db_file.filename = request.filename.strip()
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    stored = db_file.file_path.replace('\\', '/').split('/')[-1] if db_file.file_path else ""
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "file_type": db_file.file_type,
        "file_path": stored,
        "status": db_file.status,
        "created_at": db_file.created_at,
    }