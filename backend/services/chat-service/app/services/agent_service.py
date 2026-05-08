import httpx
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.services.memory_service import SYSTEM_PROMPT, get_chat_history, update_chat_history

# -- global cache for sources retrieved during tool use --
current_sources = []


def build_contextual_query(history: list, query: str, max_turns: int = 4) -> str:
    # -- build retrieval query preserving recent conversation context --
    # -- helps disambiguate follow-up questions like "tell me more" --
    recent_turns = []
    for message in history[-max_turns:]:
        if isinstance(message, (HumanMessage, AIMessage)):
            role = "User" if isinstance(message, HumanMessage) else "Assistant"
            content = getattr(message, "content", "")
            if content:
                recent_turns.append(f"{role}: {content}")

    if recent_turns:
        return "\n".join(recent_turns + [f"Current question: {query}"])

    return query


def _vector_search(query: str, file_id: str):
    # -- search vector database for relevant chunks --
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/search/"
    payload = {"query": query, "file_id": file_id, "top_k": 4}

    with httpx.Client() as client:
        response = client.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()


def _fetch_file_chunks(file_id: str, limit: int = 4):
    # -- fallback to retrieve early indexed chunks for a file --
    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/files/{file_id}/chunks/"
    params = {"limit": limit}

    with httpx.Client() as client:
        response = client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()


def _store_sources(data: list) -> str:
    # -- cache source chunks and format for LLM context --
    global current_sources
    current_sources = [
        {
            "chunk_id": str(d["chunk_id"]),
            "text": d["text"],
            "start_time": d.get("start_time"),
            "end_time": d.get("end_time"),
        }
        for d in data
    ]

    return "\n\n".join([f"Context:\n{d['text']}" for d in data])


##########################################################################
# Search Document Tool
##########################################################################
@tool 
def search_document(query: str, file_id: str) -> str:
    """
    Searches the user's uploaded document for relevant information. 
    You MUST use this tool to find context before answering any questions about the file. 
    Do not answer from your own knowledge.
    """
    # -- search document only when user explicitly needs information --
    global current_sources
    current_sources = []

    try:
        data = _vector_search(query, file_id)

        if not data:
            return "No relevant information found in the document."

        # -- cache sources for endpoint response --
        return _store_sources(data)
        
    except Exception as e:
        return f"Database search failed: {str(e)}"


def fetch_document_context(query: str, file_id: str):
    # -- direct vector search bypassing LangChain tool wrapper --
    global current_sources
    current_sources = []

    try:
        data = _vector_search(query, file_id)

        if not data:
            data = _fetch_file_chunks(file_id, limit=4)

        if not data:
            return "No relevant information found in the document."

        return _store_sources(data)
    except Exception as e:
        return f"Database search failed: {str(e)}"
    

##########################################################################
# Initialize Agent at Module Load
##########################################################################
# -- create Longcat LLM client --
llm = ChatOpenAI(
    api_key=settings.LONGCAT_API_KEY,
    base_url=settings.LONGCAT_BASE_URL,
    model=settings.LONGCAT_MODEL,
    temperature=0.3
)

# -- bind search tool to LLM --
tools = [search_document]

# -- system prompt for agent behavior --
system_prompt = SYSTEM_PROMPT

# -- build LangChain agent executor --
agent_executor = create_agent(llm, tools, system_prompt=system_prompt, debug=False)


##########################################################################
# Process Chat
##########################################################################
async def process_chat(session_id: str, query: str, file_id: str) -> tuple[str, list]:
    global current_sources
    current_sources = []

    # -- retrieve conversation history from memory --
    history = get_chat_history(session_id)

    # -- build contextual query with history for better retrieval --
    contextual_query = build_contextual_query(history, query)
    search_result = fetch_document_context(contextual_query, file_id)

    # -- return refusal if no relevant context found --
    if isinstance(search_result, str) and search_result.strip() == "No relevant information found in the document.":
        answer = "I cannot answer this based on the provided document."
        update_chat_history(session_id, query, answer)
        return answer, []

    # -- include retrieved context in agent input --
    context_message = HumanMessage(content=f"Retrieved context for document (file_id={file_id}):\n{search_result}")
    input_messages = history + [context_message, HumanMessage(content=f"User Query: {query}\n[Hidden System Note: If you need to search, use file_id '{file_id}']")]

    # -- run agent with enriched context --
    response = await agent_executor.ainvoke({"messages": input_messages})

    # -- extract answer from agent response --
    if isinstance(response.get("messages"), list) and len(response["messages"]) > 0:
        last_message = response["messages"][-1]
        answer = last_message.content if hasattr(last_message, "content") else str(last_message)
    else:
        answer = str(response.get("output", ""))

    # -- save to conversation memory --
    update_chat_history(session_id, query, answer)

    return answer, current_sources