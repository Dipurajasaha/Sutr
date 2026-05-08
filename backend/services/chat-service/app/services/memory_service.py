import json
from pathlib import Path
from threading import Lock

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.config import settings


SYSTEM_PROMPT = (
    "You are Sutr, a helpful and intelligent AI assistant. "
    "You have access to a tool called 'search_document'. "
    "If the user asks a question about their uploaded document, video, or audio, you MUST use the tool to find the answer. "
    "If they are just chatting (e.g., 'hello', 'who are you'), answer naturally without using the tool. "
    "You are a strict document analysis assistant. You must answer the user's question using ONLY the provided context chunks. If the answer cannot be found in the context, you must reply exactly with: 'I cannot answer this based on the provided document.' Do not use outside knowledge. Do not hallucinate."
)


# -- in-memory cache: { session_id: [SystemMessage, HumanMessage, AIMessage, ...] } --
_chat_histories: dict[str, list] = {}
_chat_store_lock = Lock()


def _history_path() -> Path:
    return Path(settings.CHAT_HISTORY_PATH)


def _load_persistent_store() -> dict[str, list[dict]]:
    path = _history_path()
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_persistent_store(store: dict[str, list[dict]]) -> None:
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(store, file, ensure_ascii=False, indent=2)


def _message_to_record(message) -> dict | None:
    if isinstance(message, HumanMessage):
        return {"role": "human", "content": message.content}
    if isinstance(message, AIMessage):
        return {"role": "ai", "content": message.content}
    return None


def _record_to_message(record: dict):
    role = record.get("role")
    content = record.get("content", "")

    if role == "human":
        return HumanMessage(content=content)
    if role == "ai":
        return AIMessage(content=content)
    return None

##########################################################################################
# -- retrieves the chat history for a session, initializing if empty --
##########################################################################################
def get_chat_history(session_id: str) -> list:
    if session_id not in _chat_histories:
        persistent_store = _load_persistent_store()
        records = persistent_store.get(session_id, [])
        session_messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for record in records:
            message = _record_to_message(record)
            if message is not None:
                session_messages.append(message)

        _chat_histories[session_id] = session_messages

    return _chat_histories[session_id]


##########################################################################################
# -- adds the new exchange and enforces the 10-conversation (20 messages) limit --
##########################################################################################
def update_chat_history(session_id: str, human_text: str, ai_text: str):
    # -- get the current history if it does not exist yet --
    history = get_chat_history(session_id)
    history.append(HumanMessage(content=human_text))
    history.append(AIMessage(content=ai_text))

    # -- keep the system message at index 0 and retain only the last 20 messages --
    if len(history) > 21:
        _chat_histories[session_id] = [history[0]] + history[-20:]

    with _chat_store_lock:
        store = _load_persistent_store()
        session_records = []
        for message in _chat_histories[session_id][1:]:
            record = _message_to_record(message)
            if record is not None:
                session_records.append(record)

        store[session_id] = session_records
        _save_persistent_store(store)


def get_chat_history_records(session_id: str) -> list[dict]:
    # -- return the stored conversation turns without the system prompt --
    history = get_chat_history(session_id)
    records: list[dict] = []

    for message in history[1:]:
        record = _message_to_record(message)
        if record is not None:
            records.append(record)

    return records