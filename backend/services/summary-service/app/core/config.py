import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Summary Service"
    # -- longcat API configuration --
    LONGCAT_API_KEY: str = os.getenv("LONGCAT_API_KEY", "your_longcat_api_key_here")
    LONGCAT_BASE_URL: str = "https://api.longcat.chat/openai/v1"
    LONGCAT_MODEL: str = "LongCat-Flash-Chat"
    
    # -- database configuration --
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")

    class Config:
        env_file = ".env"

settings = Settings()