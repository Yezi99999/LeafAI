"""图片上传（可作为独立图床使用）：
- POST  /upload/image        上传一张图片，落盘到本地存储并返回公开 URL（OSS 连接）
- GET   /upload/image/config 返回当前上传限制（单图大小 / 数量）
"""
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_user
from app.core.config import get_settings
from app.services import upload_service

router = APIRouter(prefix="/upload", tags=["文件上传"])

_ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/bmp": "bmp",
}


@router.get("/image/config", response_model=BaseResponse)
async def upload_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BaseResponse(data=await upload_service.get_upload_config(db))


@router.post("/image", response_model=BaseResponse)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ctype = (file.content_type or "").lower()
    if ctype not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的图片类型: {ctype or '未知'}")

    cfg = await upload_service.get_upload_config(db)
    max_bytes = cfg["max_size_mb"] * 1024 * 1024
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"图片大小超过限制({cfg['max_size_mb']}MB)")

    settings = get_settings()
    upload_dir = Path(settings.FILE_STORAGE_PATH) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}.{_ALLOWED_TYPES[ctype]}"
    (upload_dir / file_name).write_bytes(data)

    base = str(request.base_url).rstrip("/") if request else ""
    url = f"{base}/static/uploads/{file_name}"
    return BaseResponse(data={
        "url": url,
        "file_name": file_name,
        "size": len(data),
        "content_type": ctype,
    })