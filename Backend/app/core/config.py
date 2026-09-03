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

    # 图片服务（OpenAI 兼容参数，任意同类服务均可）与对话服务
    IMAGE_API_KEY: str = ""
    IMAGE_BASE_URL: str = ""
    DEEPSEEK_API_KEY: str = ""

    # JWT 签名密钥；生产环境务必通过环境变量覆盖
    JWT_SECRET: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()