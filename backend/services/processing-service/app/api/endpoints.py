from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.database import get_db
from app.schemas.process import ProcessRequest, ProcessResponse
from app.models.chunk import TextChunk
from app.services.pdf_parser import process_pdf
from app.services.media_parser import process_media

router = APIRouter()

#####################################################################################
# -- extracts content from a file, chunks it, and saves to DB --
#####################################################################################
@router.post("/process/", response_model=ProcessResponse)
async def process_file(request: ProcessRequest, db: AsyncSession = Depends(get_db)):

    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found at {request.file_path}")
    
    try:
        # -- 1. route to correct processor --
        if request.file_type == "document":
            extracted_data = await run_in_threadpool(process_pdf, request.file_path)
        elif request.file_type in ["audio", "video"]:
            extracted_data = await run_in_threadpool(process_media, request.file_path)
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
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))