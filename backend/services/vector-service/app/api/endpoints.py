from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.database import get_db
from app.schemas.vector import IndexRequest, SearchRequest, SearchResult
from app.models.vector_metadata import VectorMetadata
from app.services.embedding_service import vector_store

router = APIRouter()


def _sanitize_chunk_text(value) -> str:
    # -- normalize incoming text before storing in database --
    if value is None:
        return ""

    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="ignore")
    else:
        text = str(value)

    text = text.replace("\x00", "")
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text.strip()

##########################################################################
# Index Chunks
##########################################################################
@router.post("/index/", status_code=201)
async def index_chunks(request: IndexRequest, db: AsyncSession = Depends(get_db)):
    try:
        if not request.chunks:
            raise HTTPException(status_code=400, detail="No chunks provided.")
        
        normalized_chunks = []
        file_ids_to_process = set()
        for chunk in request.chunks:
            clean_text = _sanitize_chunk_text(chunk.text)
            if not clean_text:
                continue
            normalized_chunks.append((chunk, clean_text))
            file_ids_to_process.add(chunk.file_id)

        if not normalized_chunks:
            raise HTTPException(status_code=400, detail="No valid chunks to index.")

        # -- if FAISS was recreated from scratch, clear stale DB ids to avoid primary-key collisions --
        if vector_store.index.ntotal == 0:
            from sqlalchemy import delete
            await db.execute(delete(VectorMetadata))

        # -- delete existing chunks for these files to avoid unique constraint violations --
        from sqlalchemy import delete
        for file_id in file_ids_to_process:
            await db.execute(delete(VectorMetadata).where(VectorMetadata.file_id == file_id))

        texts = [clean_text for _, clean_text in normalized_chunks]

        # -- generate embeddings and add to FAISS index --
        embeddings = vector_store.generate_embeddings(texts)
        faiss_ids = vector_store.add_to_index(embeddings)

        # -- map FAISS IDs to chunk UUIDs in PostgreSQL --
        db_records = []
        for i, (chunk, clean_text) in enumerate(normalized_chunks):
            record = VectorMetadata(
                faiss_id = faiss_ids[i],
                chunk_id = chunk.chunk_id,
                file_id = chunk.file_id,
                text=clean_text,
                start_time=chunk.start_time,
                end_time=chunk.end_time,
            )
            db.add(record)
            db_records.append(record)

        await db.commit()
        return {"status": "success", "indexed_count": len(db_records)}
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Index endpoint error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


##########################################################################
# Search Vectors
##########################################################################
@router.post("/search/", response_model=list[SearchResult])
async def search_vectors(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    # -- search FAISS index for nearest neighbors --
    distances, faiss_indices = vector_store.search_index(request.query, request.top_k)

    # -- retrieve metadata from PostgreSQL using FAISS IDs --
    results = []
    for score, f_id in zip(distances, faiss_indices):
        if f_id == -1:      # -- FAISS returns -1 if there aren't enough vectors
            continue

        result = await db.execute(select(VectorMetadata).where(VectorMetadata.faiss_id == f_id))
        metadata = result.scalar_one_or_none()

        if metadata:
            # -- skip if file_id filter doesn't match --
            if request.file_id and metadata.file_id != request.file_id:
                continue

            results.append(SearchResult(
                chunk_id=metadata.chunk_id,
                file_id=metadata.file_id,
                text=metadata.text,
                score=score,
                start_time=getattr(metadata, "start_time", None),
                end_time=getattr(metadata, "end_time", None),
            ))

    return results


##########################################################################
# Get File Chunks (Fallback)
##########################################################################
@router.get("/files/{file_id}/chunks/", response_model=list[SearchResult])
async def get_file_chunks(file_id: str, limit: int = 4, db: AsyncSession = Depends(get_db)):
    file_uuid = UUID(file_id)
    result = await db.execute(
        select(VectorMetadata)
        .where(VectorMetadata.file_id == file_uuid)
        .order_by(VectorMetadata.faiss_id)
        .limit(limit)
    )
    metadata_rows = result.scalars().all()

    return [
        SearchResult(
            chunk_id=row.chunk_id,
            file_id=row.file_id,
            text=row.text,
            score=0.0,
            start_time=getattr(row, "start_time", None),
            end_time=getattr(row, "end_time", None),
        )
        for row in metadata_rows
    ]


##########################################################################
# Delete File Vectors (Cascading)
##########################################################################
@router.delete("/files/{file_id}/chunks/", status_code=200)
async def delete_file_vectors(file_id: str, db: AsyncSession = Depends(get_db)):
    # -- delete all vector metadata records for a file --
    file_uuid = UUID(file_id)
    
    result = await db.execute(
        select(VectorMetadata).where(VectorMetadata.file_id == file_uuid)
    )
    metadata_rows = result.scalars().all()
    
    if not metadata_rows:
        return {"status": "success", "deleted_count": 0, "message": f"No vector records found for file {file_id}"}
    
    # -- FAISS index removal is complex; rely on DB cleanup instead --
    faiss_ids_to_remove = [row.faiss_id for row in metadata_rows if row.faiss_id is not None]
    
    for metadata in metadata_rows:
        await db.delete(metadata)
    
    await db.commit()
    
    return {
        "status": "success",
        "deleted_count": len(metadata_rows),
        "message": f"Deleted {len(metadata_rows)} vector records for file {file_id}"
    }