from functools import lru_cache
from typing import Type, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AIModel, AIProvider, ProviderCategory
from app.adapters.base import BaseAIClient, ChatClient, ImageClient, VideoClient, AudioClient
from app.adapters.chat.openai_compatible import OpenAICompatibleChatClient
from app.adapters.image.openai_compatible import OpenAICompatibleImageClient
from app.adapters.video.openai_compatible import OpenAICompatibleVideoClient
from app.adapters.audio.openai_compatible import OpenAICompatibleAudioClient
from app.core.exceptions import ModelNotFoundException, ProviderException


class AIScheduler:
    ADAPTER_MAP = {
        ProviderCategory.CHAT: OpenAICompatibleChatClient,
        ProviderCategory.IMAGE: OpenAICompatibleImageClient,
        ProviderCategory.VIDEO: OpenAICompatibleVideoClient,
        ProviderCategory.AUDIO: OpenAICompatibleAudioClient,
    }

    def __init__(self):
        self._clients: dict[int, BaseAIClient] = {}

    async def get_client(self, db: AsyncSession, model_id: int) -> BaseAIClient:
        if model_id in self._clients:
            return self._clients[model_id]

        model = await self._get_model(db, model_id)
        provider = await self._get_provider(db, model.provider_id)

        adapter_cls = self.ADAPTER_MAP.get(provider.category)
        if adapter_cls is None:
            raise ProviderException(f"不支持的模型类别: {provider.category}")

        client = adapter_cls(
            api_key=provider.api_key or "",
            base_url=provider.base_url or "",
            extra_config=provider.extra_config or {},
        )
        self._clients[model_id] = client
        return client

    async def get_chat_client(self, db: AsyncSession, model_id: int) -> ChatClient:
        client = await self.get_client(db, model_id)
        if not isinstance(client, ChatClient):
            raise ProviderException("模型不是对话类型")
        return client

    async def get_image_client(self, db: AsyncSession, model_id: int) -> ImageClient:
        client = await self.get_client(db, model_id)
        if not isinstance(client, ImageClient):
            raise ProviderException("模型不是图片生成类型")
        return client

    async def get_video_client(self, db: AsyncSession, model_id: int) -> VideoClient:
        client = await self.get_client(db, model_id)
        if not isinstance(client, VideoClient):
            raise ProviderException("模型不是视频生成类型")
        return client

    async def get_audio_client(self, db: AsyncSession, model_id: int) -> AudioClient:
        client = await self.get_client(db, model_id)
        if not isinstance(client, AudioClient):
            raise ProviderException("模型不是语音类型")
        return client

    async def _get_model(self, db: AsyncSession, model_id: int) -> AIModel:
        result = await db.execute(
            select(AIModel).where(AIModel.id == model_id, AIModel.is_enabled == True)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ModelNotFoundException(f"模型不存在或未启用: model_id={model_id}")
        return model

    async def _get_provider(self, db: AsyncSession, provider_id: int) -> AIProvider:
        result = await db.execute(
            select(AIProvider).where(AIProvider.id == provider_id, AIProvider.is_enabled == True)
        )
        provider = result.scalar_one_or_none()
        if provider is None:
            raise ProviderException(f"服务商不存在或未启用: provider_id={provider_id}")
        return provider

    def clear_client(self, model_id: int):
        self._clients.pop(model_id, None)

    def clear_all(self):
        self._clients.clear()


@lru_cache()
def get_scheduler() -> AIScheduler:
    return AIScheduler()