import os
from pydantic_settings import BaseSettings, SettingsConfigDict

##########################################################################
# -- application configuration using Pydantic BaseSettings --
##########################################################################
class Settings(BaseSettings):
    # -- configuration settings for the upload service --
    PROJECT_NAME: str = "Upload Service"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")

    # -- directory where files will be stored locally --
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # -- Pydantic V2 standard for config --
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()