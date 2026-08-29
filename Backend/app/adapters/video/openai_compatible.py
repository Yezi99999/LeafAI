from typing import Optional
import httpx
from app.adapters.base import VideoClient
from app.core.exceptions import ProviderException, ProviderTokenExpired, ProviderQuotaExhausted, ProviderTimeout


class OpenAICompatibleVideoClient(VideoClient):
    def __init__(self, api_key: str, base_url: str, extra_config: Optional[dict] = None):
        super().__init__(api_key, base_url, extra_config)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.extra_config.get("timeout", 600.0)),
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        model_name: str,
        image_url: Optional[str] = None,
        duration: int = 5,
        resolution: str = "1080p",
        fps: int = 24,
    ) -> dict:
        client = await self._get_client()
        payload = {
            "model": model_name,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
        }
        if image_url:
            payload["image_url"] = image_url

        api_path = self.extra_config.get("api_path", "/videos/generations")

        try:
            response = await client.post(api_path, json=payload)
            if response.status_code == 401:
                raise ProviderTokenExpired()
            if response.status_code == 429:
                raise ProviderQuotaExhausted()
            if response.status_code >= 400:
                raise ProviderException(f"视频生成失败: {response.status_code} {response.text}")
            return response.json()
        except httpx.TimeoutException:
            raise ProviderTimeout("视频生成请求超时")
        except (ProviderTokenExpired, ProviderQuotaExhausted, ProviderException):
            raise
        except Exception as e:
            raise ProviderException(f"视频生成异常: {str(e)}")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None