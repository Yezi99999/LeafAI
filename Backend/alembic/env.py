import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from app.core.config import get_settings
from app.db.session import Base

# 优先从环境变量读取数据库连接串，避免在版本库中泄露凭据
settings = get_settings()
DATABASE_SYNC_URL = os.environ.get("DATABASE_SYNC_URL") or settings.DATABASE_SYNC_URL
from app.db.models import (
    User, AIProvider, AIModel, AIChatSession, AIChatMessage, AITask
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url():
    # 环境变量 / .env 优先，其次使用 alembic.ini 中的占位值
    url = DATABASE_SYNC_URL
    if url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg", "postgresql", 1)
    elif "://" not in url:
        url = config.get_main_option("sqlalchemy.url")
    return url


def run_migrations_offline():
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()