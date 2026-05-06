import whisper
import warnings

# -- suppress FP16 warnings on CPUs --
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

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