from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatHistoryMessage, SourceChunk
from app.services.agent_service import process_chat
from app.services.memory_service import get_chat_history_records

router = APIRouter()

##########################################################################
# -- Chat Query with RAG --
##########################################################################
@router.post("/query/", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    # -- process chat query through RAG pipeline with memory --
    answer, sources = await process_chat(
        session_id=request.session_id,
        query=request.query,
        file_id=request.file_id
    )

    # -- format source chunks for response --
    formatted_sources = [SourceChunk(**s) for s in sources]

    return ChatResponse(
        answer=answer,
        sources=formatted_sources
    )


##########################################################################
# -- Get Chat History --
##########################################################################
@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str):
    # -- retrieve stored conversation history for session --
    records = get_chat_history_records(session_id)
    messages = [ChatHistoryMessage(**record) for record in records]
    return ChatHistoryResponse(session_id=session_id, messages=messages)