import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sutr API Gateway"
    
    # -- internal service registry (use localhost for local dev, or container names in Docker) --
    UPLOAD_SERVICE_URL: str = os.getenv("UPLOAD_SERVICE_URL", "http://localhost:8001")
    PROCESS_SERVICE_URL: str = os.getenv("PROCESS_SERVICE_URL", "http://localhost:8002")
    VECTOR_SERVICE_URL: str = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8003")
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://localhost:8004")
    SUMMARY_SERVICE_URL: str = os.getenv("SUMMARY_SERVICE_URL", "http://localhost:8005")
    MEDIA_SERVICE_URL: str = os.getenv("MEDIA_SERVICE_URL", "http://localhost:8006")

    class Config:
        env_file = ".env"

# -- instantiate settings --
settings = Settings()