import httpx
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.services.memory_service import get_chat_history, update_chat_history


#####################################################################################
# -- global variable to cache sources when the tool is used --
#####################################################################################
current_sources = []


#####################################################################################
# -- the tool function that will be called by the agent when it needs to search the document --
#####################################################################################
@tool 
def search_document(query: str, file_id: str) -> str:
    """Use this tool ONLY when you need to retrieve information from the user's uploaded document."""
    global current_sources
    current_sources = []    # --> reset sources for this turn

    url = f"{settings.VECTOR_SERVICE_URL}/api/v1/vectors/search/"
    payload = {"query": query, "file_id": file_id, "top_k": 4}

    # -- using standard sync httpx inside the tool for stable  LangChain integration --
    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return "No relevant information found in the document."

            # -- save the sources globally so the endpoint can return them to the UI --
            current_sources = [
                {
                    "chunk_id": str(d["chunk_id"]),
                    "text": d["text"],
                    "start_time": d.get("start_time"),
                    "end_time": d.get("end_time"),
                }
                for d in data
            ]

            # -- returns the compiled text to the LLM --
            return "\n\n".join([f"Context:\n{d['text']}" for d in data])
        
    except Exception as e:
        return f"Database search failed: {str(e)}"
    
###################################################################################
# -- Initialize the agent at the module level so it is created only once when the service starts --
###################################################################################
# -- 1. initialize the Longcat LLM --
llm = ChatOpenAI(
    api_key=settings.LONGCAT_API_KEY,
    base_url=settings.LONGCAT_BASE_URL,
    model=settings.LONGCAT_MODEL,
    temperature=0.3
)

# -- 2. bind the tool to the LLM --
tools = [search_document]

# -- 3. system prompt for the agent --
system_prompt = (
    "You are Sutr, a helpful and intelligent AI assistant. "
    "You have access to a tool called 'search_document'. "
    "If the user asks a question about their uploaded document, video, or audio, you MUST use the tool to find the answer. "
    "If they are just chatting (e.g., 'hello', 'who are you'), answer naturally without using the tool. "
    "You are a strict document analysis assistant. You must answer the user's question using ONLY the provided context chunks. If the answer cannot be found in the context, you must reply exactly with: 'I cannot answer this based on the provided document.' Do not use outside knowledge. Do not hallucinate."
)

# -- 4. build the agent using the new LangChain API --
agent_executor = create_agent(llm, tools, system_prompt=system_prompt, debug=False)


#####################################################################################
# -- Runs the agent and manages memory --
#####################################################################################
async def process_chat(session_id: str, query: str, file_id: str) -> tuple[str, list]:
    global current_sources
    current_sources = []    # --> reset before execution

    history = get_chat_history(session_id)  # --> get current memory

    # -- Build the input messages with history --
    input_messages = history + [HumanMessage(content=f"User Query: {query}\n[Hidden System Note: If you need to search, use file_id '{file_id}']")]

    # -- execute the agent --
    response = await agent_executor.ainvoke({"messages": input_messages})

    # -- Extract the answer from the response --
    if isinstance(response.get("messages"), list) and len(response["messages"]) > 0:
        last_message = response["messages"][-1]
        answer = last_message.content if hasattr(last_message, "content") else str(last_message)
    else:
        answer = str(response.get("output", ""))

    # update memory
    update_chat_history(session_id, query, answer)

    return answer, current_sources