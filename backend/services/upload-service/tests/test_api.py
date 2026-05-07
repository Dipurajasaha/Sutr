import pytest
import uuid
from io import BytesIO
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, Mock
from fastapi import UploadFile, HTTPException

from app.main import app, startup_event
from app.core.config import settings
from app.api.endpoints import upload_file, get_file_status
from app.services.upload_manager import create_file_metadata
from app.models.file import FileMetadata

##########################################################################################
# -- tests the application startup event for database initialization coverage --
##########################################################################################
@pytest.mark.asyncio
@patch("app.main.engine")  # <-- Patch the entire engine object instead of .begin()
async def test_startup_event(mock_engine):
    # -- Mock the async context manager behavior --
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    
    await startup_event()
    
    # -- Verify that the code attempted to create tables --
    mock_conn.run_sync.assert_called_once()

##########################################################################################
# -- tests the health check endpoint --
##########################################################################################
@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "upload-service"}

##########################################################################################
# -- tests rejecting an unsupported file type --
##########################################################################################
@pytest.mark.asyncio
async def test_upload_invalid_file_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.txt", b"dummy content", "text/plain")}
        response = await ac.post("/api/v1/upload/", files=files)
        
    assert response.status_code == 400
    assert "File type not supported" in response.json()["detail"]

##########################################################################################
# -- tests successful PDF upload and file persistence --
##########################################################################################
@pytest.mark.asyncio
async def test_upload_valid_document(tmp_path):
    # Override the upload directory to a temporary pytest path to avoid cluttering local storage
    settings.UPLOAD_DIR = str(tmp_path)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test_doc.pdf", b"dummy pdf content", "application/pdf")}
        response = await ac.post("/api/v1/upload/", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_doc.pdf"
    assert data["file_type"] == "document"
    assert data["status"] == "uploaded"
    assert "id" in data

##########################################################################################
# -- tests successful audio categorization --
##########################################################################################
@pytest.mark.asyncio
async def test_upload_valid_audio(tmp_path):
    settings.UPLOAD_DIR = str(tmp_path)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test_audio.mp3", b"dummy audio content", "audio/mpeg")}
        response = await ac.post("/api/v1/upload/", files=files)
        
    assert response.status_code == 200
    assert response.json()["file_type"] == "audio"

##########################################################################################
# -- tests successful video categorization --
##########################################################################################
@pytest.mark.asyncio
async def test_upload_valid_video(tmp_path):
    settings.UPLOAD_DIR = str(tmp_path)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test_video.mp4", b"dummy video content", "video/mp4")}
        response = await ac.post("/api/v1/upload/", files=files)
        
    assert response.status_code == 200
    assert response.json()["file_type"] == "video"

##########################################################################################
# -- tests retrieving a file that was successfully uploaded --
##########################################################################################
@pytest.mark.asyncio
async def test_get_file_status_success(tmp_path):
    settings.UPLOAD_DIR = str(tmp_path)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload a file to generate a valid DB record
        files = {"file": ("test_doc.pdf", b"dummy pdf content", "application/pdf")}
        upload_response = await ac.post("/api/v1/upload/", files=files)
        file_id = upload_response.json()["id"]
        
        # 2. Fetch the metadata using the generated ID
        response = await ac.get(f"/api/v1/files/{file_id}")
        
    assert response.status_code == 200
    assert response.json()["id"] == file_id

##########################################################################################
# -- tests retrieving a file ID that does not exist --
##########################################################################################
@pytest.mark.asyncio
async def test_get_file_status_not_found():
    # Generate a random UUID that is guaranteed not to be in the test DB
    fake_id = str(uuid.uuid4())
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/files/{fake_id}")
        
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"

##########################################################################################
# -- hits the core database generator to ensure full coverage lines --
##########################################################################################
@pytest.mark.asyncio
async def test_get_db_coverage():
    from app.core.database import get_db
    async for session in get_db():
        assert session is not None
        break

##########################################################################################
# -- tests secondary video format to guarantee 100% branch coverage on routing --
##########################################################################################
@pytest.mark.asyncio
async def test_upload_valid_video_mkv(tmp_path):
    settings.UPLOAD_DIR = str(tmp_path)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test_video.mkv", b"dummy mkv content", "video/x-matroska")}
        response = await ac.post("/api/v1/upload/", files=files)
        
    assert response.status_code == 200
    assert response.json()["file_type"] == "video"

##########################################################################################
# -- tests the upload endpoint function directly to cover the final return path --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.create_file_metadata", new_callable=AsyncMock)
@patch("app.api.endpoints.save_file_to_disk", new_callable=AsyncMock)
@patch("app.api.endpoints.uuid.uuid4")
async def test_upload_file_function_returns_created_metadata(mock_uuid4, mock_save_file, mock_create_metadata):
    mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    mock_save_file.return_value = "/tmp/uploads/12345678-1234-5678-1234-567812345678.pdf"

    expected_file = FileMetadata(
        filename="direct-test.pdf",
        file_type="document",
        file_path="/tmp/uploads/12345678-1234-5678-1234-567812345678.pdf",
        status="uploaded",
    )
    mock_create_metadata.return_value = expected_file

    upload = UploadFile(filename="direct-test.pdf", file=BytesIO(b"pdf-bytes"))
    result = await upload_file(upload, db=AsyncMock())

    assert result is expected_file
    mock_save_file.assert_awaited_once()
    mock_create_metadata.assert_awaited_once()
    assert mock_create_metadata.await_args.args[2] == "document"

##########################################################################################
# -- tests the metadata helper directly so commit and refresh are covered explicitly --
##########################################################################################
@pytest.mark.asyncio
async def test_create_file_metadata_persists_and_refreshes():
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    result = await create_file_metadata(db, "file.pdf", "document", "/tmp/file.pdf")

    assert isinstance(result, FileMetadata)
    assert result.filename == "file.pdf"
    assert result.file_type == "document"
    assert result.file_path == "/tmp/file.pdf"
    assert result.status == "uploaded"
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)

##########################################################################################
# -- tests the file lookup endpoint directly for the success branch --
##########################################################################################
@pytest.mark.asyncio
async def test_get_file_status_direct_success():
    expected_file = FileMetadata(
        filename="lookup.pdf",
        file_type="document",
        file_path="/tmp/lookup.pdf",
        status="uploaded",
    )
    expected_file.id = uuid.UUID("12345678-1234-5678-1234-567812345678")

    result = Mock()
    result.scalar_one_or_none.return_value = expected_file

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    file_record = await get_file_status(expected_file.id, db=db)

    assert file_record is expected_file
    db.execute.assert_awaited_once()

##########################################################################################
# -- tests the file lookup endpoint directly for the 404 branch --
##########################################################################################
@pytest.mark.asyncio
async def test_get_file_status_direct_not_found():
    result = Mock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc_info:
        await get_file_status(uuid.uuid4(), db=db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "File not found"
    db.execute.assert_awaited_once()