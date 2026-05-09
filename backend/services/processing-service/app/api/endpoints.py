from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
import httpx
import logging
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.process import ProcessRequest, ProcessResponse
from app.models.chunk import TextChunk
from app.services.pdf_parser import process_pdf
from app.services.media_parser import process_media
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _sanitize_chunk_text(value) -> str:
    # -- normalize chunk text to safe UTF-8 content for database storage --
    if value is None:
        return ""

    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="ignore")
    else:
        text = str(value)

    # -- remove null bytes and invalid surrogate code points --
    text = text.replace("\x00", "")
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text.strip()

##########################################################################
# Process File
##########################################################################
@router.post("/process/", response_model=ProcessResponse)
async def process_file(request: ProcessRequest, db: AsyncSession = Depends(get_db)):
    logger.info("Processing task started for file_id=%s", request.file_id)
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
        # -- route to correct processor based on file type --
        if file_type == "document":
            extracted_data = await run_in_threadpool(process_pdf, file_path)
        elif file_type in ["audio", "video"]:
            try:
                extracted_data = await run_in_threadpool(process_media, file_path)
            except Exception as e:
                logger.error("Media processing failed for file_path=%s: %s", file_path, str(e))
                extracted_data = []
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        
        # -- store extracted chunks in database --
        db_chunks = []
        for index, data in enumerate(extracted_data):
            clean_text = _sanitize_chunk_text(data.get("text", ""))
            if not clean_text:
                continue

            chunk = TextChunk(
                file_id = request.file_id,
                chunk_index = index,
                text = clean_text,
                start_time = data["start_time"],
                end_time = data["end_time"]
            )
            db.add(chunk)
            db_chunks.append(chunk)

        if not db_chunks:
            raise HTTPException(status_code=400, detail="No valid transcript text extracted from media file.")

        # -- flush to get DB-generated chunk IDs before sending to vector-service --
        await db.flush()

        # -- send chunks to vector-service for embedding and indexing --
        vector_url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/index/"
        logger.info("Sending %d chunks to vector-service at %s for file_id=%s", len(db_chunks), vector_url, request.file_id)
        vector_ok = False
        try:
            async with httpx.AsyncClient() as client:
                vector_response = await client.post(
                    vector_url,
                    json={
                        "chunks": [
                            {
                                "chunk_id": str(chunk.id),
                                "file_id": str(chunk.file_id),
                                "text": chunk.text,
                                "start_time": chunk.start_time,
                                "end_time": chunk.end_time,
                            }
                            for chunk in db_chunks
                        ]
                    },
                    timeout=30.0,
                )
            logger.info("Vector-service response for file_id=%s: %s", request.file_id, vector_response.status_code)
            vector_response.raise_for_status()
            vector_ok = True
        except httpx.RequestError:
            logger.exception("Failed to contact vector-service at %s for file_id=%s", vector_url, request.file_id)
        except Exception:
            logger.exception("Unexpected error sending to vector-service for file_id=%s", request.file_id)

        # -- mark file as completed regardless of vector-service status --
        logger.info("Committing completed status for file_id=%s (vector_ok=%s)", request.file_id, vector_ok)
        await db.execute(
            text("UPDATE files SET status = :status WHERE id = :file_id"),
            {"status": "completed", "file_id": str(request.file_id)},
        )
        await db.commit()

        # -- trigger auto-summary generation --
        logger.info("Triggering auto-summary generation for file_id=%s", request.file_id)
        try:
            async with httpx.AsyncClient() as client:
                summary_response = await client.post(
                    f"{settings.SUMMARY_SERVICE_URL}/api/v1/summary/generate/",
                    json={
                        "file_id": str(request.file_id),
                        "summary_type": "quick",
                        "store": True
                    },
                    timeout=60.0,
                )
                logger.info("Summary-service response for file_id=%s: %s", request.file_id, summary_response.status_code)
                summary_response.raise_for_status()
                
                # -- parse summary and store in upload service --
                summary_data = summary_response.json()
                summary_quick = summary_data.get("summary", "")
                
                logger.info("Storing summary for file_id=%s", request.file_id)
                update_response = await client.patch(
                    f"{settings.UPLOAD_SERVICE_URL}/api/v1/files/{request.file_id}",
                    json={
                        "summary_quick": summary_quick
                    },
                    timeout=30.0,
                )
                logger.info("Upload-service update response for file_id=%s: %s", request.file_id, update_response.status_code)
                update_response.raise_for_status()
        except Exception as e:
            logger.warning("Failed to auto-generate summary for file_id=%s: %s", request.file_id, str(e))

        return ProcessResponse(
            status = "success",
            file_id = request.file_id,
            total_chunks = len(db_chunks),
            message = "File processed and chunked successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing pipeline failed for file_id=%s", request.file_id)
        await db.rollback()
        logger.info("Committing failed status for file_id=%s", request.file_id)
        await db.execute(
            text("UPDATE files SET status = :status WHERE id = :file_id"),
            {"status": "failed", "file_id": str(request.file_id)},
        )
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))