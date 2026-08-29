from typing import Optional
import httpx
from app.adapters.base import AudioClient
from app.core.exceptions import ProviderException, ProviderTokenExpired, ProviderQuotaExhausted, ProviderTimeout


class OpenAICompatibleAudioClient(AudioClient):
    def __init__(self, api_key: str, base_url: str, extra_config: Optional[dict] = None):
        super().__init__(api_key, base_url, extra_config)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.extra_config.get("timeout", 120.0)),
            )
        return self._client

    async def tts(
        self,
        text: str,
        model_name: str,
        voice: str = "default",
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        client = await self._get_client()
        payload = {
            "model": model_name,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
        }
        api_path = self.extra_config.get("tts_api_path", "/audio/speech")

        try:
            response = await client.post(api_path, json=payload)
            if response.status_code == 401:
                raise ProviderTokenExpired()
            if response.status_code == 429:
                raise ProviderQuotaExhausted()
            if response.status_code >= 400:
                raise ProviderException(f"TTS失败: {response.status_code} {response.text}")
            return response.content
        except httpx.TimeoutException:
            raise ProviderTimeout("TTS请求超时")
        except (ProviderTokenExpired, ProviderQuotaExhausted, ProviderException):
            raise
        except Exception as e:
            raise ProviderException(f"TTS异常: {str(e)}")

    async def asr(
        self,
        audio_bytes: bytes,
        model_name: str,
        language: Optional[str] = None,
    ) -> dict:
        client = await self._get_client()
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": model_name}
        if language:
            data["language"] = language

        api_path = self.extra_config.get("asr_api_path", "/audio/transcriptions")

        try:
            response = await client.post(api_path, data=data, files=files)
            if response.status_code == 401:
                raise ProviderTokenExpired()
            if response.status_code == 429:
                raise ProviderQuotaExhausted()
            if response.status_code >= 400:
                raise ProviderException(f"ASR失败: {response.status_code} {response.text}")
            return response.json()
        except httpx.TimeoutException:
            raise ProviderTimeout("ASR请求超时")
        except (ProviderTokenExpired, ProviderQuotaExhausted, ProviderException):
            raise
        except Exception as e:
            raise ProviderException(f"ASR异常: {str(e)}")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None