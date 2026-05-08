from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.pdf_parser import process_pdf

with patch("whisper.load_model", return_value=Mock(transcribe=Mock())):
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
@patch("app.services.media_parser.os.path.exists", return_value=True)
@patch("app.services.media_parser.model")
async def test_process_media(mock_model, mock_exists):
    """Test media processing with mocked model"""
    mock_model.transcribe.return_value = {
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
    mock_model.transcribe.assert_called_once_with("/fake/audio.mp3")


@pytest.mark.asyncio
async def test_process_media_no_model():
    """Test media processing when model is not available"""
    import app.services.media_parser as mp_module
    original_model = mp_module.model
    mp_module.model = None
    
    try:
        result = mp_module.process_media("/fake/audio.mp3")
        assert result == []
    finally:
        mp_module.model = original_model


@pytest.mark.asyncio
async def test_process_media_file_not_found():
    """Test media processing when file doesn't exist"""
    result = media_parser.process_media("/nonexistent/audio.mp3")
    assert result == []
