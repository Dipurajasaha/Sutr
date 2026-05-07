import os 
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# -- Explicitly load .env file from project root --
config_path = Path(__file__).resolve()  # app/core/config.py
project_root = config_path.parents[5]  # Go up to project root (D:\Projects\Sutr\Sutr)
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)

#####################################################################################
# -- configuration using Pydantic for Processing Service --
#####################################################################################
class Settings(BaseSettings):
    PROJECT_NAME: str = "Processing Service"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "../upload-service/uploads") # Shared volume for local dev

    class Config:
        env_file = ".env"


# -- create a global settings instance that can be imported across the app --
settings = Settings()