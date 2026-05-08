import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app, startup_event


class MockVectorResponse:
    status_code = 201

    def raise_for_status(self):
        return None


class MockVectorClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return MockVectorResponse()

##########################################################################################
# -- tests the application startup event for database initialization coverage --
##########################################################################################
@pytest.mark.asyncio
@patch("app.main.Base.metadata.create_all")
@patch("app.main.engine")
async def test_startup_event(mock_engine, mock_create_all):
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    await startup_event()
    mock_conn.run_sync.assert_awaited_once_with(mock_create_all)

##########################################################################################
# -- tests 404 when a file path does not physically exist --
##########################################################################################
@pytest.mark.asyncio
async def test_process_file_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "file_id": str(uuid.uuid4()),
            "file_path": "/fake/path/doesnotexist.pdf",
            "file_type": "document"
        }
        response = await ac.post("/api/v1/process/", json=payload)
        
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]

##########################################################################################
# -- tests successful document processing by mocking PyMuPDF --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True) # Trick API into thinking file exists
@patch("app.api.endpoints.process_pdf") # Mock the actual AI extraction
@patch("app.api.endpoints.httpx.AsyncClient", return_value=MockVectorClient())
async def test_process_document_success(mock_async_client, mock_process_pdf, mock_exists):
    # -- mock the AI returning chunked data --
    mock_process_pdf.return_value = [
        {"text": "Chunk 1 text", "start_time": None, "end_time": None},
        {"text": "Chunk 2 text", "start_time": None, "end_time": None}
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        file_id = str(uuid.uuid4())
        payload = {"file_id": file_id, "file_path": "/fake/doc.pdf", "file_type": "document"}
        response = await ac.post("/api/v1/process/", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_chunks"] == 2
    assert data["file_id"] == file_id

##########################################################################################
# -- tests successful media processing by mocking Whisper --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_media")
@patch("app.api.endpoints.httpx.AsyncClient", return_value=MockVectorClient())
async def test_process_media_success(mock_async_client, mock_process_media, mock_exists):
    mock_process_media.return_value = [
        {"text": "Hello world", "start_time": 0.0, "end_time": 2.5}
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"file_id": str(uuid.uuid4()), "file_path": "/fake/audio.mp3", "file_type": "audio"}
        response = await ac.post("/api/v1/process/", json=payload)
        
    assert response.status_code == 200
    assert response.json()["total_chunks"] == 1

##########################################################################################
# -- tests 400 for unsupported file types --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
async def test_process_unsupported_type(mock_exists):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"file_id": str(uuid.uuid4()), "file_path": "/fake/image.png", "file_type": "image"}
        response = await ac.post("/api/v1/process/", json=payload)
        
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type."

##########################################################################################
# -- hits the core database generator to ensure full coverage lines --
##########################################################################################
@pytest.mark.asyncio
async def test_get_db_coverage():
    from app.core.database import get_db
    async for session in get_db():
        assert session is not None
        break