from unittest.mock import patch, Mock
import pytest


def test_media_parser_ensure_ffmpeg_available_finds_system():
    """Test that _ensure_ffmpeg_available succeeds when ffmpeg is in PATH"""
    from app.services.media_parser import _ensure_ffmpeg_available
    # Patch shutil.which to return a fake path
    with patch('app.services.media_parser.shutil.which', return_value='/usr/bin/ffmpeg'):
        result = _ensure_ffmpeg_available()
        assert result == '/usr/bin/ffmpeg'


def test_media_parser_ensure_ffmpeg_fallback_imageio():
    """Test that _ensure_ffmpeg_available falls back to imageio_ffmpeg"""
    from app.services.media_parser import _ensure_ffmpeg_available
    
    fake_imageio = Mock()
    fake_imageio.get_ffmpeg_exe.return_value = '/tmp/imageio_ffmpeg'
    
    with patch('app.services.media_parser.shutil.which', return_value=None):
        with patch.dict('sys.modules', {'imageio_ffmpeg': fake_imageio}):
            with patch('app.services.media_parser.os.path.dirname', return_value='/tmp'):
                result = _ensure_ffmpeg_available()
                assert result == '/tmp/imageio_ffmpeg'


def test_media_parser_ensure_ffmpeg_no_fallback_raises():
    """Test that _ensure_ffmpeg_available raises when ffmpeg missing"""
    from app.services.media_parser import _ensure_ffmpeg_available
    
    with patch('app.services.media_parser.shutil.which', return_value=None):
        with patch('app.services.media_parser.os.environ', {}):
            with patch('builtins.__import__', side_effect=ImportError('no imageio')):
                with pytest.raises(RuntimeError, match="FFmpeg binary not found"):
                    _ensure_ffmpeg_available()
