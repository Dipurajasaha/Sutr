from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


# -- in-memory store: { session_id: [List of Messages] } -- 
_chat_histories: dict[str, list] = {}

##########################################################################################
# -- retrieves the chat history for a session, initializing if empty --
##########################################################################################
def get_chat_history(session_id: str) -> list:
    if session_id not in _chat_histories:
        # -- initialize with the system prompt --
        _chat_histories[session_id] = [
            SystemMessage(content=(
                "You are Sutr, a helpful and intelligent AI assistant. "
                "You have access to a tool called 'search_document'. "
                "If the user asks a question about their uploaded document, video, or audio, you MUST use the tool to find the answer. "
                "If they are just chatting (e.g., 'hello', 'who are you'), answer naturally without using the tool. "
                "You are a strict document analysis assistant. You must answer the user's question using ONLY the provided context chunks. If the answer cannot be found in the context, you must reply exactly with: 'I cannot answer this based on the provided document.' Do not use outside knowledge. Do not hallucinate."
            ))
        ]
    return  _chat_histories[session_id]


##########################################################################################
# -- adds the new exchange and enforces the 10-conversation (20 messages) limit --
##########################################################################################
def update_chat_history(session_id: str, human_text: str, ai_text: str):
    history = get_chat_history(session_id)      # --> get the current history (initializes if not exists)
    history.append(HumanMessage(content=human_text))
    history.append(AIMessage(content=ai_text))

    # -- # Keep the system message (index 0), but slice the rest to keep only the last 20 messages (10 pairs) --
    if len(history) > 21:
        _chat_histories[session_id] = [history[0]] + history[-20:]