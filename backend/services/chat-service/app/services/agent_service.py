import httpx
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
            current_sources = [{"chunk_id": str(d["chunk_id"]), "text": d["text"]} for d in data]

            # -- returns the compiled text to the LLM --
            return "\n\n".join([f"Context:\n{d['text']}" for d in data])
        
    except Exception as e:
        return f"Database search failed: {str(e)}"
    
###################################################################################
# -- Initialize the agent and related components at the module level so they are created only once when the service starts --
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

# -- 3. create the prompt template supporting memory --
prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# -- 4. build the agent executor --
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


#####################################################################################
# -- Runs the agent and manages memory --
#####################################################################################
async def process_chat(session_id: str, query: str, file_id: str) -> tuple[str, list]:
    global current_sources
    current_sources = []    # --> reset before execution

    history = get_chat_history(session_id)  # --> get current memory

    # -- execute the agent --
    response = await agent_executor.ainvoke({
        "input": f"User Query: {query}\n[Hidden System Note: If you need to search, use file_id '{file_id}']",
        "chat_history": history
    })

    answer = response["output"]

    # update memory
    update_chat_history(session_id, query, answer)

    return answer, current_sources