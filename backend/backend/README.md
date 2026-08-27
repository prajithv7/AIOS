# AIOS — Backend

Unified multi-provider AI backend per `AIOS-backend-final.md`. FastAPI + LiteLLM + Turso/libSQL + Redis.

## Stack
- **FastAPI** — API server
- **LiteLLM** — unified LLM gateway (OpenAI, Anthropic, Gemini, DeepSeek, NVIDIA NIM, Ollama)
- **Turso / libSQL** — database (SQLite-compatible locally)
- **Redis** — cache, rate-limit, provider health, queue
- **JWT** access/refresh auth, envelope-encrypted key vault

## Getting started (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env   # set MASTER_KEY and JWT_SECRET to long random strings
uvicorn app.main:app --reload
```

Run Redis (required for full functionality): `docker compose up redis`

## API surface
- `/api/auth` — signup, login, refresh, logout (refresh in httpOnly cookie)
- `/api/keys` — encrypted key vault (masked reads only, no plaintext)
- `/api/providers`, `/api/models` — registry
- `/api/conversations/:id/messages` — chat send
- `/chat/stream` — SSE streaming
- `/api/compare` — multi-model fan-out + judge
- `/api/route/recommend` — model recommendation
- `/api/projects/:id/memory[/:memoryId]` — project memory

## Test
```bash
pytest
```
