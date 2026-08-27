from app.core.config import settings

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    aioredis = None
    _REDIS_AVAILABLE = False

HEALTH_FLAG_TTL = 60
KEY_PREFIX = "aios:provider_health"


class ProviderHealthService:
    """Redis-backed per-provider health flags used by the fallback router (spec §12).

    A provider is marked unhealthy for ``HEALTH_FLAG_TTL`` seconds after a call
    fails; the fallback router skips unhealthy providers. Redis is optional: if
    it is unavailable every provider is treated as healthy so the app still works.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not _REDIS_AVAILABLE:
            return None
        if self._client is None:
            self._client = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._client

    def _key(self, provider_id: str) -> str:
        return f"{KEY_PREFIX}:{provider_id}"

    async def is_healthy(self, provider_id: str) -> bool:
        client = self._get_client()
        if client is None:
            return True
        try:
            return not bool(await client.exists(self._key(provider_id)))
        except Exception:
            return True

    async def record_failure(self, provider_id: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.setex(self._key(provider_id), HEALTH_FLAG_TTL, "down")
        except Exception:
            pass

    async def record_success(self, provider_id: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.delete(self._key(provider_id))
        except Exception:
            pass

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass