from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.database import get_db
from app.schemas.process import ProcessRequest, ProcessResponse
from app.models.chunk import TextChunk
from app.services.pdf_parser import process_pdf
from app.services.media_parser import process_media
from app.core.config import settings

router = APIRouter()

#####################################################################################
# -- extracts content from a file, chunks it, and saves to DB --
#####################################################################################
@router.post("/process/", response_model=ProcessResponse)
async def process_file(request: ProcessRequest, db: AsyncSession = Depends(get_db)):
    file_type = "document" if request.file_type == "pdf" else request.file_type
    file_path = request.file_path
    if not os.path.isabs(file_path):
        candidates = [
            file_path,
            os.path.join(settings.UPLOAD_DIR, file_path),
            os.path.join("..", "upload-service", "uploads", os.path.basename(file_path)),
        ]
        file_path = next((p for p in candidates if os.path.exists(p)), file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found at {request.file_path}")
    
    try:
        # -- 1. route to correct processor --
        if file_type == "document":
            extracted_data = await run_in_threadpool(process_pdf, file_path)
        elif file_type in ["audio", "video"]:
            extracted_data = await run_in_threadpool(process_media, file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        
        # -- 2.store chunks in database --
        db_chunks = []
        for index, data in enumerate(extracted_data):
            chunk = TextChunk(
                file_id = request.file_id,
                chunk_index = index,
                text = data["text"],
                start_time = data["start_time"],
                end_time = data["end_time"]
            )
            db.add(chunk)
            db_chunks.append(chunk)

        await db.commit()

        return ProcessResponse(
            status = "success",
            file_id = request.file_id,
            total_chunks = len(db_chunks),
            message = "File processed and chunked successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))