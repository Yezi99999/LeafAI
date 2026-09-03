"""
LeafAI 数据库初始化 + 管理员设置脚本

用法（在 Backend 目录下执行）：
    python init_db.py
    python init_db.py --admin-username admin --admin-password 'your-secret'
    python init_db.py --admin-username admin --admin-password 'new-secret' --reset-admin

说明：
    - 一次性完成：创建数据库 + 创建所有表 + 种子数据（服务商/模型/功能开关）。
    - 管理员用户名/密码优先取命令行参数，其次取环境变量 ADMIN_USERNAME / ADMIN_PASSWORD，
      最后兜底为 admin / admin123。
    - 管理员已存在时默认【不覆盖密码】；如需重置密码请加 --reset-admin。
"""
import asyncio
import argparse
import os
import sys
from urllib.parse import urlparse
import asyncpg
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()

parser = argparse.ArgumentParser(description="LeafAI 数据库初始化与管理员设置")
parser.add_argument(
    "--admin-username", default=None,
    help="管理员用户名（默认取环境变量 ADMIN_USERNAME，兜底为 admin）",
)
parser.add_argument(
    "--admin-password", default=None,
    help="管理员密码（默认取环境变量 ADMIN_PASSWORD，兜底为 admin123）",
)
parser.add_argument(
    "--reset-admin", action="store_true",
    help="当管理员已存在时强制重置其密码；不带此参数则保留原密码",
)
_cli_args = parser.parse_args()

ADMIN_USERNAME = _cli_args.admin_username or os.environ.get("ADMIN_USERNAME") or "admin"
ADMIN_PASSWORD = _cli_args.admin_password or os.environ.get("ADMIN_PASSWORD") or "admin123"
RESET_ADMIN = _cli_args.reset_admin or bool(os.environ.get("ADMIN_RESET_PASSWORD"))
_IS_AUTO = (
    _cli_args.admin_password is not None
    or os.environ.get("ADMIN_PASSWORD") is not None
)


# 数据库连接信息从环境变量 / .env 解析，避免在版本库中写入密码
def _parse_db_url():
    parts = urlparse(settings.DATABASE_SYNC_URL)
    path = parts.path.lstrip("/")
    return {
        "user": parts.username or "postgres",
        "password": parts.password or "",
        "host": parts.hostname or "localhost",
        "port": parts.port or 5432,
        "name": path,
    }


_db = _parse_db_url()
DB_USER = _db["user"]
DB_PASSWORD = _db["password"]
DB_HOST = _db["host"]
DB_PORT = _db["port"]
DB_NAME = _db["name"]


async def create_database():
    conn = await asyncpg.connect(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT,
        database="postgres",
    )
    try:
        await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"[OK] 数据库 '{DB_NAME}' 创建成功")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f"[OK] 数据库 '{DB_NAME}' 已存在")
    finally:
        await conn.close()


