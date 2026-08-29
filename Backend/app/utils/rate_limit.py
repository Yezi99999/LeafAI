import time
import functools
from typing import Callable, Optional
from app.core.config import get_settings

settings = get_settings()


class RateLimiter:
    def __init__(self, max_calls: int = 60, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self.calls: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key not in self.calls:
            self.calls[key] = []
        self.calls[key] = [t for t in self.calls[key] if now - t < self.period]
        if len(self.calls[key]) < self.max_calls:
            self.calls[key].append(now)
            return True
        return False

    def reset(self, key: str):
        self.calls.pop(key, None)


_global_limiter = RateLimiter(
    max_calls=settings.RATE_LIMIT_PER_MINUTE,
    period=60.0,
)


def rate_limit(key_func: Optional[Callable] = None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.RATE_LIMIT_ENABLED:
                return await func(*args, **kwargs)
            key = key_func(*args, **kwargs) if key_func else func.__name__
            if not _global_limiter.is_allowed(key):
                from app.core.exceptions import ProviderException
                raise ProviderException("请求过于频繁，请稍后重试")
            return await func(*args, **kwargs)
        return wrapper
    return decorator