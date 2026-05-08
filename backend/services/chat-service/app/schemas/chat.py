from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    # -- unique id for the current browser/chat tab --
    session_id: str
    query: str
    # -- current document used in chat --
    file_id: str

class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    start_time: float | None = None
    end_time: float | None = None

class ChatResponse(BaseModel):
    answer: str
    # -- populated only if the vector DB was used --
    sources: List[SourceChunk]


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatHistoryMessage]