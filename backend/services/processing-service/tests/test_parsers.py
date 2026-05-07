from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.pdf_parser import process_pdf

with patch("whisper.load_model", return_value=Mock()):
    from app.services import media_parser


@pytest.mark.asyncio
@patch("app.services.pdf_parser.fitz.open")
async def test_process_pdf(mock_fitz_open):
    page_one = Mock()
    page_one.get_text.return_value = "First page text"
    page_two = Mock()
    page_two.get_text.return_value = "Second page text"

    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [page_one, page_two]
    mock_fitz_open.return_value.__enter__.return_value = mock_doc

    result = process_pdf("/fake/document.pdf")

    assert len(result) == 1
    assert result[0]["text"] == "First page text\nSecond page text"
    assert result[0]["start_time"] is None
    assert result[0]["end_time"] is None
    mock_fitz_open.assert_called_once_with("/fake/document.pdf")


@pytest.mark.asyncio
@patch("app.services.media_parser.model.transcribe")
async def test_process_media(mock_transcribe):
    mock_transcribe.return_value = {
        "segments": [
            {"text": " Hello world ", "start": 0.0, "end": 2.5},
            {"text": " Another segment ", "start": 2.5, "end": 5.0},
        ]
    }

    result = media_parser.process_media("/fake/audio.mp3")

    assert result == [
        {"text": "Hello world", "start_time": 0.0, "end_time": 2.5},
        {"text": "Another segment", "start_time": 2.5, "end_time": 5.0},
    ]
    mock_transcribe.assert_called_once_with("/fake/audio.mp3")
