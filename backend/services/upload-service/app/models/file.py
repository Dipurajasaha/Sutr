import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, timezone 

from app.core.database import Base

##########################################################################
# -- SQLAlchemy model for storing file metadata in DB --
##########################################################################
class FileMetadata(Base):
    # -- SQLAlchemy model for storing file metadata in DB --
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String, index=True)
    file_type = Column(String)  # document (PDF), audio, video 
    file_path = Column(String, unique=True) # local storage path 
    status = Column(String, default="uploaded") # state tracking: uploaded, processing, completed, failed 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    summary_quick = Column(Text, nullable=True) # Quick summary (auto-generated on upload)
    summary_detailed = Column(Text, nullable=True) # Detailed summary/notes (auto-generated on upload)