import os
import shutil
import whisper
import warnings
import logging

# -- suppress FP16 warnings on CPUs --
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
logger = logging.getLogger(__name__)

def _ensure_ffmpeg_available() -> str:
    # -- check if ffmpeg is available on system PATH --
    ffmpeg_binary = shutil.which("ffmpeg")
    if ffmpeg_binary:
        return ffmpeg_binary

    # -- fallback to bundled imageio-ffmpeg if installed --
    try:
        import imageio_ffmpeg
        ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_binary)
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        return ffmpeg_binary
    except Exception as e:
        raise RuntimeError(
            "FFmpeg binary not found. Install ffmpeg or add it to PATH."
        ) from e

# -- verify ffmpeg availability at module load time --
_ensure_ffmpeg_available()

# -- load Whisper model once at startup --
print("Loading Whisper 'small' model. This might take a moment on the first run...")
model = whisper.load_model("small")


##########################################################################
# Transcribe Audio/Video
##########################################################################
def process_media(file_path: str) -> list[dict]:
    logger.info("Starting audio/video extraction and transcription for file_path=%s", file_path)
    result = model.transcribe(file_path)
    logger.info("Whisper finished transcribing file_path=%s", file_path)

    chunks = []
    # -- Whisper provides segments with native timestamps --
    for segment in result["segments"]:
        chunks.append({
            "text": segment["text"].strip(),
            "start_time": segment["start"],
            "end_time": segment["end"]
        })
    return chunks