from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

############################################################################################
# -- SQLAlchemy model to map FAISS integer indices to application-level UUIDs --
# -- this facilitates retrieval of text content and file context during the RAG process --
############################################################################################
class VectorMetadata(Base):
    __tablename__ = "vector_metadata"

    faiss_id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(UUID(as_uuid=True), index=True, nullable=False, unique=True)
    file_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    text = Column(String, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)