import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test that GET /health returns 200 with status healthy."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ask_question_success(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ with valid input and mocked agent."""
    with patch("app.api.endpoints.process_chat") as mock_process_chat:
        # Mock the tuple returned by process_chat (answer, sources)
        mock_process_chat.return_value = (
            "This is a mocked answer from the agent.",
            [{"chunk_id": "123e4567-e89b-12d3-a456-426614174000", "text": "Source text snippet"}]
        )

        payload = {
            "session_id": "test_session_1",
            "query": "What is in the document?",
            "file_id": "123e4567-e89b-12d3-a456-426614174000"
        }

        response = await async_client.post("/api/v1/chat/query/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a mocked answer from the agent."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_id"] == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_ask_question_empty_sources(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ when agent returns no sources."""
    with patch("app.api.endpoints.process_chat") as mock_process_chat:
        mock_process_chat.return_value = ("No sources found", [])

        payload = {
            "session_id": "test_session_2",
            "query": "What is not in the document?",
            "file_id": "nonexistent-file"
        }

        response = await async_client.post("/api/v1/chat/query/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "No sources found"
        assert data["sources"] == []


@pytest.mark.asyncio
async def test_ask_question_multiple_sources(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ with multiple sources in response."""
    with patch("app.api.endpoints.process_chat") as mock_process_chat:
        mock_process_chat.return_value = (
            "Found multiple sources",
            [
                {"chunk_id": "chunk-1", "text": "First source"},
                {"chunk_id": "chunk-2", "text": "Second source"},
                {"chunk_id": "chunk-3", "text": "Third source"}
            ]
        )

        payload = {
            "session_id": "test_session_3",
            "query": "Find everything",
            "file_id": "file-789"
        }

        response = await async_client.post("/api/v1/chat/query/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Found multiple sources"
        assert len(data["sources"]) == 3


@pytest.mark.asyncio
async def test_ask_question_missing_session_id(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ with missing session_id field."""
    payload = {
        "query": "What is the answer?",
        "file_id": "file-123"
    }

    response = await async_client.post("/api/v1/chat/query/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_ask_question_missing_query(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ with missing query field."""
    payload = {
        "session_id": "test-session",
        "file_id": "file-123"
    }

    response = await async_client.post("/api/v1/chat/query/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_question_missing_file_id(async_client: AsyncClient):
    """Test POST /api/v1/chat/query/ with missing file_id field."""
    payload = {
        "session_id": "test-session",
        "query": "What is the question?"
    }

    response = await async_client.post("/api/v1/chat/query/", json=payload)
    assert response.status_code == 422