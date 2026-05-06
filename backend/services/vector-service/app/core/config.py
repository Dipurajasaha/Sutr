import os
from pydantic_settings import BaseSettings

##############################################################################
# -- configuration settings for the Vector Service --
##############################################################################
class Settings(BaseSettings):
    PROJECT_NAME: str = "Vector Service"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://sutr_admin:sutr_password@localhost:5432/sutr_db")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./faiss_store/index.bin")

    class Config:
        env_file = ".env"

settings = Settings()