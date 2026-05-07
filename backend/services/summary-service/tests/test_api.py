import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.models.chunk import TextChunk
from app.services.summary_manager import generate_summary

# -- Import test database session factory from conftest --
# We'll create our own TestingSessionLocal here for accessing the test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_summary.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

##########################################################################################
# -- tests the health check --
##########################################################################################
@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "summary-service"

##########################################################################################
# -- tests summarization with successful chunk retrieval and mocked LLM (short summary) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_success_short(mock_client):
    # -- 1. Mock the LLM response --
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="This is a short summary."))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # -- 2. Seed the test DB with chunks --
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Part 1"))
        session.add(TextChunk(file_id=file_id, chunk_index=1, text="Part 2"))
        await session.commit()

    # -- 3. Call the API --
    payload = {"file_id": str(file_id), "summary_type": "short"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)

    assert response.status_code == 200
    assert response.json()["summary"] == "This is a short summary."
    assert response.json()["summary_type"] == "short"

##########################################################################################
# -- tests summarization with detailed summary type --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_success_detailed(mock_client):
    # -- 1. Mock the LLM response --
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Key points: \n- Point 1\n- Point 2"))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # -- 2. Seed the test DB with chunks --
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Section 1"))
        session.add(TextChunk(file_id=file_id, chunk_index=1, text="Section 2"))
        session.add(TextChunk(file_id=file_id, chunk_index=2, text="Section 3"))
        await session.commit()

    # -- 3. Call the API --
    payload = {"file_id": str(file_id), "summary_type": "detailed"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)

    assert response.status_code == 200
    assert "Key points" in response.json()["summary"]
    assert response.json()["summary_type"] == "detailed"

##########################################################################################
# -- tests behavior when no chunks are found --
##########################################################################################
@pytest.mark.asyncio
async def test_generate_summary_no_content():
    payload = {"file_id": str(uuid.uuid4()), "summary_type": "detailed"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)

    assert response.status_code == 200
    assert "No content found" in response.json()["summary"]

##########################################################################################
# -- tests error handling during LLM call --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_llm_failure(mock_client):
    # -- 1. Mock an API exception --
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Timeout"))
    
    # -- 2. Seed test DB with chunks --
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Data"))
        await session.commit()

    # -- 3. Call the API --
    payload = {"file_id": str(file_id), "summary_type": "short"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)

    # -- 4. Verify error handling --
    assert response.status_code == 200
    assert "Summarization failed" in response.json()["summary"]

##########################################################################################
# -- tests validation error for invalid UUID format --
##########################################################################################
@pytest.mark.asyncio
async def test_generate_summary_validation_error():
    """Test that invalid UUID format returns 422 validation error"""
    payload = {"file_id": "not-a-uuid", "summary_type": "short"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)
    
    # FastAPI validates UUID at schema level
    assert response.status_code == 422

##########################################################################################
# -- tests default summary type (should use detailed) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_default_type(mock_client):
    # -- 1. Mock the LLM response --
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Detailed summary here."))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # -- 2. Seed the test DB with chunks --
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Content"))
        await session.commit()

    # -- 3. Call the API without specifying summary_type --
    payload = {"file_id": str(file_id)}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/summary/generate/", json=payload)

    assert response.status_code == 200
    assert "Detailed summary here" in response.json()["summary"]

##########################################################################################
# -- database coverage --
##########################################################################################
##########################################################################################
# -- DIRECT UNIT TESTS for generate_summary function (for coverage) --
##########################################################################################

@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_short_coverage(mock_client):
    """Direct test of generate_summary with short summary type"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Short summary result."))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Chunk 1"))
        session.add(TextChunk(file_id=file_id, chunk_index=1, text="Chunk 2"))
        await session.commit()
    
    # -- Call generate_summary directly --
    async with TestingSessionLocal() as session:
        result = await generate_summary(session, str(file_id), "short")
    
    assert result == "Short summary result."
    # -- Verify the mock was called with correct params --
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args
    assert "Provide a concise 3-5 sentence summary" in str(call_args)

@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_detailed_coverage(mock_client):
    """Direct test of generate_summary with detailed summary type"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Detailed summary with bullet points."))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Section A"))
        session.add(TextChunk(file_id=file_id, chunk_index=1, text="Section B"))
        await session.commit()
    
    # -- Call generate_summary directly --
    async with TestingSessionLocal() as session:
        result = await generate_summary(session, str(file_id), "detailed")
    
    assert result == "Detailed summary with bullet points."
    # -- Verify the mock was called with correct params --
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args
    assert "Provide a detailed summary" in str(call_args)

@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_no_chunks_coverage(mock_client):
    """Direct test when no chunks are found"""
    file_id = uuid.uuid4()
    
    # -- Don't add any chunks, just call with empty DB --
    async with TestingSessionLocal() as session:
        result = await generate_summary(session, str(file_id), "short")
    
    assert result == "No content found to summarize."
    # -- Verify the mock was NOT called since we returned early --
    mock_client.chat.completions.create.assert_not_called()

@pytest.mark.asyncio
@patch("app.services.summary_manager.client")
async def test_generate_summary_llm_error_coverage(mock_client):
    """Direct test of error handling in LLM call"""
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Network timeout"))
    
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Content"))
        await session.commit()
    
    # -- Call generate_summary directly --
    async with TestingSessionLocal() as session:
        result = await generate_summary(session, str(file_id), "short")
    
    assert "Summarization failed: Network timeout" == result

@pytest.mark.asyncio
async def test_generate_summary_uuid_conversion_coverage():
    """Direct test of UUID conversion logic"""
    file_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(TextChunk(file_id=file_id, chunk_index=0, text="Test"))
        await session.commit()
    
    # -- Test with string UUID (should convert) --
    with patch("app.services.summary_manager.client") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Result"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        async with TestingSessionLocal() as session:
            # -- Pass as string, function should convert --
            result = await generate_summary(session, str(file_id), "short")
        
        assert result == "Result"

@pytest.mark.asyncio
async def test_generate_summary_invalid_uuid_format():
    """Direct test of invalid UUID format error handling"""
    # -- Pass an invalid UUID string --
    async with TestingSessionLocal() as session:
        result = await generate_summary(session, "not-a-valid-uuid", "short")
    
    assert result == "Invalid file_id format."

@pytest.mark.asyncio
async def test_get_db_coverage():
    from app.core.database import get_db
    async for session in get_db():
        assert session is not None
        break