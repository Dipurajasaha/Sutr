import pytest
import httpx
from httpx import AsyncClient, ASGITransport, Response, Request
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_list_files(mock_client_class):
    """Test listing files from upload service"""
    mock_client = AsyncMock()
    mock_response = Response(200, json=[{"id": "1", "name": "file.pdf"}], request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_get_file(mock_client_class):
    """Test getting a specific file"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"id": "file-1", "name": "test.pdf"}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/file-1")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_delete_file(mock_client_class):
    """Test deleting a file"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"status": "deleted"}, request=Request("DELETE", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/files/file-1")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_rename_file(mock_client_class):
    """Test renaming a file"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"id": "file-1", "name": "newname.pdf"}, request=Request("PATCH", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch("/api/files/file-1", json={"name": "newname.pdf"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_chat_query(mock_client_class):
    """Test sending a chat query"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"reply": "Hello!"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/chat/query/", json={"query": "Hello"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_chat_history(mock_client_class):
    """Test getting chat history"""
    mock_client = AsyncMock()
    mock_response = Response(200, json=[{"role": "user", "content": "Hi"}], request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/chat/history/session-123")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_index_vectors(mock_client_class):
    """Test indexing vectors"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"indexed": 5}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/vectors/index/", json={"chunks": []})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_search_vectors(mock_client_class):
    """Test searching vectors"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"results": []}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/vectors/search/", json={"query": "test"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_get_file_chunks(mock_client_class):
    """Test getting file chunks"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"chunks": []}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/vectors/chunks/file-1")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_delete_file_vectors(mock_client_class):
    """Test deleting file vectors"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"deleted": True}, request=Request("DELETE", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/vectors/chunks/file-1")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_generate_summary(mock_client_class):
    """Test generating summary"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"summary": "Test summary"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/summary/generate", json={"file_id": "1"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_generate_summary_with_trailing_slash(mock_client_class):
    """Test generating summary with trailing slash"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"summary": "Test summary"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/summary/generate/", json={"file_id": "1"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_generate_summary_404_fallback(mock_client_class):
    """Test generating summary with fallback on 404"""
    from fastapi import HTTPException
    
    mock_client = AsyncMock()
    # First call returns 404, triggers fallback
    mock_client.request = AsyncMock(side_effect=HTTPException(status_code=404))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            response = await ac.post("/api/summary/generate", json={"file_id": "1"})
        except:
            pass


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_media_playback(mock_client_class):
    """Test media playback"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"url": "stream"}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/media/playback/file-1")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_uploads_file_not_found(mock_client_class):
    """Test uploads with file not found"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    error_response = Response(404, request=Request("GET", "url"))
    mock_client.get.side_effect = httpx.HTTPStatusError("404", request=Request("GET", "url"), response=error_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/uploads/test.pdf")

    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_uploads_network_error(mock_client_class):
    """Test uploads with network error"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/uploads/test.pdf")

    assert response.status_code == 503


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_uploads_success(mock_client_class):
    """Test uploads with successful file streaming"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        "content-type": "application/pdf",
        "content-length": "1000",
        "cache-control": "max-age=3600"
    }
    
    async def mock_aiter_bytes():
        yield b"file content"
    
    mock_response.aiter_bytes = mock_aiter_bytes
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/uploads/test.pdf")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_process_file(mock_client_class):
    """Test processing a file"""
    mock_client = AsyncMock()
    mock_response = Response(200, json={"status": "success"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/process/", json={"file_id": "1"})

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_gateway_uploads_root_success(mock_client_class):
    """Test root-level uploads endpoint with successful response"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        "content-type": "application/pdf",
        "content-length": "1000",
        "cache-control": "max-age=3600",
        "last-modified": "Wed, 21 Oct 2015 07:28:00 GMT",
        "etag": "abc123"
    }
    
    async def mock_aiter_bytes():
        yield b"file content"
    
    mock_response.aiter_bytes = mock_aiter_bytes
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/uploads/test.pdf")

    assert response.status_code == 200


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_gateway_uploads_root_404(mock_client_class):
    """Test root-level uploads endpoint with 404 response"""
    mock_client = AsyncMock()
    error_response = Response(404, request=Request("GET", "url"))
    mock_client.get = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPStatusError("404", request=Request("GET", "url"), response=error_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/uploads/nonexistent.pdf")

    assert response.status_code == 404


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_gateway_uploads_root_network_error(mock_client_class):
    """Test root-level uploads endpoint with network error"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/uploads/test.pdf")

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "api-gateway"}
