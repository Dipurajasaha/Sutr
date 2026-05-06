from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse, SourceChunk
from app.services.agent_service import process_chat

router = APIRouter()

#####################################################################################
# -- Handles conversational queries with smart vector routing --
#####################################################################################
@router.post("/query/", response_model=ChatResponse)
async def ask_question(request: ChatRequest):

    # -- process the chat and get the answer and sources --
    answer, sources = await process_chat(
        session_id=request.session_id,
        query=request.query,
        file_id=request.file_id
    )

    # -- format the sources --
    formatted_sources = [SourceChunk(**s) for s in sources]

    return ChatResponse(
        answer=answer,
        sources=formatted_sources
    )