# AIOS — Frontend

Next.js (App Router) frontend per `AIOS-frontend-final.md`. Editorial/docs theme with cream background, serif headings, single green accent.

## Getting started

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to backend origin
npm run dev
```

Point `NEXT_PUBLIC_API_URL` at the backend (default `http://localhost:8000`).

## Routes
- `/` — landing
- `/login`, `/signup` — auth
- `/app` → `/app/chat/:conversationId` — chat workspace (SSE)
- `/app/compare/:runId` — multi-model compare + judge
- `/app/projects`, `/app/projects/:id` — projects + memory
- `/app/keys` — key vault
- `/app/settings` — account

## Scripts
- `npm run dev` — dev server
- `npm run build` — production build
- `npm run typecheck` — `tsc --noEmit`
