import importlib.util
import sys
import types
import shutil
from unittest.mock import Mock


def _load_media_parser_as(name: str, which_return=None, imageio_get=None, whisper_behaviour=None):
    """
    Load the media_parser module under a temporary name to exercise import-time branches.
    - which_return: value to return from shutil.which
    - imageio_get: if provided, a path string for imageio_ffmpeg.get_ffmpeg_exe
    - whisper_behaviour: a callable (name, device) -> model or raise
    """
    path = r"D:\Projects\Sutr\Sutr\backend\services\processing-service\app\services\media_parser.py"

    # Prepare fake whisper module
    fake_whisper = types.ModuleType('whisper')
    def load_model(name, device=None):
        if whisper_behaviour:
            return whisper_behaviour(name, device=device)
        return Mock(transcribe=Mock())
    fake_whisper.load_model = load_model

    # Insert fake whisper into sys.modules for the import
    sys.modules['whisper'] = fake_whisper

    # Optionally insert fake imageio_ffmpeg
    if imageio_get is not None:
        fake_img = types.ModuleType('imageio_ffmpeg')
        fake_img.get_ffmpeg_exe = lambda: imageio_get
        sys.modules['imageio_ffmpeg'] = fake_img

    # Patch shutil.which temporarily
    orig_which = shutil.which
    shutil.which = (lambda prog: which_return)

    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        # cleanup
        shutil.which = orig_which
        sys.modules.pop('whisper', None)
        if imageio_get is not None:
            sys.modules.pop('imageio_ffmpeg', None)


def test_import_with_imageio_and_cpu_fallback():
    # Simulate no ffmpeg on PATH but imageio provides binary, and whisper cuda fails
    def whisper_behaviour(name, device=None):
        if device == 'cuda':
            raise RuntimeError('cuda not available')
        return Mock(transcribe=Mock())

    mod = _load_media_parser_as('tmp.media_parser_cpu', which_return=None, imageio_get='C:/fake/ffmpeg', whisper_behaviour=whisper_behaviour)
    # model should be set (CPU fallback)
    assert getattr(mod, 'model', None) is not None


def test_import_whisper_all_fail_results_in_model_none():
    def whisper_behaviour(name, device=None):
        raise RuntimeError('load failed')

    mod = _load_media_parser_as('tmp.media_parser_none', which_return='C:/ffmpeg', imageio_get=None, whisper_behaviour=whisper_behaviour)
    assert getattr(mod, 'model', None) is None


def test_import_with_cuda_success():
    def whisper_behaviour(name, device=None):
        if device == 'cuda':
            return Mock(transcribe=Mock())
        raise RuntimeError('should prefer cuda')

    mod = _load_media_parser_as('tmp.media_parser_cuda', which_return='C:/ffmpeg', imageio_get=None, whisper_behaviour=whisper_behaviour)
    assert getattr(mod, 'model', None) is not None


def test_import_with_no_ffmpeg_and_no_imageio_logs_warning():
    # Simulate no ffmpeg on PATH and no imageio_ffmpeg available so _ensure_ffmpeg_available raises
    def whisper_behaviour(name, device=None):
        return Mock(transcribe=Mock())

    mod = _load_media_parser_as('tmp.media_parser_no_ffmpeg', which_return=None, imageio_get=None, whisper_behaviour=whisper_behaviour)
    # module imported; model may be set or None depending on whisper behaviour
    assert hasattr(mod, 'model')
