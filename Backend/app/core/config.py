from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "LeafAI"
    PROJECT_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leafai"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/leafai"

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: list[str] = ["*"]

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    TASK_RESULT_TTL: int = 3600

    FILE_STORAGE_PATH: str = "./storage"

    DUOMI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()