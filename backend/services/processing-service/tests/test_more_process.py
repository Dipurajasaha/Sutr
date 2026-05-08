import uuid
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import RequestError

from app.api.endpoints import process_file
from app.schemas.process import ProcessRequest
import importlib
import sys


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_no_valid_chunks(mock_process_pdf, mock_exists):
    # returned data contains only empty/whitespace texts -> should raise 400
    mock_process_pdf.return_value = [
        {"text": "   ", "start_time": None, "end_time": None},
        {"text": "", "start_time": None, "end_time": None},
    ]

    req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
    with pytest.raises(Exception) as exc:
        await process_file(req, db=AsyncMock())

    # Expect HTTPException or similar indicating no valid transcript
    assert "No valid transcript" in str(exc.value)


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
@patch("app.api.endpoints.httpx.AsyncClient")
async def test_process_file_vector_service_unavailable(mock_async_client_cls, mock_process_pdf, mock_exists):
    # valid chunks
    mock_process_pdf.return_value = [
        {"text": "Chunk one", "start_time": None, "end_time": None}
    ]

    # Make the AsyncClient context manager whose post raises RequestError
    class BadClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise RequestError("Connection failed")

    mock_async_client_cls.return_value = BadClient()

    req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
    resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
def test_media_parser_and_ffmpeg_stub(monkeypatch, tmp_path):
    """Test that media_parser loads and handles FFmpeg properly"""
    # This test verifies the module can be imported and used without crashing
    # even when FFmpeg or Whisper have issues
    from app.services.media_parser import process_media, model
    
    # Test 1: Module imported successfully
    assert True
    
    # Test 2: process_media handles non-existent files gracefully
    result = process_media(str(tmp_path / "nonexistent.mp3"))
    assert isinstance(result, list)
    assert result == []  # Should return empty list, not crash


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_triggers_summary(mock_process_pdf, mock_exists):
    # valid chunks
    mock_process_pdf.return_value = [
        {"text": "Chunk one", "start_time": None, "end_time": None}
    ]

    # Fake AsyncClient to handle vector and summary calls
    class GoodClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, timeout=None):
            if "/vectors/index/" in url:
                class R: status_code = 201
                def raise_for_status(self):
                    return None
                return R()
            if "/summary/generate" in url:
                class R:
                    status_code = 200
                    def raise_for_status(self):
                        return None
                    def json(self):
                        return {"summary": "quick summary"}
                return R()
            return MagicMock()

        async def patch(self, url, json=None, timeout=None):
            class R: status_code = 200
            return R()

    with patch("app.api.endpoints.httpx.AsyncClient", return_value=GoodClient()):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_sanitize_bytes(mock_process_pdf, mock_exists):
    # Test _sanitize_chunk_text with bytes input containing null bytes
    mock_process_pdf.return_value = [
        {"text": b"Chunk with \x00 null byte", "start_time": None, "end_time": None}
    ]

    with patch("app.api.endpoints.httpx.AsyncClient"):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_sanitize_none(mock_process_pdf, mock_exists):
    # Test _sanitize_chunk_text with None text
    mock_process_pdf.return_value = [
        {"text": None, "start_time": None, "end_time": None},
        {"text": "Valid chunk", "start_time": None, "end_time": None}
    ]

    with patch("app.api.endpoints.httpx.AsyncClient"):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
