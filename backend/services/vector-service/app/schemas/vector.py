from pydantic import BaseModel
from uuid import UUID
from typing import List


# -- represents a single extracted text chunk ready for vectorization --
class ChunkInput(BaseModel):
    chunk_id: UUID
    file_id: UUID
    text: str

# -- payload schema for the /index/ endpoint --
class IndexRequest(BaseModel):
    chunks: List[ChunkInput]

# -- payload schema for the /search/ endpoint --
class SearchRequest(BaseModel):
    query: str
    file_id: UUID = None
    top_k: int = 5

# -- response schema representing a single matched text chunk from FAISS --
class SearchResult(BaseModel):
    chunk_id: UUID
    file_id: UUID   
    text: str
    score: float