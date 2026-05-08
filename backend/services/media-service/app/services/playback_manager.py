import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.media_models import FileMetadata, TextChunk
from app.schemas.media import TimestampSegment

##########################################################################################
# -- maps chunk IDs back to their timestamps and joins with the file path --
##########################################################################################
async def get_segments_for_chunks(db: AsyncSession, file_id: uuid.UUID, chunk_ids: list[uuid.UUID]):
    # -- fetch file path --
    file_result = await db.execute(select(FileMetadata).where(FileMetadata.id == file_id))
    file_data = file_result.scalar_one_or_none()
    
    if not file_data:
        return None, []

    # -- fetch specific chunks to get their start and end times --
    chunk_result = await db.execute(
        select(TextChunk).where(TextChunk.id.in_(chunk_ids)).order_by(TextChunk.start_time)
    )
    chunks = chunk_result.scalars().all()

    # -- format chunk data into playback segments --
    segments = [
        TimestampSegment(
            start=c.start_time if c.start_time is not None else 0.0,
            end=c.end_time if c.end_time is not None else 0.0,
            text=c.text
        ) for c in chunks
    ]
    
    return file_data.file_path, segments