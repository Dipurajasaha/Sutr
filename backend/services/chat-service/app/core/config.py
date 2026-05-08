from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
import os

# -- Explicitly load .env file from project root --
config_path = Path(__file__).resolve()  # app/core/config.py
project_root = config_path.parents[5]  # Go up to project root (D:\Projects\Sutr\Sutr)
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file, override=True)

# -- Configuration for the Chat Service --
class Settings(BaseSettings):
    PROJECT_NAME: str = "Chat Service"
    LONGCAT_API_KEY: str = os.getenv("LONGCAT_API_KEY", "your_longcat_api_key_here")
    LONGCAT_BASE_URL: str = "https://api.longcat.chat/openai/v1"
    LONGCAT_MODEL: str = "LongCat-Flash-Chat"
    
    VECTOR_SERVICE_URL: str = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8003")

    class Config:
        extra = "ignore"

# -- instantiate the settings --
settings = Settings()