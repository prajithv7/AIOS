"""Rate limiting for AI endpoints (spec §16) + request/message size limits.

Redis fixed-window counter per authenticated user, following the same
optional-Redis pattern as ``app.services.health.service.ProviderHealthService``:
when Redis (or the redis package) is unavailable the limiter fails open and
the request is allowed. Exceeding the limit raises the standardized
``RATE_LIMITED`` 429 error (spec §17).
"""

import time

from fastapi import Depends

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.errors import AppError

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    aioredis = None
    _REDIS_AVAILABLE = False

KEY_PREFIX = "aios:ratelimit"


class RateLimiter:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not settings.rate_limit_enabled:
            return None
        if not _REDIS_AVAILABLE:
            return None
        if self._client is None:
            self._client = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._client

    async def check(self, identity: str) -> bool:
        """Return True when the request is allowed (or when failing open)."""
        client = self._get_client()
        if client is None:
            return True
        window = max(1, settings.rate_limit_window_seconds)
        now = int(time.time())
        window_start = now - (now % window)
        key = f"{KEY_PREFIX}:{identity}:{window_start}"
        try:
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, window)
            return count <= settings.rate_limit_requests
        except Exception:
            # Redis down/misbehaving: fail open rather than break the AI service.
            return True

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass


limiter = RateLimiter()


async def ai_rate_limit(user_id: str = Depends(get_current_user_id)):
    """Dependency for AI-heavy endpoints; keyed on the authenticated user id."""
    if not await limiter.check(user_id):
        raise AppError("RATE_LIMITED", "Rate limit exceeded", 429)


def validate_content_size(content: str, max_chars: int, label: str = "Message") -> None:
    """Reject oversized payloads before they reach orchestration/LiteLLM (spec §16)."""
    if len(content) > max_chars:
        raise AppError(
            "INVALID_REQUEST",
            f"{label} exceeds maximum size of {max_chars} characters",
            422,
        )
