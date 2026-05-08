import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, Mock
from types import SimpleNamespace

from app.main import app
from app.api.endpoints import index_chunks, search_vectors
from app.api.endpoints import get_file_chunks
from app.schemas.vector import IndexRequest, SearchRequest, ChunkInput

##########################################################################################
# -- tests the application startup event for database initialization coverage --
##########################################################################################
@pytest.mark.asyncio
@patch("sqlalchemy.ext.asyncio.AsyncEngine.begin")
async def test_startup_event(mock_begin):
    from app.main import startup_event

    mock_conn = AsyncMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_conn
    mock_context_manager.__aexit__.return_value = None
    mock_begin.return_value = mock_context_manager

    await startup_event()

    mock_conn.run_sync.assert_awaited_once()

##########################################################################################
# -- tests indexing chunks --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_index_chunks_success(mock_vector_store):
    # Mock FAISS returning IDs 1 and 2
    mock_vector_store.generate_embeddings.return_value = []
    mock_vector_store.add_to_index.return_value = [1, 2]

    payload = {
        "chunks": [
            {"chunk_id": str(uuid.uuid4()), "file_id": str(uuid.uuid4()), "text": "test 1"},
            {"chunk_id": str(uuid.uuid4()), "file_id": str(uuid.uuid4()), "text": "test 2"}
        ]
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/vectors/index/", json=payload)
        
    assert response.status_code == 201
    assert response.json()["indexed_count"] == 2

##########################################################################################
# -- tests empty chunk rejection --
##########################################################################################
@pytest.mark.asyncio
async def test_index_chunks_empty():
    payload = {"chunks": []}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/vectors/index/", json=payload)
        
    assert response.status_code == 400

##########################################################################################
# -- tests semantic search --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_success(mock_vector_store):
    file_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())
    
    # 1. Inject data into DB using index endpoint
    mock_vector_store.generate_embeddings.return_value = []
    mock_vector_store.add_to_index.return_value = [99] # FAISS ID 99
    
    index_payload = {"chunks": [{"chunk_id": chunk_id, "file_id": file_id, "text": "searchable text"}]}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/vectors/index/", json=index_payload)
        
        # 2. Search for it (Mock FAISS finding ID 99)
        mock_vector_store.search_index.return_value = ([0.1], [99])
        search_payload = {"query": "search query", "file_id": file_id, "top_k": 5}
        
        response = await ac.post("/api/v1/vectors/search/", json=search_payload)
        
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["chunk_id"] == chunk_id

##########################################################################################
# -- tests semantic search filtering out non-matching file_id --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_file_id_mismatch_returns_empty(mock_vector_store):
    file_id = str(uuid.uuid4())
    other_file_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_vector_store.search_index.return_value = ([0.1], [99])
    mock_vector_store.add_to_index.return_value = [99]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/vectors/index/",
            json={"chunks": [{"chunk_id": chunk_id, "file_id": other_file_id, "text": "searchable text"}]},
        )

        response = await ac.post(
            "/api/v1/vectors/search/",
            json={"query": "search query", "file_id": file_id, "top_k": 5},
        )

    assert response.status_code == 200
    assert response.json() == []

##########################################################################################
# -- tests semantic search returning a match when file_id matches --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_file_id_match_returns_result(mock_vector_store):
    file_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    mock_vector_store.search_index.return_value = ([0.1], [99])
    mock_vector_store.add_to_index.return_value = [99]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/vectors/index/",
            json={"chunks": [{"chunk_id": chunk_id, "file_id": file_id, "text": "searchable text"}]},
        )

        response = await ac.post(
            "/api/v1/vectors/search/",
            json={"query": "search query", "file_id": file_id, "top_k": 5},
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["chunk_id"] == chunk_id

##########################################################################################
# -- direct endpoint tests to hit the exact index and search branches --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_index_chunks_direct_success(mock_vector_store):
    chunk_id = uuid.uuid4()
    file_id = uuid.uuid4()

    mock_vector_store.generate_embeddings.return_value = []
    mock_vector_store.add_to_index.return_value = [7]

    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()

    request = IndexRequest(
        chunks=[ChunkInput(chunk_id=chunk_id, file_id=file_id, text="direct chunk")]
    )

    result = await index_chunks(request, db=db)

    assert result == {"status": "success", "indexed_count": 1}
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_direct_file_id_mismatch_returns_empty(mock_vector_store):
    request_file_id = uuid.uuid4()
    chunk_file_id = uuid.uuid4()

    mock_vector_store.search_index.return_value = ([0.1], [99])

    metadata = SimpleNamespace(
        chunk_id=uuid.uuid4(),
        file_id=chunk_file_id,
        text="searchable text",
    )
    db_result = SimpleNamespace(scalar_one_or_none=lambda: metadata)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)

    request = SearchRequest(query="search query", file_id=request_file_id, top_k=5)
    result = await search_vectors(request, db=db)

    assert result == []
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_direct_file_id_match_returns_result(mock_vector_store):
    file_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    mock_vector_store.search_index.return_value = ([0.1], [99])

    metadata = SimpleNamespace(
        chunk_id=chunk_id,
        file_id=file_id,
        text="searchable text",
    )
    db_result = SimpleNamespace(scalar_one_or_none=lambda: metadata)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)

    request = SearchRequest(query="search query", file_id=file_id, top_k=5)
    result = await search_vectors(request, db=db)

    assert len(result) == 1
    assert result[0].chunk_id == chunk_id
    assert result[0].file_id == file_id
    db.execute.assert_awaited_once()

##########################################################################################
# -- tests FAISS returning no valid vectors (-1) --
##########################################################################################
@pytest.mark.asyncio
@patch("app.api.endpoints.vector_store")
async def test_search_vectors_faiss_minus_one(mock_vector_store):
    # -1 is FAISS's way of saying "I don't have enough data"
    mock_vector_store.search_index.return_value = ([0.0], [-1])
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/vectors/search/", json={"query": "query"})
        
    assert response.status_code == 200
    assert len(response.json()) == 0

##########################################################################################
# -- tests file-scoped chunk fallback endpoint --
##########################################################################################
@pytest.mark.asyncio
async def test_get_file_chunks_direct_returns_ordered_chunks():
    file_id = uuid.uuid4()

    rows = [
        SimpleNamespace(
            chunk_id=uuid.uuid4(),
            file_id=file_id,
            text="first chunk",
            start_time=0.0,
            end_time=1.0,
            faiss_id=1,
        ),
        SimpleNamespace(
            chunk_id=uuid.uuid4(),
            file_id=file_id,
            text="second chunk",
            start_time=1.0,
            end_time=2.0,
            faiss_id=2,
        ),
    ]

    db_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))
    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)

    result = await get_file_chunks(str(file_id), limit=2, db=db)

    assert len(result) == 2
    assert result[0].text == "first chunk"
    assert result[1].text == "second chunk"

##########################################################################################
# -- db coverage --
##########################################################################################
@pytest.mark.asyncio
async def test_get_db_coverage():
    from app.core.database import get_db
    async for session in get_db():
        assert session is not None
        break