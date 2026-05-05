from pydantic_settings import BaseSettings

class BaseConfig(BaseSettings):
    PROJECT_NAME: str = "Sutr Microservice"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str | None = None 

    class Cofig:
        env_file = ".env"
        case_sensitive = True