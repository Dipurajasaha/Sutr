import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.endpoints import delete_file_vectors


@pytest.mark.asyncio
async def test_delete_file_vectors_no_records():
    db_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))
    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)

    resp = await delete_file_vectors(str(uuid.uuid4()), db=db)
    assert resp["deleted_count"] == 0
    assert "No vector records" in resp["message"]


@pytest.mark.asyncio
async def test_delete_file_vectors_with_records():
    file_id = uuid.uuid4()
    rows = [
        SimpleNamespace(faiss_id=1),
        SimpleNamespace(faiss_id=2),
    ]
    db_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))

    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    resp = await delete_file_vectors(str(file_id), db=db)
    assert resp["deleted_count"] == 2
    db.delete.assert_awaited()
    db.commit.assert_awaited()
