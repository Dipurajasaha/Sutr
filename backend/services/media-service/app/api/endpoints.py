from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.media import MediaPlaybackResponse
from app.services.playback_manager import get_segments_for_chunks
from typing import List

router = APIRouter()

@router.get("/playback/{file_id}", response_model=MediaPlaybackResponse)
async def get_playback_info(
    file_id: str, 
    chunk_ids: List[str] = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    # -- retrieve path and timestamp segments --
    file_path, segments = await get_segments_for_chunks(db, file_id, chunk_ids)
    
    if file_path is None:
        raise HTTPException(status_code=404, detail="File metadata not found")

    return MediaPlaybackResponse(
        file_id=file_id,
        file_path=file_path,
        segments=segments
    )