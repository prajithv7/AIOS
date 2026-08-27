# AIOS — AI Orchestration System

One workspace to chat with any connected AI provider, switch models mid-thread, fan a prompt across models, and get a judged winner. Built to `AIOS-backend-final.md` and `AIOS-frontend-final.md`.

## Layout
```
Aiso/
├── backend/    FastAPI + LiteLLM + Turso/libSQL + Redis (API server)
└── frontend/   Next.js (App Router) + Tailwind + TanStack Query + Zustand
```

## Run it
Backend (port 8000):
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # set MASTER_KEY + JWT_SECRET
docker compose up redis          # optional, for full redis features
uvicorn app.main:app --reload
```

Frontend (port 3000):
```bash
cd frontend
npm install
cp .env.example .env.local        # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Verify
- Backend: `GET http://localhost:8000/health`
- Backend tests: `cd backend && pytest`
- Frontend checks: `cd frontend && npm run typecheck && npm run build`

> Note: LiteLLM (the provider gateway) currently requires Python <3.14 and is split out to
> `backend/requirements-lite.txt`. Core auth/key-vault/registry endpoints run without it.