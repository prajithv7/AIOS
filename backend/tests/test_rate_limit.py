"""Tests for §16 rate limiting + message size limits on AI endpoints."""

import os
import tempfile

_TEST_DB = f"{tempfile.gettempdir()}/aios_test_rl.db"
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ.setdefault("MASTER_KEY", "test-master-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')

import pytest
import httpx
from httpx import ASGITransport

from app.core.config import settings
from app.middleware import rate_limit as rl


class FakeRedis:
    """In-memory stand-in for the async Redis client."""

    def __init__(self):
        self.counters = {}

    async def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key, ttl):
        pass


class BrokenRedis:
    """Simulates Redis being down: every operation raises."""

    async def incr(self, key):
        raise ConnectionError("redis down")

    async def expire(self, key, ttl):
        raise ConnectionError("redis down")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def fake_redis(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(rl.limiter, "_client", client)
    return client


@pytest.fixture()
def reset_limiter(monkeypatch):
    monkeypatch.setattr(rl.limiter, "_client", None)
    monkeypatch.setattr(settings, "rate_limit_requests", 30)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "max_message_chars", 32000)
    monkeypatch.setattr(settings, "max_compare_chars", 64000)


@pytest.fixture(scope="session")
async def client():
    from app.db.migrations import run_migrations
    await run_migrations()
    from app.main import app
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
async def auth(client):
    r = await client.post("/api/auth/signup", json={"email": "rl@x.com", "name": "RL", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = await client.get("/api/users/me", headers={"Authorization": "Bearer " + token})
    user_id = me.json()["id"]
    return {"Authorization": "Bearer " + token}, user_id


def _conv_body(content="hello"):
    return {"conversationId": "does-not-matter", "content": content}


@pytest.mark.anyio
async def test_under_limit_allowed(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    # Handler is reached (401 provider auth error), not rate-limited (429).
    r = await client.post("/api/conversations/c1/messages", json=_conv_body(), headers=headers)
    assert r.status_code != 429


@pytest.mark.anyio
async def test_rate_limit_exceeded_429(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    monkeypatch_limit(2)
    codes = []
    for _ in range(3):
        r = await client.post("/api/compare", json={"content": "hi", "modelIds": ["m"]}, headers=headers)
        codes.append(r.status_code)
    assert codes[0] != 429
    assert codes[1] != 429
    assert codes[2] == 429
    assert r.json()["error"]["code"] == "RATE_LIMITED"


def monkeypatch_limit(n):
    # settings is a pydantic settings instance; patch the attribute directly.
    object.__setattr__(settings, "rate_limit_requests", n)


@pytest.mark.anyio
async def test_different_users_independent(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    monkeypatch_limit(1)
    r1 = await client.post("/api/compare", json={"content": "hi", "modelIds": ["m"]}, headers=headers)
    assert r1.status_code != 429
    # Second user's identity has its own counter.
    r2 = await rl.limiter.check("other-user-id")
    assert r2 is True


@pytest.mark.anyio
async def test_redis_unavailable_fails_open(client, auth, reset_limiter, monkeypatch):
    monkeypatch.setattr(rl.limiter, "_client", BrokenRedis())
    monkeypatch_limit(1)  # would block if Redis worked
    headers, _ = auth
    r = await client.post("/api/compare", json={"content": "hi", "modelIds": ["m"]}, headers=headers)
    assert r.status_code != 429


@pytest.mark.anyio
async def test_message_below_size_limit_allowed(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    r = await client.post("/api/conversations/c1/messages", json=_conv_body("x" * 100), headers=headers)
    assert r.status_code != 422


@pytest.mark.anyio
async def test_message_above_size_limit_rejected(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    object.__setattr__(settings, "max_message_chars", 50)
    r = await client.post("/api/conversations/c1/messages", json=_conv_body("x" * 51), headers=headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.anyio
async def test_compare_payload_above_limit_rejected(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    object.__setattr__(settings, "max_compare_chars", 10)
    r = await client.post("/api/compare", json={"content": "x" * 11, "modelIds": ["m"]}, headers=headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.anyio
async def test_stream_endpoint_rate_limited(client, auth, reset_limiter, fake_redis):
    headers, _ = auth
    monkeypatch_limit(1)
    r1 = await client.post("/chat/stream", json=_conv_body(), headers=headers)
    assert r1.status_code != 429
    r2 = await client.post("/chat/stream", json=_conv_body(), headers=headers)
    assert r2.status_code == 429
    assert r2.json()["error"]["code"] == "RATE_LIMITED"


@pytest.mark.anyio
async def test_limiter_uses_authenticated_user_identity(client, auth, reset_limiter, fake_redis):
    headers, user_id = auth
    await rl.limiter.check(user_id)
    assert any(user_id in key for key in fake_redis.counters)


@pytest.mark.anyio
async def test_configuration_values_respected(client, auth, reset_limiter, fake_redis):
    headers, user_id = auth
    object.__setattr__(settings, "rate_limit_requests", 3)
    object.__setattr__(settings, "rate_limit_window_seconds", 120)
    results = [await rl.limiter.check(user_id) for _ in range(3)]
    assert results == [True, True, True]
    assert await rl.limiter.check(user_id) is False
    # The window length affects the counter key (window_start is derived from it).
    assert any(k.startswith(rl.KEY_PREFIX + ":" + user_id + ":") for k in fake_redis.counters)


@pytest.mark.anyio
async def test_disabled_limiter_allows_all(client, auth, reset_limiter, fake_redis):
    object.__setattr__(settings, "rate_limit_enabled", False)
    headers, user_id = auth
    for _ in range(50):
        assert await rl.limiter.check(user_id) is True
    assert fake_redis.counters == {}