async def create_tables_and_seed():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.session import Base
    from app.db.models import (
        User, AIProvider, AIModel, AIChatSession, AIChatMessage, AITask,
        ProviderCategory,
    )

    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] 所有表创建成功")

    # 确保 user 表有 user_id 列（兼容旧表迁移）
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS user_id VARCHAR(32)'))
        await conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_user_id ON "user" (user_id)'))
    print("[OK] user_id 列已就绪")

    # 确保 ai_model 表有 prompt_max_length 列（兼容旧表迁移）
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text('ALTER TABLE ai_model ADD COLUMN IF NOT EXISTS prompt_max_length INTEGER DEFAULT 5000'))
    print("[OK] prompt_max_length 列已就绪")

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as db:
        import uuid
        from app.core.security import hash_password

        # 1. 补全所有已有用户的 user_id
        all_users = await db.execute(
            __import__("sqlalchemy").select(User).where(User.user_id.is_(None))
        )
        missing_users = all_users.scalars().all()
        for u in missing_users:
            u.user_id = uuid.uuid4().hex[:16]
        if missing_users:
            print(f"[OK] 已为 {len(missing_users)} 个用户补充 user_id")

        # 2. 创建或更新管理员（可按参数自定义用户名/密码；已存在时不覆盖密码，除非 --reset-admin）
        admin = await db.execute(
            __import__("sqlalchemy").select(User).where(User.username == ADMIN_USERNAME)
        )
        admin = admin.scalar_one_or_none()
        if not admin:
            admin = User(
                user_id=uuid.uuid4().hex[:16],
                username=ADMIN_USERNAME,
                email=f"{ADMIN_USERNAME}@leafai.local",
                hashed_password=hash_password(ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            await db.flush()
            print(f"[OK] 管理员 '{ADMIN_USERNAME}' 创建成功 (id={admin.id})")
        else:
            admin.is_superuser = True
            admin.is_active = True
            if not admin.user_id:
                admin.user_id = uuid.uuid4().hex[:16]
            if RESET_ADMIN:
                admin.hashed_password = hash_password(ADMIN_PASSWORD)
                print(f"[OK] 管理员 '{ADMIN_USERNAME}' 已存在，密码已重置 (id={admin.id})")
            else:
                print(
                    f"[OK] 管理员 '{ADMIN_USERNAME}' 已存在 (id={admin.id})"
                    f"{'，保留原密码' if not _IS_AUTO else ''}。"
                    "如需重置密码请加 --reset-admin"
                )
        admin_id = admin.id

        # 2. 创建图片服务服务商（通用 OpenAI 兼容参数，任意同类服务均可；id=1）
        image_provider = await db.execute(
            __import__("sqlalchemy").select(AIProvider).where(AIProvider.name == "Image Provider")
        )
        image_provider = image_provider.scalar_one_or_none()
        image_key = settings.IMAGE_API_KEY
        image_base_url = settings.IMAGE_BASE_URL or "https://duomiapi.com/v1"
        if not image_provider:
            image_provider = AIProvider(
                id=1,
                name="Image Provider",
                category=ProviderCategory.IMAGE,
                api_key=image_key,
                base_url=image_base_url,
                timeout=120,
                extra_config={"async": True, "api_path": "/images/generations"},
                is_enabled=True,
                priority=1,
            )
            db.add(image_provider)
            await db.flush()
            print(f"[OK] 图片服务服务商创建成功 (id={image_provider.id})")
        else:
            if settings.IMAGE_API_KEY:
                image_provider.api_key = settings.IMAGE_API_KEY
            print(f"[OK] 图片服务服务商已存在 (id={image_provider.id})")

        # 2.1 创建 DeepSeek 服务商（对话，id=2），使用 env 配置的 DeepSeek_API_KEY
        deepseek = await db.execute(
            __import__("sqlalchemy").select(AIProvider).where(AIProvider.name == "DeepSeek")
        )
        deepseek = deepseek.scalar_one_or_none()
        if not deepseek:
            deepseek = AIProvider(
                id=2,
                name="DeepSeek",
                category=ProviderCategory.CHAT,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",
                timeout=120,
                extra_config={"api_path": "/chat/completions"},
                is_enabled=True,
                priority=1,
            )
            db.add(deepseek)
            await db.flush()
            print(f"[OK] DeepSeek 服务商创建成功 (id={deepseek.id})")
        else:
            if settings.DEEPSEEK_API_KEY:
                deepseek.api_key = settings.DEEPSEEK_API_KEY
            print(f"[OK] DeepSeek 服务商已存在 (id={deepseek.id})")

        # 3. 创建默认图片模型
        model = await db.execute(
            __import__("sqlalchemy").select(AIModel).where(AIModel.model_name == "gpt-image-2")
        )
        model = model.scalar_one_or_none()
        if not model:
            model = AIModel(
                display_name="GPT-Image-2",
                provider_id=image_provider.id,
                category=ProviderCategory.IMAGE,
                model_name="gpt-image-2",
                is_default=True,
                is_enabled=True,
                prompt_max_length=5000,
            )
            db.add(model)
            await db.flush()
            print(f"[OK] 图片模型创建成功 (id={model.id})")
        else:
            print(f"[OK] 图片模型已存在 (id={model.id})")
            if not model.prompt_max_length:
                model.prompt_max_length = 5000

        # 3.1 创建默认对话模型（DeepSeek Chat）
        chat_model = await db.execute(
            __import__("sqlalchemy").select(AIModel).where(AIModel.model_name == "deepseek-chat")
        )
        chat_model = chat_model.scalar_one_or_none()
        if not chat_model:
            chat_model = AIModel(
                display_name="DeepSeek Chat",
                provider_id=deepseek.id,
                category=ProviderCategory.CHAT,
                model_name="deepseek-chat",
                is_default=True,
                is_enabled=True,
                prompt_max_length=8192,
            )
            db.add(chat_model)
            await db.flush()
            print(f"[OK] 对话模型创建成功 (id={chat_model.id})")
        else:
            if not chat_model.prompt_max_length:
                chat_model.prompt_max_length = 8192
            print(f"[OK] 对话模型已存在 (id={chat_model.id})")

        # 4. 将已有数据关联到 admin 用户
        sa = __import__("sqlalchemy")
        from sqlalchemy import update

        result_task = await db.execute(
            sa.select(AITask).where(AITask.user_id.is_(None))
        )
        orphan_tasks = result_task.scalars().all()
        if orphan_tasks:
            for t in orphan_tasks:
                t.user_id = admin_id
            print(f"[OK] 已将 {len(orphan_tasks)} 条 ai_task 关联到 admin")

        result_session = await db.execute(
            sa.select(AIChatSession).where(AIChatSession.user_id.is_(None))
        )
        orphan_sessions = result_session.scalars().all()
        if orphan_sessions:
            for s in orphan_sessions:
                s.user_id = admin_id
            print(f"[OK] 已将 {len(orphan_sessions)} 条 ai_chat_session 关联到 admin")

        if not orphan_tasks and not orphan_sessions:
            print("[OK] 所有数据已关联到 admin")

        await db.commit()

    await engine.dispose()


async def main():
    print("=" * 50)
    print("LeafAI 数据库初始化")
    print("=" * 50)

    await create_database()
    await create_tables_and_seed()

    print("=" * 50)
    print("初始化完成！种子数据：")
    print(f"  - 管理员: {ADMIN_USERNAME}（密码{'已按参数设置' if _IS_AUTO else '：admin123'}；生产环境请务必通过参数或环境变量指定）")
    print("  - 服务商: 图片服务 (OpenAI 兼容) / DeepSeek (对话)")
    print("  - 模型: gpt-image-2 / deepseek-chat")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())