import os
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# -- Explicitly load .env file from project root --
config_path = Path(__file__).resolve()  # app/core/config.py
project_root = config_path.parents[5]  # Go up to project root (D:\Projects\Sutr\Sutr)
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sutr API Gateway"
    
    # -- internal service registry (use localhost for local dev, or container names in Docker) --
    UPLOAD_SERVICE_URL: str = os.getenv("UPLOAD_SERVICE_URL", "http://localhost:8001")
    PROCESS_SERVICE_URL: str = os.getenv("PROCESS_SERVICE_URL", "http://localhost:8003")
    VECTOR_SERVICE_URL: str = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8005")
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://localhost:8004")
    SUMMARY_SERVICE_URL: str = os.getenv("SUMMARY_SERVICE_URL", "http://localhost:8006")
    MEDIA_SERVICE_URL: str = os.getenv("MEDIA_SERVICE_URL", "http://localhost:8007")

    class Config:
        env_file = ".env"

# -- instantiate settings --
settings = Settings()