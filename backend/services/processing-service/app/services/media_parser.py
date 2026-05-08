import os
import shutil
import whisper
import warnings
import logging

# -- suppress FP16 warnings on CPUs --
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
logger = logging.getLogger(__name__)

# -- GPU memory cleanup helper --
def _clear_gpu_memory():
    try:
        import torch
        torch.cuda.empty_cache()
        logger.info("GPU memory cleared")
    except Exception as e:
        logger.debug("Could not clear GPU memory: %s", str(e))

def _ensure_ffmpeg_available() -> str:
    # -- check if ffmpeg is available on system PATH --
    ffmpeg_binary = shutil.which("ffmpeg")
    if ffmpeg_binary:
        logger.info("FFmpeg found at: %s", ffmpeg_binary)
        return ffmpeg_binary

    # -- fallback to bundled imageio-ffmpeg if installed --
    try:
        import imageio_ffmpeg
        ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_binary)
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        logger.info("FFmpeg bundled via imageio-ffmpeg: %s", ffmpeg_binary)
        return ffmpeg_binary
    except Exception as e:
        logger.error("FFmpeg binary not found: %s", str(e))
        raise RuntimeError(
            "FFmpeg binary not found. Install ffmpeg or add it to PATH."
        ) from e

# -- verify ffmpeg availability at module load time --
try:
    _ensure_ffmpeg_available()
    logger.info("FFmpeg availability check passed")
except RuntimeError as e:
    logger.warning("FFmpeg availability check failed: %s (will fail at runtime if processing media files)", str(e))

# -- load Whisper model once at startup --
try:
    print("Loading Whisper 'small' model. This might take a moment on the first run...")
    logger.info("Loading Whisper 'small' model...")
    model = whisper.load_model("small", device="cuda")
    logger.info("Whisper model loaded on CUDA GPU")
except Exception as e:
    logger.error("Failed to load Whisper model on CUDA: %s - falling back to CPU", str(e))
    try:
        model = whisper.load_model("small", device="cpu")
        logger.info("Whisper model loaded on CPU (fallback)")
    except Exception as e2:
        logger.error("Failed to load Whisper model on CPU: %s", str(e2))
        model = None


##########################################################################
# Transcribe Audio/Video
##########################################################################
def process_media(file_path: str) -> list[dict]:
    logger.info("Starting audio/video extraction and transcription for file_path=%s", file_path)
    
    # -- check if model was loaded --
    if model is None:
        logger.error("Whisper model not available - failed to load at startup")
        return []
    
    # -- verify file exists --
    if not os.path.exists(file_path):
        logger.error("Media file not found: %s", file_path)
        return []
    
    try:
        logger.debug("Attempting to transcribe file with Whisper: %s", file_path)
        result = model.transcribe(file_path)
        logger.info("Whisper finished transcribing file_path=%s with %d segments", file_path, len(result.get("segments", [])))
        
        chunks = []
        # -- Whisper provides segments with native timestamps --
        for segment in result.get("segments", []):
            text = segment.get("text", "").strip()
            if text:  # Only add non-empty segments
                chunks.append({
                    "text": text,
                    "start_time": segment.get("start", 0.0),
                    "end_time": segment.get("end", 0.0)
                })
        
        logger.info("Extracted %d text chunks from transcription", len(chunks))
        _clear_gpu_memory()
        return chunks
        
    except FileNotFoundError as e:
        logger.error("Media file not found during transcription: %s - %s", file_path, str(e))
        return []
    except RuntimeError as e:
        logger.error("Whisper runtime error (often FFmpeg-related): %s", str(e))
        return []
    except Exception as e:
        logger.exception("Unexpected error during media transcription for file_path=%s: %s", file_path, str(e))
        return []
    return chunks