import json
from typing import AsyncIterator, Optional
import httpx
from app.adapters.base import ChatClient
from app.core.exceptions import ProviderException, ProviderTokenExpired, ProviderQuotaExhausted, ProviderTimeout


class OpenAICompatibleChatClient(ChatClient):
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
                timeout=httpx.Timeout(self.extra_config.get("timeout", 120.0)),
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict],
        model_name: str,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict | AsyncIterator[dict]:
        client = await self._get_client()
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream,
        }
        if stream:
            payload["stream_options"] = {"include_usage": True}
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        api_path = self.extra_config.get("api_path", "/chat/completions")

        try:
            if stream:
                return self._stream_completion(client, api_path, payload)
            else:
                response = await client.post(api_path, json=payload)
                return self._handle_response(response)
        except httpx.TimeoutException:
            raise ProviderTimeout("对话请求超时")
        except httpx.ConnectError:
            raise ProviderException(f"无法连接到服务商: {self.base_url}")

    async def _stream_completion(self, client: httpx.AsyncClient, api_path: str, payload: dict) -> AsyncIterator[dict]:
        try:
            async with client.stream("POST", api_path, json=payload) as response:
                if response.status_code == 401:
                    raise ProviderTokenExpired()
                if response.status_code == 429:
                    raise ProviderQuotaExhausted()
                if response.status_code >= 400:
                    error_text = await response.aread()
                    raise ProviderException(f"服务商返回错误: {response.status_code} {error_text.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            yield json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
        except (ProviderTokenExpired, ProviderQuotaExhausted, ProviderException):
            raise
        except httpx.TimeoutException:
            raise ProviderTimeout("流式对话超时")
        except Exception as e:
            raise ProviderException(f"流式响应异常: {str(e)}")

    def _handle_response(self, response: httpx.Response) -> dict:
        if response.status_code == 401:
            raise ProviderTokenExpired()
        if response.status_code == 429:
            raise ProviderQuotaExhausted()
        if response.status_code >= 400:
            raise ProviderException(f"服务商返回错误: {response.status_code} {response.text}")
        return response.json()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None