from typing import Optional
import httpx
from app.adapters.base import ImageClient
from app.core.exceptions import ProviderException, ProviderTokenExpired, ProviderQuotaExhausted, ProviderTimeout


class OpenAICompatibleImageClient(ImageClient):
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
                timeout=httpx.Timeout(self.extra_config.get("timeout", 300.0)),
            )
        return self._client

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
        client = await self._get_client()
        payload: dict = {
            "model": model_name,
            "prompt": prompt,
            "size": size,
        }
        if quality:
            payload["quality"] = quality
        if style:
            payload["style"] = style
        if image:
            payload["image"] = image if len(image) > 1 else image[0]
        if callback_url:
            payload["callback_url"] = callback_url

        api_path = self.extra_config.get("api_path", "/images/generations")
        use_async = self.extra_config.get("async", True)

        params = {}
        if use_async:
            params["async"] = "true"

        try:
            response = await client.post(api_path, json=payload, params=params)
            if response.status_code == 401:
                raise ProviderTokenExpired()
            if response.status_code == 429:
                raise ProviderQuotaExhausted()
            if response.status_code >= 400:
                raise ProviderException(f"图片生成失败: {response.status_code} {response.text}")
            return response.json()
        except httpx.TimeoutException:
            raise ProviderTimeout("图片生成请求超时")
        except (ProviderTokenExpired, ProviderQuotaExhausted, ProviderException):
            raise
        except Exception as e:
            raise ProviderException(f"图片生成异常: {str(e)}")

    async def query_task(self, remote_task_id: str) -> dict:
        client = await self._get_client()
        try:
            response = await client.get(f"/tasks/{remote_task_id}")
            if response.status_code == 401:
                raise ProviderTokenExpired()
            if response.status_code >= 400:
                raise ProviderException(f"查询任务失败: {response.status_code} {response.text}")
            return response.json()
        except httpx.TimeoutException:
            raise ProviderTimeout("查询任务超时")
        except (ProviderTokenExpired, ProviderException):
            raise
        except Exception as e:
            raise ProviderException(f"查询任务异常: {str(e)}")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None