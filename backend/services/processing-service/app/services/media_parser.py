import os
import shutil
import whisper
import warnings

# -- suppress FP16 warnings on CPUs --
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def _ensure_ffmpeg_available() -> str:
    """
    Ensure ffmpeg is available for Whisper transcribe().
    Whisper spawns the `ffmpeg` binary; on Windows this commonly fails with WinError 2.
    """
    ffmpeg_binary = shutil.which("ffmpeg")
    if ffmpeg_binary:
        return ffmpeg_binary

    # Fallback: use bundled binary from imageio-ffmpeg if installed.
    try:
        import imageio_ffmpeg  # type: ignore
        ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_binary)
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        return ffmpeg_binary
    except Exception as e:
        raise RuntimeError(
            "FFmpeg binary not found. Install ffmpeg or add it to PATH."
        ) from e

# -- verify ffmpeg once at import time --
_ensure_ffmpeg_available()

# -- load model globally to avoid reloading on every request --
print("Loading Whisper 'small' model. This might take a moment on the first run...")
model = whisper.load_model("small")


#####################################################################################
# -- transcribes audio/video and returns chunked segments with timestamps --
#####################################################################################
def process_media(file_path: str) -> list[dict]:
    
    result = model.transcribe(file_path)

    chunks = []
    # -- Whisper naturally chunks output into segments with timestamps -- 
    for segment in result["segments"]:
        chunks.append({
            "text": segment["text"].strip(),
            "start_time": segment["start"],
            "end_time": segment["end"]
        })
    return chunks