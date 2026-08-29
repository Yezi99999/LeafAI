from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Any


class BaseAIClient(ABC):
    def __init__(self, api_key: str, base_url: str, extra_config: Optional[dict] = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.extra_config = extra_config or {}


class ChatClient(BaseAIClient, ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model_name: str,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict | AsyncIterator[dict]:
        pass


class ImageClient(BaseAIClient, ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_name: str,
        size: str = "1024x1024",
        n: int = 1,
        negative_prompt: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
        image: Optional[list[str]] = None,
        callback_url: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def query_task(self, remote_task_id: str) -> dict:
        pass


class VideoClient(BaseAIClient, ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_name: str,
        image_url: Optional[str] = None,
        duration: int = 5,
        resolution: str = "1080p",
        fps: int = 24,
    ) -> dict:
        pass


class AudioClient(BaseAIClient, ABC):
    @abstractmethod
    async def tts(
        self,
        text: str,
        model_name: str,
        voice: str = "default",
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        pass

    @abstractmethod
    async def asr(
        self,
        audio_bytes: bytes,
        model_name: str,
        language: Optional[str] = None,
    ) -> dict:
        pass