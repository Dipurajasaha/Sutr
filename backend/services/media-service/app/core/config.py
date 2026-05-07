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

class Settings(BaseSettings):
    PROJECT_NAME: str = "Media Timestamp Service"
    # -- database configuration --
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")

    class Config:
        env_file = ".env"

settings = Settings()