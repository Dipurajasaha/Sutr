import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chat Service"
    LONGCAT_API_KEY: str = os.getenv("LONGCAT_API_KEY", "your_longcat_api_key_here")
    LONGCAT_BASE_URL: str = "https://api.longcat.chat/openai/v1"
    LONGCAT_MODEL: str = "LongCat-Flash-Chat"
    
    VECTOR_SERVICE_URL: str = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8003")

    class Config:
        env_file = ".env"

settings = Settings()