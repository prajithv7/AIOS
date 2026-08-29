# Arbiter

> One workspace to chat with any AI provider, switch models mid-thread without losing context, fan a prompt out to multiple models, and get a judged comparison — with secure key management and project-level memory.

Arbiter (formerly *AIOS*) is a unified backend + frontend for interacting with multiple AI providers through a single conversation. It preserves context across model switches, runs multi-model comparisons with an AI judge, recommends the best model per task, stores project memory, manages provider API keys securely, and falls back automatically when a provider is unavailable.

---

## Table of Contents

- [Why Arbiter](#why-arbiter)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Design System](#design-system)
- [Screens / Routes](#screens--routes)
- [API Routes](#api-routes)
- [Database Schema](#database-schema)
- [Error Handling](#error-handling)
- [Security](#security)
- [Phased Build Plan](#phased-build-plan)
- [Getting Started](#getting-started)
- [Principles](#principles)

---

## Why Arbiter

Most AI chat tools lock you into a single provider and a single opinion. Arbiter treats providers as interchangeable, ranked backends:

- Connect OpenAI, Anthropic, Gemini, DeepSeek, NVIDIA NIM, and Ollama through one interface
- Switch models mid-conversation without losing context
- Send the same task to several models at once and see a judged, scored comparison
- Get a model recommendation for a given task based on capability, not a hardcoded provider preference
- Keep project-level memory (instructions, decisions, tech stack, preferences) separate from raw chat history
- Fall back automatically to another authorized provider if one goes down

---

## Core Features

| Feature | Description |
|---|---|
| **Multi-provider chat** | Single normalized conversation format across all providers |
| **Model switching** | Switch models mid-thread; backend reconstructs the context for the new provider |
| **Multi-model compare** | Fan out one prompt to 2–4 models in parallel, view responses side by side |
| **AI Judge** | Structured scoring (correctness, relevance, completeness, reasoning, code quality, instruction-following, clarity) with a winner and reasoning — a recommendation, not an absolute verdict |
| **Auto-recommendation** | Routes tasks (coding, reasoning, long-document, vision) to capability-matched models |
| **Provider fallback** | Automatic retry with an authorized alternate provider on failure, logged with reason |
| **Key vault** | Encrypted API key storage; keys are never returned to the frontend after creation |
| **Project memory** | Structured, retrievable-on-demand memory per project, distinct from chat history |
| **Streaming** | Token-by-token SSE streaming with graceful failure handling |

---

## Architecture

```text
Client
  |
  v
API Server
  |
  +--> Auth / User Management
  |
  +--> Conversation Service
  |
  +--> Context / Memory Service
  |
  +--> AI Orchestrator
  |      |
  |      +--> LLMGateway (LiteLLM) — wraps all provider adapters
  |
  +--> Model Router (Task Classification -> Model Selection -> Fallback)
  |
  +--> Comparison / Judge Service
  |
  +--> API Key / Credential Service
  |
  v
Turso Database (+ Redis for state/cache)
```

**Key design rule:** these layers stay separate. Routing decisions never hardcode a provider name — capability metadata drives selection:

```text
Provider → Model → Capability → User Authorization → Routing Decision → AI Execution
```

### AI Orchestrator flow

1. Load conversation history
2. Load only the relevant project/context memory (never the whole store)
3. Determine task type
4. Select the requested or recommended model
5. Build a provider-neutral request
6. Resolve the user's key from the vault, call via `LLMGateway`
7. Store the response, tagged with model/provider
8. Return the result to the client

### Multi-model fan-out

```text
User Task → AI Orchestrator → [Model A, Model B, Model C] (parallel) → Comparison/Judge → Final Result
```

### Provider Adapter interface

Every provider is accessed through one interface (implemented via LiteLLM, with a thin project-specific wrapper for typing/error normalization). Application code never depends on a provider SDK directly:

```ts
interface AIProvider {
  chat(request: ChatRequest): Promise<ChatResponse>;
  stream(request: ChatRequest): AsyncIterable<ChatChunk>;
  getModels(): Promise<ModelInfo[]>;
  healthCheck(): Promise<boolean>;
}
```

### Provider fallback

```text
Requested Model → Health Check/Request
   +-- Success -> Response
   +-- Failure -> Fallback Router -> Authorized Model -> Response
```

- Only falls back among providers the user has authorized
- Never silently switches if it violates user config/privacy settings
- Every fallback is recorded: original provider/model, failure reason, fallback provider/model, timestamp
- Redis-backed health/status flags per provider, updated on error/timeout

---

## Tech Stack

### Backend

| Layer | Choice |
|---|---|
| Framework | FastAPI (Python) |
| LLM Gateway | LiteLLM — unified interface across OpenAI, Anthropic, Gemini, DeepSeek, NVIDIA NIM, Ollama |
| Database | Turso (libSQL — SQLite-compatible, edge-hosted) |
| Cache/Queue | Redis — session state, rate-limit counters, job queue, provider health flags |
| Containerization | Docker / Docker Compose |
| Coding agent | opencode |

### Frontend

| Layer | Choice |
|---|---|
| Framework | React 18 + Next.js (App Router) |
| Styling | Tailwind CSS + CSS variables for theme tokens (light/dark) |
| State/data | TanStack Query (server state) + Zustand (UI/session state) |
| Realtime | Native `EventSource` (SSE) for `/chat/stream`, with WebSocket fallback |
| Forms | React Hook Form + Zod validation |
| Charts | Recharts (judge scores) |
| Auth | JWT access/refresh — refresh in an httpOnly cookie, access token in memory |
| Icons | Tabler outline icon set |

---

## Repository Structure

### Backend

```text
backend/
├── app/  (or src/)
│   ├── api/            # routes
│   ├── core/            # config, security, env
│   ├── db/              # schema, migrations, client (Turso)
│   ├── models/          # ORM/data models
│   ├── services/
│   │   ├── auth/
│   │   ├── conversations/
│   │   ├── memory/
│   │   ├── orchestration/   # AI Orchestrator
│   │   ├── routing/         # Model Router
│   │   ├── comparison/      # Judge
│   │   └── credentials/     # Key vault
│   ├── providers/
│   │   └── llm_gateway.py   # LiteLLM wrapper implementing AIProvider interface
│   └── middleware/
├── tests/
├── docker-compose.yml
├── .env.example
└── README.md
```

### Frontend

```text
frontend/
├── app/
│   ├── (marketing)/page.tsx        # Landing
│   ├── login/  signup/
│   └── app/
│       ├── chat/[conversationId]/
│       ├── compare/[runId]/
│       ├── projects/  projects/[id]/
│       ├── keys/
│       └── settings/
├── components/
│   ├── ui/            # Button, Card, Badge, StepRow, CodePreview
│   ├── chat/           # MessageBubble, Composer, ModelSelector, StreamRenderer
│   ├── compare/         # ModelPicker, ComparisonGrid, JudgeSummary
│   └── keys/            # ProviderCard, ConnectKeyModal
├── lib/
│   ├── api/              # typed fetch/query wrappers per backend route group
│   ├── stream/           # SSE client
│   └── stores/            # Zustand stores
├── styles/
│   └── tokens.css          # CSS variables (design tokens)
└── tests/
```

---

## Design System

Editorial/documentation visual theme: warm cream background, serif headings, a single deep teal-green accent.

### Palette (light mode)

| Token | Value | Use |
|---|---|---|
| `--bg-page` | `#F4F1EA` | page background |
| `--surface-card` | `#FFFFFF` | cards, panels |
| `--text-primary` | `#1A1A1A` | headings, primary text |
| `--text-secondary` | `#555555` | body/supporting text |
| `--text-muted` | `#888888` | captions, meta |
| `--accent` | `#0F6E56` | primary buttons, links, active states |
| `--accent-soft` | `#E1F5EE` | accent-tinted chips/badges |
| `--border` | `#E4E1D8` | hairline borders (1px) |
| `--code-bg` | `#1E1E1E` | code/JSON preview blocks |
| `--code-text` | `#9FE1CB` | code block text |

Dark mode: `--bg-page:#161513`, `--surface-card:#1F1E1B`, `--text-primary:#F4F1EA`, accent bumped to `#1D9E75` for contrast.

### Typography

- Headings: serif (`Source Serif 4` / `Georgia` fallback), weight 500 only
- Body/UI: sans (`Inter` or system-ui), weights 400/500 only
- Sentence case everywhere — no Title Case, no ALL CAPS except small eyebrow labels (12px, letter-spacing 1px)

### Components

- **Buttons** — primary: solid accent bg, white text, 8px radius. Secondary: transparent, 1px border, hover fills surface.
- **Cards** — white bg, 1px border, 12px radius, `padding: 1rem 1.25rem`.
- **Step rows** — numbered eyebrow (`01`, `02`…), serif sub-heading, 1–2 line description; even steps on white, odd steps on accent-soft tint, banding the row instead of reading flat.
- **Code/JSON preview** — dark card, mono font, filename tab with a "Copy" action.
- **Badges** — pill, accent-soft bg + accent text, 12px font.

---

## Screens / Routes

```text
/                        Landing (marketing/explainer)
/login, /signup          Auth
/app                      Redirect → /app/chat (last active conversation)
/app/chat/:conversationId Main chat workspace
/app/compare/:runId      Multi-model comparison + judge result view
/app/projects            Project list
/app/projects/:id        Project detail (conversations + memory)
/app/keys                 API key vault management
/app/settings              Account, preferences, default models
```

### Landing (`/`)

Hero with eyebrow label, serif H1, subhead, primary CTA ("Open workspace") and secondary CTA ("See the docs"); a small JSON preview of an example `/api/compare` request; a 4-step "How it works" strip (*Connect your keys → Ask anything → Compare on demand → Get the judged winner*); footer strip of provider name badges.

### Chat workspace (`/app/chat/:conversationId`)

- Left rail: conversation list grouped by project, "New conversation" button
- Top bar: model selector with capability badges, a "Recommend" toggle that calls `/api/route/recommend`
- Message thread: role-tagged bubbles; assistant messages show a footer chip with the `model_id`/`provider_id` used, so a model switch mid-thread stays visible
- Composer: text input, attach affordance (future), a "Compare across models" button
- Streaming: tokens render incrementally via SSE; failures show an inline retry chip

### Multi-model compare (`/app/compare/:runId`)

Picker step: checklist of authorized models (2–4 recommended) plus the task input. Result step: one response card per model with latency/token usage, a top summary panel with the judge's winner, per-model scores as a bar chart, and the judge's reasoning. Failed providers render as a dimmed card with the error code rather than disappearing.

### API key vault (`/app/keys`)

Provider list with connection status badges. "Connect" opens a modal with a single masked input; the backend returns only a masked confirmation (e.g. `sk-••••4f2a`) — the frontend never requests or renders a decrypted key. Disconnect requires a confirm dialog.

### Projects (`/app/projects`, `/app/projects/:id`)

List view: cards with name, conversation count, last active. Detail view: tabs for Conversations and Memory (instructions, decisions, tech stack, preferences, notes) as editable structured entries, not free chat.

### Settings (`/app/settings`)

Default model, default judge model, account/session management, logout.

---

## API Routes

```text
/api/auth
/api/users
/api/conversations
/api/messages
/api/models
/api/providers
/api/compare
/api/route
/api/memory
/api/keys
```

Examples:

```http
POST /api/conversations/:conversationId/messages   { "content": "...", "modelId": "model_id" }
POST /api/compare        { "conversationId", "content", "modelIds": [...] }
POST /api/route/recommend { "content": "Debug this Python algorithm" }
GET  /api/providers
GET  /api/models
POST /api/keys
DELETE /api/keys/:providerId
POST/GET/DELETE /api/projects/:projectId/memory[/:memoryId]
```

Auth endpoints: `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout` (JWT access + refresh). Every conversation/project/credential/model request verifies resource ownership against the authenticated session — a frontend-supplied `user_id` is never trusted.

Streaming: SSE (or WebSocket) at `/chat/stream`; LiteLLM output is proxied token-by-token. The completed assistant message is stored once the stream finishes; failed streams are stored as a failed run with a normalized error.

---

## Database Schema

Turso (libSQL). Tables:

```text
users, sessions, providers, models, user_providers, api_credentials,
conversations, messages, projects, project_memory,
model_runs, comparisons, fallback_events, usage_records
```

Key tables:

| Table | Columns |
|---|---|
| `users` | `id, email, name, created_at, updated_at` |
| `api_credentials` | `id, user_id, provider_id, encrypted_key, created_at, updated_at` |
| `conversations` | `id, user_id, project_id, title, created_at, updated_at` |
| `messages` | `id, conversation_id, role, content, provider_id, model_id, metadata_json, created_at` |
| `models` | `id, provider_id, model_key, display_name, capabilities_json, context_window, supports_streaming, supports_tools, supports_vision, status, created_at, updated_at` |
| `project_memory` | `id, project_id, type, content, metadata_json, created_at, updated_at` |
| `model_runs` | `id, conversation_id, message_id, provider_id, model_id, status, latency_ms, input_tokens, output_tokens, error_code, created_at` |
| `comparisons` | `id, conversation_id, task_message_id, winner_model_id, result_json, created_at` |
| `fallback_events` | `id, conversation_id, original_provider_id, original_model_id, fallback_provider_id, fallback_model_id, reason, created_at` |

Indexes: `users.email`, `sessions.user_id`, `conversations.user_id`, `messages.conversation_id`, `projects.user_id`, `project_memory.project_id`, `models.provider_id`, `model_runs.conversation_id`, `model_runs.created_at`.

Conventions: foreign keys where appropriate; UTC timestamps; UUID/ULID public-facing IDs (never sequential internal IDs); migrations via Alembic or a libSQL-compatible SQL runner.

---

## Error Handling

Normalized error envelope:

```json
{ "error": { "code": "PROVIDER_UNAVAILABLE", "message": "The selected AI provider is temporarily unavailable.", "requestId": "req_123" } }
```

Codes: `AUTH_REQUIRED, FORBIDDEN, INVALID_REQUEST, MODEL_NOT_FOUND, PROVIDER_NOT_FOUND, PROVIDER_UNAUTHORIZED, PROVIDER_UNAVAILABLE, MODEL_UNAVAILABLE, RATE_LIMITED, CONTEXT_TOO_LARGE, AI_REQUEST_FAILED, INTERNAL_ERROR`

All provider-specific errors are normalized into these types before reaching the client.

### Frontend mapping

| Backend code | UI treatment |
|---|---|
| `AUTH_REQUIRED` / `FORBIDDEN` | Redirect to `/login`, toast "Your session expired" |
| `PROVIDER_UNAVAILABLE` / `MODEL_UNAVAILABLE` | Inline chip on the affected message/card, offer fallback model if one exists |
| `RATE_LIMITED` | Disable composer briefly, show retry-after if provided |
| `CONTEXT_TOO_LARGE` | Inline warning above composer, suggest a new conversation or summarizing |
| `PROVIDER_UNAUTHORIZED` | Link directly to `/app/keys` for that provider |
| `INTERNAL_ERROR` | Generic toast, no stack trace ever rendered |

---

## Security

- Envelope encryption at rest for provider keys (Fernet/AES-GCM); master key from env/secrets manager, never stored in Turso
- Decrypted keys are never returned to the frontend after creation, and never logged
- Keys never appear in conversation messages or get committed to Git
- User auth passwords hashed with argon2/bcrypt
- All request bodies, model/provider IDs validated
- Protected routes authenticated; resource ownership authorized on every request
- AI endpoints rate-limited; request/message sizes capped
- Metadata sanitized/validated
- HTTPS in production; CORS restricted to trusted origins
- Server secrets via environment variables only
- Error messages never leak provider credentials or stack traces

**Build rule:** the key vault is written and reviewed before any other network-facing feature ships.

---

## Phased Build Plan

### Backend

| Phase | Scope | Exit criteria |
|---|---|---|
| 1 — Foundation | JWT auth (signup/login/refresh/logout), encrypted key vault (masked GET, no plaintext ever), core schema (`users, provider_keys, conversations, messages, projects`), Turso/Docker setup | Auth works end-to-end; keys unreadable in DB; migrations run cleanly |
| 2 — Core Routing | LiteLLM integration (`LLMGateway`), conversation engine with context preservation across model switches, SSE/WebSocket streaming, Redis-backed provider health + fallback retry | User can chat, switch models mid-thread, see streamed output, survive a simulated provider outage |
| 3 — Judge, Compare, Recommend, Memory | Fan-out execution (`/api/compare`), rubric-based AI Judge, recommendation engine (heuristic → learned ranking), project memory | A prompt runs against 3+ models simultaneously, gets judged/scored/stored, with a recommendation surfaced |
| 4 — Post-MVP | Advanced routing, usage analytics, cost-aware routing, RAG-based memory, provider health dashboards | — |

### Frontend

| Phase | Scope | Exit criteria |
|---|---|---|
| 1 — Foundation | Auth screens, key vault UI (connect/disconnect, masked status only), design tokens/theme setup | User can sign up, log in, add a masked key, see it listed as connected |
| 2 — Core Chat | Chat workspace with model selector, SSE streaming, model-switch-mid-thread UI, fallback indicator | User can chat, switch models, watch streamed output, see a fallback event surfaced |
| 3 — Compare, Judge, Projects | Multi-model compare screen, judge summary + score chart, Projects with memory tabs | User runs a prompt against 3+ models, sees judged winner + scores, attaches a conversation to a project |
| 4 — Post-MVP | Usage analytics dashboard, cost-aware model picker, provider health status page, RAG-memory search UI | — |

---

## Getting Started

```bash
# Backend
cd backend
cp .env.example .env         # fill in Turso URL/token, Redis URL, JWT secret, encryption master key
docker compose up --build

# Frontend
cd frontend
cp .env.example .env.local   # point at the backend API base URL
npm install
npm run dev
```

> Fill in provider API keys through the app itself (`/app/keys`) after signing up — never in `.env`.

---

## Principles

**Backend:** provider-agnostic · modular · secure · testable · observable · extensible · database-driven configuration · resilient to provider failure · new providers addable without rewriting core orchestration. Core architectural components: AI Orchestrator + Provider Adapter (LiteLLM-backed) + Model Registry.

**Frontend:** provider-agnostic UI (never hardcode a provider's name into logic, only display it) · every screen traceable to a real backend route · no key material ever rendered · streaming-first chat · comparison and judging are first-class, not an afterthought.
