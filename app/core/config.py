from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    PROJECT_NAME: str = "Financial Dashboard API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-only-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Using sqlite for easy local starting, but code uses postgres compatible approaches
    DATABASE_URL: str = "sqlite:///./finance.db"

settings = Settings()

