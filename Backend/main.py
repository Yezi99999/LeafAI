from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import uvicorn
import tomllib
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.session import engine, Base
from app.db.models import (
    User, AIProvider, AIModel, AIChatSession, AIChatMessage, AITask, OperationLog,
    FeatureToggle, PointsConsumptionRate, PointsTransaction, UserNotification,
    BusinessDailyStats, SystemConfig,
)
from app.api.v1.chat import router as chat_router
from app.api.v1.image import router as image_router
from app.api.v1.video import router as video_router
from app.api.v1.audio import router as audio_router
from app.api.v1.task import router as task_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.admin_features import admin_router as admin_features_router
from app.api.v1.admin_features import client_router as features_client_router
from app.api.v1.admin_points import router as admin_points_router
from app.api.v1.admin_notify import router as admin_notify_router
from app.api.v1.admin_analytics import router as admin_analytics_router
from app.api.v1.admin_audit import router as admin_audit_router
from app.api.v1.admin_config import router as admin_config_router
from app.api.v1.admin_records import router as admin_records_router
from app.api.v1.points import router as points_router
from app.api.v1.notify import router as notify_router
from app.api.v1.config import router as config_router
from app.api.v1.upload import router as upload_router
from app.api.v1.auth import router as auth_router

from app.services.toggle_service import ensure_defaults

settings = get_settings()


def get_project_version() -> str:
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "unknown"


PROJECT_VERSION = get_project_version()
PROJECT_NAME = "LeafAI"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # 预置核心能力开关（避免管理员手动逐个创建）；已存在则跳过
        from app.db.session import async_session_factory
        async with async_session_factory() as _db:
            await ensure_defaults(_db)
            await _db.commit()
        print("数据库表初始化完成")
    except Exception as e:
        print(f"数据库连接失败，表未自动创建: {e}")
        print("请先执行: python init_db.py")
    yield
    await engine.dispose()


app = FastAPI(
    title=PROJECT_NAME,
    version=PROJECT_VERSION,
    description="LeafAI AI平台后台服务",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "msg": exc.msg,
            "data": None,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """统一 HTTP 错误信封：所有接口返回 code/msg/data。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": str(exc.detail),
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验错误统一信封。"""
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "msg": "参数校验失败",
            "data": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": f"服务器内部错误: {str(exc)}",
            "data": None,
        },
    )


api_prefix = settings.API_V1_PREFIX
app.include_router(chat_router, prefix=api_prefix)
app.include_router(image_router, prefix=api_prefix)
app.include_router(video_router, prefix=api_prefix)
app.include_router(audio_router, prefix=api_prefix)
app.include_router(task_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(admin_users_router, prefix=api_prefix)
app.include_router(admin_features_router, prefix=api_prefix)
app.include_router(features_client_router, prefix=api_prefix)
app.include_router(admin_points_router, prefix=api_prefix)
app.include_router(admin_notify_router, prefix=api_prefix)
app.include_router(admin_analytics_router, prefix=api_prefix)
app.include_router(admin_audit_router, prefix=api_prefix)
app.include_router(admin_config_router, prefix=api_prefix)
app.include_router(admin_records_router, prefix=api_prefix)
app.include_router(points_router, prefix=api_prefix)
app.include_router(notify_router, prefix=api_prefix)
app.include_router(config_router, prefix=api_prefix)
app.include_router(upload_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)

# 本地存储静态目录（上传图片等对外公开访问）
try:
    from pathlib import Path as _P
    _storage = _P(settings.FILE_STORAGE_PATH)
    _storage.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(_storage)), name="static")
except Exception as e:
    print(f"[warn] 静态存储目录挂载失败: {e}")


@app.get("/")
def read_root():
    return {"project": PROJECT_NAME, "version": PROJECT_VERSION}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )