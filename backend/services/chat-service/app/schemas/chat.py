from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str     # --> unique id for the current browser/chat tab 
    query: str
    file_id: str        # --> the current document using in chat 

class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    start_time: float | None = None
    end_time: float | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]  # --> will be populated only if the Vector DB was used 