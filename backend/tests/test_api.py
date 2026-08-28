import asyncio
import os
import tempfile

os.environ.setdefault("MASTER_KEY", "test-master-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
_TEST_DB = f"{tempfile.gettempdir()}/aios_test.db"
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')

import pytest
import httpx
from httpx import ASGITransport


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    from app.db.migrations import run_migrations
    await run_migrations()
    from app.main import app
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
async def authed(client):
    r = await client.post("/api/auth/signup", json={"email": "u@x.com", "name": "User", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": "Bearer " + token}


@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_auth_me(client, authed):
    r = await client.get("/api/users/me", headers=authed)
    assert r.status_code == 200
    assert r.json()["email"] == "u@x.com"


@pytest.mark.anyio
async def test_key_vault_masked(client, authed):
    r = await client.post("/api/keys", headers=authed, json={"provider_id": "openai", "api_key": "sk-secretvalue1234"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "connected"
    assert "sk-secretvalue1234" not in str(body)

    r = await client.get("/api/keys", headers=authed)
    assert r.status_code == 200
    for p in r.json():
        if p["provider_id"] == "openai":
            assert p["connected"] is True
            assert "sk-secretvalue1234" not in str(p["masked_key"])
        else:
            assert p["connected"] is False


@pytest.mark.anyio
async def test_models_registry(client, authed):
    r = await client.get("/api/models", headers=authed)
    assert r.status_code == 200
    models = r.json()
    assert len(models) >= 1
    assert any(m["authorized"] for m in models)


@pytest.mark.anyio
async def test_project_and_memory(client, authed):
    r = await client.post("/api/projects", headers=authed, json={"name": "Demo"})
    assert r.status_code == 200
    pid = r.json()["id"]

    r = await client.post(f"/api/projects/{pid}/memory", headers=authed,
                          json={"type": "notes", "content": "Use pydantic v2"})
    assert r.status_code == 200

    r = await client.get(f"/api/projects/{pid}/memory", headers=authed)
    assert r.status_code == 200
    assert any(e["content"] == "Use pydantic v2" for e in r.json())


@pytest.mark.anyio
async def test_recommend(client, authed):
    r = await client.post("/api/route/recommend", headers=authed, json={"content": "debug this python algorithm"})
    assert r.status_code == 200
    body = r.json()
    assert body["task_type"] == "coding"
    assert body["recommended_model_id"]


@pytest.mark.anyio
async def test_memory_injected_into_context(client, authed):
    r = await client.post("/api/projects", headers=authed, json={"name": "MemProj"})
    assert r.status_code == 200
    pid = r.json()["id"]

    r = await client.post(f"/api/projects/{pid}/memory", headers=authed,
                          json={"type": "tech_stack", "content": "Always use pydantic v2"})
    assert r.status_code == 200

    r = await client.post("/api/conversations", headers=authed, json={"title": "C", "project_id": pid})
    assert r.status_code == 200
    cid = r.json()["id"]

    from app.services.orchestration.service import OrchestrationService
    from sqlalchemy import select
    from app.db.schema import User
    from app.db.client import async_session_maker
    async with async_session_maker() as db:
        user = (await db.execute(select(User).where(User.email == "u@x.com"))).scalar_one()
        svc = OrchestrationService(db)
        conv = await svc.conversations.require(user.id, cid)
        ctx = await svc._build_context(user.id, conv, "Hello")
        assert any(m["role"] == "system" and "pydantic v2" in m["content"] for m in ctx)


@pytest.mark.anyio
async def test_project_summary_md(client, authed):
    r = await client.post("/api/projects", headers=authed, json={"name": "SummaryProj", "description": "Test project"})
    pid = r.json()["id"]
    await client.post(f"/api/projects/{pid}/memory", headers=authed,
                      json={"type": "notes", "content": "Important note"})

    r = await client.get(f"/api/projects/{pid}/summary", headers=authed)
    assert r.status_code == 200
    body = r.json()
    assert body["filename"].endswith(".md")
    assert "# Project Summary" in body["markdown"]
    assert "Important note" in body["markdown"]
    assert "Test project" in body["markdown"]


@pytest.mark.anyio
async def test_unauthorized(client):
    r = await client.get("/api/users/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_project_update_and_delete(client, authed):
    r = await client.post("/api/projects", headers=authed, json={"name": "TempProj", "description": "to delete"})
    assert r.status_code == 200
    pid = r.json()["id"]

    r = await client.put(f"/api/projects/{pid}", headers=authed, json={"name": "UpdatedProj"})
    assert r.status_code == 200
    assert r.json()["name"] == "UpdatedProj"
    assert r.json()["description"] == "to delete"

    r = await client.delete(f"/api/projects/{pid}", headers=authed)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r = await client.get(f"/api/projects/{pid}", headers=authed)
    assert r.status_code == 404


@pytest.mark.anyio
async def test_conversation_delete(client, authed):
    r = await client.post("/api/conversations", headers=authed, json={"title": "To Delete"})
    assert r.status_code == 200
    cid = r.json()["id"]

    r = await client.delete(f"/api/conversations/{cid}", headers=authed)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r = await client.get(f"/api/conversations/{cid}", headers=authed)
    assert r.status_code == 404


@pytest.mark.anyio
async def test_conversation_update_title(client, authed):
    r = await client.post("/api/conversations", headers=authed, json={"title": "Old Title"})
    assert r.status_code == 200
    cid = r.json()["id"]

    r = await client.patch(f"/api/conversations/{cid}", headers=authed, json={"title": "New Title"})
    assert r.status_code == 200
    assert r.json()["title"] == "New Title"


@pytest.mark.anyio
async def test_conversation_cannot_delete_others(client, authed):
    r = await client.post("/api/conversations", headers=authed, json={"title": "Owned"})
    cid = r.json()["id"]

    r2 = await client.post("/api/auth/signup", json={"email": "other@test.com", "name": "Other", "password": "pass123"})
    other_token = r2.json()["access_token"]
    other_headers = {"Authorization": "Bearer " + other_token}

    r = await client.delete(f"/api/conversations/{cid}", headers=other_headers)
    assert r.status_code == 404