@patch("app.api.endpoints.process_pdf")
async def test_process_file_path_resolution_fallback(mock_process_pdf):
    # Test the path candidate resolution - abs path doesn't exist but fallback does
    def path_exists_side_effect(path):
        # Only the fallback candidate exists
        return "/fake.pdf" in path or "upload-service" in path

    mock_process_pdf.return_value = [
        {"text": "Fallback path worked", "start_time": None, "end_time": None}
    ]

    with patch("app.api.endpoints.os.path.exists", side_effect=path_exists_side_effect):
        with patch("app.api.endpoints.httpx.AsyncClient"):
            req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="fake.pdf", file_type="document")
            resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_media_type(mock_process_pdf, mock_exists):
    # Test routing to process_media for audio/video
    with patch("app.api.endpoints.process_media") as mock_process_media:
        mock_process_media.return_value = [
            {"text": "Audio chunk", "start_time": 0.0, "end_time": 1.5}
        ]
        with patch("app.api.endpoints.httpx.AsyncClient"):
            req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/audio.mp3", file_type="audio")
            resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"
    assert resp.total_chunks == 1


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_unsupported_type(mock_process_pdf, mock_exists):
    # Test unsupported file type rejection
    req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/file.xyz", file_type="unknown")
    with pytest.raises(Exception) as exc:
        await process_file(req, db=AsyncMock())

    assert "Unsupported file type" in str(exc.value)


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_vector_service_error_response(mock_process_pdf, mock_exists):
    # Test vector-service returning error status code
    mock_process_pdf.return_value = [
        {"text": "Chunk", "start_time": None, "end_time": None}
    ]

    class BadVectorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *args, **kwargs):
            if "/vectors/index/" in url:
                class BadResp:
                    status_code = 500
                    def raise_for_status(self):
                        raise Exception("Vector service error")
                return BadResp()
            if "/summary/generate" in url:
                class R:
                    status_code = 200
                    def raise_for_status(self):
                        pass
                    def json(self):
                        return {"summary": "test"}
                return R()
            return MagicMock()

        async def patch(self, url, *args, **kwargs):
            class R: status_code = 200
            return R()

    with patch("app.api.endpoints.httpx.AsyncClient", return_value=BadVectorClient()):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_summary_service_error(mock_process_pdf, mock_exists):
    # Test summary-service failure doesn't crash entire pipeline
    mock_process_pdf.return_value = [
        {"text": "Chunk", "start_time": None, "end_time": None}
    ]

    class SummaryErrorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *args, **kwargs):
            if "/vectors/index/" in url:
                class R: status_code = 201
                def raise_for_status(self): pass
                return R()
            if "/summary/generate" in url:
                raise Exception("Summary service down")
            return MagicMock()

        async def patch(self, url, *args, **kwargs):
            class R: status_code = 200
            return R()

    with patch("app.api.endpoints.httpx.AsyncClient", return_value=SummaryErrorClient()):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_general_exception(mock_process_pdf, mock_exists):
    # Test handling of general exceptions and rollback
    mock_process_pdf.side_effect = RuntimeError("Processing error")

    mock_db = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()

    req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
    with pytest.raises(Exception) as exc:
        await process_file(req, db=mock_db)

    assert "Processing error" in str(exc.value)
    mock_db.rollback.assert_called()


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_upload_service_patch_error(mock_process_pdf, mock_exists):
    # Test failure to patch summary to upload-service
    mock_process_pdf.return_value = [
        {"text": "Chunk", "start_time": None, "end_time": None}
    ]

    class PatchErrorClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *args, **kwargs):
            if "/vectors/index/" in url:
                class R: status_code = 201
                def raise_for_status(self): pass
                return R()
            if "/summary/generate" in url:
                class R:
                    status_code = 200
                    def raise_for_status(self): pass
                    def json(self):
                        return {"summary": "test"}
                return R()
            return MagicMock()

        async def patch(self, url, *args, **kwargs):
            raise Exception("Patch failed")

    with patch("app.api.endpoints.httpx.AsyncClient", return_value=PatchErrorClient()):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=False)
async def test_process_file_not_found(mock_exists):
    # Test file not found in all candidates
    req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/nonexistent.pdf", file_type="document")
    with pytest.raises(Exception) as exc:
        await process_file(req, db=AsyncMock())

    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
@patch("app.api.endpoints.os.path.exists", return_value=True)
@patch("app.api.endpoints.process_pdf")
async def test_process_file_summary_with_bad_json(mock_process_pdf, mock_exists):
    # Test summary generation when response.json() fails
    mock_process_pdf.return_value = [
        {"text": "Test", "start_time": None, "end_time": None}
    ]

    class BadJsonClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, *args, **kwargs):
            if "/vectors/index/" in url:
                class R: 
                    status_code = 201
                def raise_for_status(self): pass
                return R()
            if "/summary/generate" in url:
                class R:
                    status_code = 200
                    def raise_for_status(self): pass
                    def json(self):
                        raise ValueError("Invalid JSON")
                return R()
            return MagicMock()

        async def patch(self, url, *args, **kwargs):
            class R: status_code = 200
            return R()

    with patch("app.api.endpoints.httpx.AsyncClient", return_value=BadJsonClient()):
        req = ProcessRequest(file_id=str(uuid.uuid4()), file_path="/fake.pdf", file_type="document")
        resp = await process_file(req, db=AsyncMock())

    assert resp.status == "success"


def test_media_parser_ffmpeg_fallback():
    # Test that FFmpeg resolution works with imageio_ffmpeg fallback
    import tempfile
    import os as os_module
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake ffmpeg executable
        fake_ffmpeg_path = os_module.path.join(tmpdir, "ffmpeg")
        with open(fake_ffmpeg_path, "w") as f:
            f.write("#!/bin/bash\necho 'fake'\n")
        
        # Mock shutil.which to return None (ffmpeg not in PATH)
        def mock_which(prog):
            return None
        
        # Mock imageio_ffmpeg to provide the fallback
        mock_ffmpeg_module = MagicMock()
        mock_ffmpeg_module.get_ffmpeg_exe.return_value = fake_ffmpeg_path
        
        original_modules = sys.modules.copy()
        sys.modules["imageio_ffmpeg"] = mock_ffmpeg_module
        
        try:
            with patch("shutil.which", side_effect=mock_which):
                # Import and reload the module to trigger _ensure_ffmpeg_available
                import app.services.media_parser as mp
                importlib.reload(mp)
                # Verify it didn't crash
                assert True
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)
            importlib.reload(importlib.import_module("app.services.media_parser"))
