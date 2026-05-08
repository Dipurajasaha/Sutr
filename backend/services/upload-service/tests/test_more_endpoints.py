import uuid
import os
import tempfile
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.endpoints import (
    delete_file,
    rename_file,
    list_all_files,
    get_file_status,
)
from app.services.upload_manager import delete_file_from_disk


@pytest.mark.asyncio
async def test_delete_file_not_found():
    db = AsyncMock()
    result = SimpleNamespace(scalar_one_or_none=lambda: None)
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await delete_file(uuid.uuid4(), db=db)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_file_success():
    file_obj = SimpleNamespace(id=uuid.uuid4(), filename="f.txt", file_path="/tmp/f.txt")
    result = SimpleNamespace(scalar_one_or_none=lambda: file_obj)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    async def fake_delete_file(path):
        return None

    with patch("app.api.endpoints.delete_file_from_disk", new=fake_delete_file):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.delete.return_value.status_code = 200

            resp = await delete_file(file_obj.id, db=db)

    assert "deleted successfully" in resp["detail"]
    db.delete.assert_awaited()
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_rename_file_empty_filename():
    file_obj = SimpleNamespace(id=uuid.uuid4(), filename="old", file_path="/tmp/old.txt")
    result = SimpleNamespace(scalar_one_or_none=lambda: file_obj)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    class Req:
        filename = "   "
        summary_quick = None
        summary_detailed = None

    with pytest.raises(HTTPException) as exc:
        await rename_file(file_obj.id, Req(), db=db)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_rename_file_success():
    file_obj = SimpleNamespace(id=uuid.uuid4(), filename="old", file_path="/tmp/old.txt", summary_quick=None, summary_detailed=None)
    result = SimpleNamespace(scalar_one_or_none=lambda: file_obj)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.add = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    class Req:
        filename = "newname.pdf"
        summary_quick = "sq"
        summary_detailed = "sd"

    resp = await rename_file(file_obj.id, Req(), db=db)
    assert resp.filename == "newname.pdf"


@pytest.mark.asyncio
async def test_list_all_files_direct():
    rows = [
        SimpleNamespace(id=uuid.uuid4(), filename="a", file_type="document", file_path="/tmp/a.pdf", status="uploaded", created_at=None, summary_quick=None, summary_detailed=None),
    ]
    db_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))
    db = AsyncMock()
    db.execute = AsyncMock(return_value=db_result)

    result = await list_all_files(db=db)
    assert result == rows


def test_delete_file_from_disk_missing_raises():
    with pytest.raises(FileNotFoundError):
        # path that does not exist
        import asyncio
        asyncio.get_event_loop().run_until_complete(delete_file_from_disk("/tmp/no-such-file-xyz"))


def test_delete_file_from_disk_success(tmp_path):
    p = tmp_path / "f.tmp"
    p.write_text("data")
    import asyncio
    asyncio.get_event_loop().run_until_complete(delete_file_from_disk(str(p)))
    assert not p.exists()
