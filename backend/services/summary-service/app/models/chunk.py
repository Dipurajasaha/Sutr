import uuid
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

##########################################################################################
# -- internal model for accessing text chunks (Isolated from other services) --
##########################################################################################
class TextChunk(Base):
    __tablename__ = "text_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)