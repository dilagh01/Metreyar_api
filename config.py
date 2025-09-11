from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Metreyar API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./metreyar.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-for-development-12345")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # برای توسعه، در production محدود کنید

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
