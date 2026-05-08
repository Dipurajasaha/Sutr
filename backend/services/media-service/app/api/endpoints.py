from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.core.database import get_db
from app.schemas.media import MediaPlaybackResponse
from app.services.playback_manager import get_segments_for_chunks
from typing import List

router = APIRouter()

##########################################################################
# Get Playback Info
##########################################################################
@router.get("/playback/{file_id}", response_model=MediaPlaybackResponse)
async def get_playback_info(
    file_id: str, 
    chunk_ids: List[str] = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    # -- map chunk IDs to playable segments with timestamps --
    file_uuid = uuid.UUID(file_id)
    chunk_uuid_list = [uuid.UUID(chunk_id) for chunk_id in chunk_ids]
    file_path, segments = await get_segments_for_chunks(db, file_uuid, chunk_uuid_list)
    
    if file_path is None:
        raise HTTPException(status_code=404, detail="File metadata not found")

    return MediaPlaybackResponse(
        file_id=file_id,
        file_path=file_path,
        segments=segments
    )