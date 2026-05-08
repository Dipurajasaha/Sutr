import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import pytest_asyncio
from pathlib import Path

# Pre-mock heavy dependencies to avoid model downloads during test collection
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faiss'] = MagicMock()
# Provide a lightweight stub for langchain_core.tools.tool decorator used at import-time
import types
langchain_core_mod = types.ModuleType("langchain_core")
langchain_tools = types.ModuleType("langchain_core.tools")
def _tool_decorator(fn=None, **kwargs):
    # Pass-through decorator that returns the original function unchanged
    def decorator(func):
        return func
    if fn is not None:
        return decorator(fn)
    return decorator
langchain_tools.tool = _tool_decorator
langchain_core_mod.tools = langchain_tools
sys.modules['langchain_core'] = langchain_core_mod
sys.modules['langchain_core.tools'] = langchain_tools
sys.modules['langchain'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_core.language_models'] = MagicMock()
sys.modules['langchain.agents'] = MagicMock()

# Provide simple message classes used by agent_service
langchain_messages = types.ModuleType('langchain_core.messages')
class HumanMessage:
    def __init__(self, content=''):
        self.content = content
    type = "human"

class AIMessage:
    def __init__(self, content=''):
        self.content = content
    type = "ai"

class SystemMessage:
    def __init__(self, content=''):
        self.content = content
    type = "system"

langchain_messages.HumanMessage = HumanMessage
langchain_messages.AIMessage = AIMessage
langchain_messages.SystemMessage = SystemMessage
sys.modules['langchain_core.messages'] = langchain_messages

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services import memory_service


@pytest_asyncio.fixture
async def async_client():
    """Provide an async HTTP client for testing endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.Client for testing search_document tool."""
    with patch("httpx.Client") as mock:
        yield mock


@pytest.fixture
def mock_agent_executor():
    """Mock the agent executor for testing."""
    with patch("app.services.agent_service.agent_executor") as mock:
        yield mock


@pytest.fixture(autouse=True)
def isolated_chat_history_store(tmp_path, monkeypatch):
    """Keep chat history tests isolated from the real persistent store."""
    history_file = tmp_path / "chat_history.json"
    monkeypatch.setattr(memory_service.settings, "CHAT_HISTORY_PATH", str(history_file), raising=False)
    memory_service._chat_histories.clear()
    if history_file.exists():
        history_file.unlink()

    yield

    memory_service._chat_histories.clear()
