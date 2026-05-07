import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.media_models import FileMetadata, TextChunk
from conftest import TestingSessionLocal
from app.services.playback_manager import get_segments_for_chunks

##########################################################################################
# -- tests the health check --
##########################################################################################
@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "media-service"

##########################################################################################
# -- tests successful retrieval of playback segments --
##########################################################################################
@pytest.mark.asyncio
async def test_get_playback_info_success():
    file_id = uuid.uuid4()
    chunk_id_1 = uuid.uuid4()
    chunk_id_2 = uuid.uuid4()
    
    async with TestingSessionLocal() as session:
        # -- 1. Seed file metadata --
        session.add(FileMetadata(id=file_id, file_path="/uploads/video.mp4"))
        
        # -- 2. Seed chunks with timestamps --
        session.add(TextChunk(id=chunk_id_1, file_id=file_id, text="Intro", start_time=0.0, end_time=10.5))
        session.add(TextChunk(id=chunk_id_2, file_id=file_id, text="Topic A", start_time=10.5, end_time=25.0))
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # -- 3. Request segments for specific chunks --
        url = f"/api/v1/media/playback/{file_id}"
        params = {"chunk_ids": [str(chunk_id_1), str(chunk_id_2)]}
        response = await ac.get(url, params=params)

    assert response.status_code == 200
    data = response.json()
    assert data["file_path"] == "/uploads/video.mp4"
    assert len(data["segments"]) == 2
    assert data["segments"][0]["start"] == 0.0
    assert data["segments"][1]["end"] == 25.0

##########################################################################################
# -- tests 404 behavior for missing file metadata --
##########################################################################################
@pytest.mark.asyncio
async def test_get_playback_info_not_found():
    fake_file_id = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        url = f"/api/v1/media/playback/{fake_file_id}"
        response = await ac.get(url, params={"chunk_ids": [str(uuid.uuid4())]})

    assert response.status_code == 404
    assert "File metadata not found" in response.json()["detail"]

##########################################################################################
# -- database session coverage --
##########################################################################################
@pytest.mark.asyncio
async def test_get_db_coverage():
    from app.core.database import get_db
    async for session in get_db():
        assert session is not None
        break

##########################################################################################
# -- direct manager coverage --
##########################################################################################
@pytest.mark.asyncio
async def test_get_segments_for_chunks_direct_success():
    file_id = uuid.uuid4()
    chunk_id_1 = uuid.uuid4()
    chunk_id_2 = uuid.uuid4()

    async with TestingSessionLocal() as session:
        session.add(FileMetadata(id=file_id, file_path="/uploads/direct.mp4"))
        session.add(TextChunk(id=chunk_id_1, file_id=file_id, text="A", start_time=5.0, end_time=9.0))
        session.add(TextChunk(id=chunk_id_2, file_id=file_id, text="B", start_time=1.0, end_time=4.0))
        await session.commit()

        file_path, segments = await get_segments_for_chunks(session, file_id, [chunk_id_1, chunk_id_2])

    assert file_path == "/uploads/direct.mp4"
    assert len(segments) == 2
    assert segments[0].start == 1.0
    assert segments[1].end == 9.0


@pytest.mark.asyncio
async def test_get_segments_for_chunks_direct_not_found():
    async with TestingSessionLocal() as session:
        file_path, segments = await get_segments_for_chunks(session, uuid.uuid4(), [uuid.uuid4()])

    assert file_path is None
    assert segments == []