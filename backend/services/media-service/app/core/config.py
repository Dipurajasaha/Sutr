import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Media Timestamp Service"
    # -- database configuration --
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")

    class Config:
        env_file = ".env"

settings = Settings()