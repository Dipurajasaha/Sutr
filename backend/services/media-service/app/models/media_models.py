from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

# -- re-defining the file model to access paths --
class FileMetadata(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True)
    file_path = Column(String)

# -- re-defining the chunk model to access timestamps --
class TextChunk(Base):
    __tablename__ = "text_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True)
    file_id = Column(UUID(as_uuid=True))
    text = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)