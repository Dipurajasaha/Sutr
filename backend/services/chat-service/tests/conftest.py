import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import pytest_asyncio

# Pre-mock heavy dependencies to avoid model downloads during test collection
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faiss'] = MagicMock()

from httpx import AsyncClient, ASGITransport
from app.main import app


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
