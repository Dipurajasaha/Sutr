from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.schemas.vector import IndexRequest, SearchRequest, SearchResult
from app.models.vector_metadata import VectorMetadata
from app.services.embedding_sevice import vector_store

router = APIRouter()

#################################################################################
# -- receives text chunks, embeds them, and stores them in FAISS & PostgreSQL --
#################################################################################
@router.post("/index/", status_code=201)
async def index_chunks(request: IndexRequest, db: AsyncSession = Depends(get_db)):
    if not request.chunks:
        raise HTTPException(status_code=400, detail="No chunks provided.")
    
    texts = [chunk.text for chunk in request.chunks]

    # -- 1. generating embeddings and add to FAISS--
    embeddings = vector_store.generate_embeddings(texts)
    faiss_ids = vector_store.add_to_index(embeddings)

    # -- 2. map FAISS IDs to Chunk UUIDs in PostgresSQL --
    db_records = []
    for i, chunk in enumerate(request.chunks):
        record = VectorMetadata(
            faiss_id = faiss_ids[i],
            chunk_id = chunk.chunk_id,
            file_id = chunk.file_id,
            text=chunk.text
        )
        db.add(record)
        db_records.append(record)

    await db.commit()
    return {"status": "success", "indexed_count": len(db_records)}


#################################################################################
# -- searches FAISS for semantic similarity and retrives chunk data --
#################################################################################
@router.post("/search/", response_model=list[SearchResult])
async def search_vectors(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    
    # -- 1. search FAISS index --
    distances, faiss_indices = vector_store.search_index(request.query, request.top_k)

    # -- 2. retrieve metadata from PostgreSQL using the FAISS IDs --
    results = []
    for score, f_id in zip(distances, faiss_indices):
        if f_id == -1:      # -- FAISS returns -1 if there aren't enough vectors
            continue

        result = await db.execute(select(VectorMetadata).where(VectorMetadata.faiss_id == f_id))
        metadata = result.scalar_one_or_none()

        if metadata:
            # -- apply file_id filter if provided --
            if request.file_id and metadata.file_id != request.file_id:
                continue

            results.append(SearchResult(
                chunk_id=metadata.chunk_id,
                file_id=metadata.file_id,
                text=metadata.text,
                score=score
            ))

    return results