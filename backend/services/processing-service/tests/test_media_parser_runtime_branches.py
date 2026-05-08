from unittest.mock import patch, Mock
import pytest

from app.services import media_parser


def test_clear_gpu_memory_handles_exceptions(monkeypatch):
    # Simulate torch missing or torch.cuda.empty_cache raising
    class FakeTorch:
        class cuda:
            @staticmethod
            def empty_cache():
                raise RuntimeError("cuda error")

    monkeypatch.setitem(__import__('sys').modules, 'torch', FakeTorch())
    # Call helper directly; should not raise
    media_parser._clear_gpu_memory()


def test_process_media_transcribe_exceptions(monkeypatch, tmp_path):
    # Create a fake audio file
    fp = tmp_path / "audio.mp3"
    fp.write_text("dummy")

    # Case 1: model.transcribe raises RuntimeError -> should return []
    fake_model = Mock()
    fake_model.transcribe.side_effect = RuntimeError("ffmpeg fail")

    monkeypatch.setattr(media_parser, 'model', fake_model)
    res = media_parser.process_media(str(fp))
    assert res == []

    # Case 2: model.transcribe raises generic Exception -> should return []
    fake_model.transcribe.side_effect = Exception("unknown")
    monkeypatch.setattr(media_parser, 'model', fake_model)
    res = media_parser.process_media(str(fp))
    assert res == []


def test_process_media_transcribe_file_not_found(monkeypatch, tmp_path):
    fp = tmp_path / "audio.mp3"
    fp.write_text("dummy")

    fake_model = Mock()
    fake_model.transcribe.side_effect = FileNotFoundError("missing during transcribe")

    monkeypatch.setattr(media_parser, 'model', fake_model)
    res = media_parser.process_media(str(fp))
    assert res == []
