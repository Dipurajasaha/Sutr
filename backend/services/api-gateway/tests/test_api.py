import pytest
import httpx
from httpx import AsyncClient, ASGITransport, Response, Request
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app

##########################################################################################
# -- tests the health check endpoint --
##########################################################################################
@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "api-gateway"}

##########################################################################################
# -- tests forwarding a multipart file upload --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_upload_success(mock_client_class):
    # -- Setup the mock client instance --
    mock_client = AsyncMock()
    mock_response = Response(200, json={"id": "file-123", "status": "uploaded"}, request=Request("POST", "url"))
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.pdf", b"dummy content", "application/pdf")}
        response = await ac.post("/api/upload/", files=files)

    assert response.status_code == 200
    assert response.json()["id"] == "file-123"

##########################################################################################
# -- tests forwarding a standard JSON POST request (Process Service) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_process_success(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"status": "success"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/process/", json={"file_id": "123"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"

##########################################################################################
# -- tests forwarding a standard GET request (Media Playback) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_media_success(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"segments": []}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/media/playback/file-123?chunk_ids=c-1")

    assert response.status_code == 200

##########################################################################################
# -- tests other standard routes (Chat, Summary, File Status) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_other_routes(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"ok": True}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_chat = await ac.post("/api/chat/query/", json={"query": "test"})
        res_sum = await ac.post("/api/summary/generate/", json={"file_id": "123"})
        res_file = await ac.get("/api/files/123")

    assert res_chat.status_code == 200
    assert res_sum.status_code == 200
    assert res_file.status_code == 200

##########################################################################################
# -- ERROR HANDLING: tests a downstream service returning a 404/500 HTTP error --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_http_status_error(mock_client_class):
    # -- Simulate a downstream service explicitly returning a 404 Not Found --
    req = Request("GET", "http://downstream/api")
    res = Response(404, text="Item not found", request=req)
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.HTTPStatusError("Error", request=req, response=res))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/123")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

##########################################################################################
# -- ERROR HANDLING: tests a network crash (service is offline completely) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_request_error(mock_client_class):
    # -- Simulate the downstream service being completely offline (Connection Refused) --
    req = Request("GET", "http://downstream/api")
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection refused", request=req))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/123")

    # Gateway should catch this and return a 503 Service Unavailable
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]

##########################################################################################
# -- ERROR HANDLING: tests network crash during file upload specifically --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_upload_request_error(mock_client_class):
    req = Request("POST", "http://downstream/api")
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection refused", request=req))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.txt", b"data", "text/plain")}
        response = await ac.post("/api/upload/", files=files)

    assert response.status_code == 503

@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_upload_status_error(mock_client_class):
    req = Request("POST", "http://downstream/api")
    res = Response(400, text="Bad Request", request=req)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError("Error", request=req, response=res))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.txt", b"data", "text/plain")}
        response = await ac.post("/api/upload/", files=files)

    assert response.status_code == 400

##########################################################################################
# -- Additional coverage for all gateway routes and error cases --
##########################################################################################
@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_get_file(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"id": "file-123"}, request=Request("GET", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/file-123")

    assert response.status_code == 200
    assert response.json()["id"] == "file-123"

@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_chat_query(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"answer": "hello"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/chat/query/", json={"query": "test"})

    assert response.status_code == 200
    assert response.json()["answer"] == "hello"

@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_summary_generate(mock_client_class):
    mock_client = AsyncMock()
    mock_response = Response(200, json={"summary": "test summary"}, request=Request("POST", "url"))
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/summary/generate/", json={"file_id": "123"})

    assert response.status_code == 200
    assert response.json()["summary"] == "test summary"

@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_http_status_error_on_get_file(mock_client_class):
    req = Request("GET", "http://downstream/api")
    res = Response(404, text="Not found", request=req)
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.HTTPStatusError("Error", request=req, response=res))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/files/file-123")

    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
@patch("app.services.proxy.httpx.AsyncClient")
async def test_gateway_request_error_on_summary(mock_client_class):
    req = Request("POST", "http://downstream/api")
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection error", request=req))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/summary/generate/", json={"file_id": "123"})

    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]