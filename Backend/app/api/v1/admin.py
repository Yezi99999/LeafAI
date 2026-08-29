from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import AIProvider, AIModel
from app.schemas.admin import (
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ModelCreate, ModelUpdate, ModelResponse,
)
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/providers", response_model=BaseResponse)
async def list_providers(
    category: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(AIProvider)
    if category:
        query = query.where(AIProvider.category == category)
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(AIProvider.id)

    result = await db.execute(query)
    providers = result.scalars().all()

    count_query = select(AIProvider)
    if category:
        count_query = count_query.where(AIProvider.category == category)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return BaseResponse(data={
        "items": [ProviderResponse.model_validate(p) for p in providers],
        "total": total,
    })


@router.post("/providers", response_model=BaseResponse)
async def create_provider(
    req: ProviderCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(AIProvider).where(AIProvider.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="服务商名称已存在")

    provider = AIProvider(
        name=req.name,
        category=req.category,
        api_key=req.api_key,
        base_url=req.base_url,
        timeout=req.timeout,
        extra_config=req.extra_config,
        is_enabled=req.is_enabled,
        priority=req.priority,
    )
    db.add(provider)
    await db.flush()
    return BaseResponse(data=ProviderResponse.model_validate(provider))


@router.put("/providers/{provider_id}", response_model=BaseResponse)
async def update_provider(
    provider_id: int,
    req: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=404, detail="服务商不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(provider, key, value)

    return BaseResponse(data=ProviderResponse.model_validate(provider))


@router.delete("/providers/{provider_id}", response_model=BaseResponse)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=404, detail="服务商不存在")
    await db.delete(provider)
    return BaseResponse(msg="服务商已删除")


@router.get("/models", response_model=BaseResponse)
async def list_models(
    category: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(AIModel)
    if category:
        query = query.where(AIModel.category == category)
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(AIModel.id)

    result = await db.execute(query)
    models = result.scalars().all()

    count_query = select(AIModel)
    if category:
        count_query = count_query.where(AIModel.category == category)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return BaseResponse(data={
        "items": [ModelResponse.model_validate(m) for m in models],
        "total": total,
    })


@router.post("/models", response_model=BaseResponse)
async def create_model(
    req: ModelCreate,
    db: AsyncSession = Depends(get_db),
):
    provider_result = await db.execute(select(AIProvider).where(AIProvider.id == req.provider_id))
    if provider_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="服务商不存在")

    model = AIModel(
        display_name=req.display_name,
        provider_id=req.provider_id,
        category=req.category,
        model_name=req.model_name,
        is_default=req.is_default,
        is_enabled=req.is_enabled,
    )
    db.add(model)
    await db.flush()
    return BaseResponse(data=ModelResponse.model_validate(model))


@router.put("/models/{model_id}", response_model=BaseResponse)
async def update_model(
    model_id: int,
    req: ModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)

    return BaseResponse(data=ModelResponse.model_validate(model))


@router.delete("/models/{model_id}", response_model=BaseResponse)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    await db.delete(model)
    return BaseResponse(msg="模型已删除")