<p align="center">
  <img src="./arbiter-logo.png" alt="Arbiter logo" width="160">
</p>

<h1 align="center">Arbiter</h1>
<h1 align="center">Arbiter</h1>

<p align="center">
  <strong>One workspace. Every model. One intelligent judge.</strong>
</p>

<p align="center">
  Arbiter brings multiple AI providers and models into a single workspace.
  Chat, switch models, compare responses, route tasks intelligently,
  and let an AI judge identify the strongest answer.
</p>

<p align="center">
  <em>
    Built for developers who want control over their AI workflow.
  </em>
</p>

<p align="center">
  <a href="https://github.com/prajithv7/AIOS">GitHub</a> •
  <a href="#features">Features</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#architecture">Architecture</a>
</p>


## Why Arbiter?

Most AI chat applications lock you into one provider and one model.

**Arbiter treats AI providers as interchangeable backends.** It gives you one workspace where you can connect multiple providers, move between models without losing conversation context, run the same task across several models, and compare their answers with a structured AI Judge.

### The idea

```text
Connect your providers
        ↓
Ask your question
        ↓
Choose a model or let Arbiter recommend one
        ↓
Run one model — or compare several
        ↓
AI Judge evaluates the results
        ↓
Get a reasoned recommendation
```

---

## ✨ Core Features

| Feature | What it does |
|---|---|
| **Multi-provider chat** | Use multiple AI providers through one normalized conversation interface |
| **Model switching** | Switch models mid-conversation without losing context |
| **Multi-model compare** | Send one task to 2–4 models in parallel and view responses side by side |
| **AI Judge** | Scores responses on correctness, relevance, completeness, reasoning, code quality, instruction-following, and clarity |
| **Model recommendation** | Recommends capability-matched models for coding, reasoning, long documents, vision, and other tasks |
| **Provider fallback** | Automatically retries with another authorized provider when a provider fails |
| **Project memory** | Stores structured instructions, decisions, tech stack, preferences, and notes separately from chat history |
| **Secure key vault** | Encrypts provider API keys and never returns decrypted keys to the frontend |
| **Streaming** | Token-by-token SSE streaming with graceful failure handling |
| **Usage tracking** | Records model-run usage and execution metadata for future analytics |

> **AI Judge results are recommendations, not absolute truth.** The goal is to make model selection easier and more transparent.

---

## 🧠 How Arbiter Works

### Standard chat flow

```text
User
 │
 ▼
Frontend
 │
 ▼
API Server
 │
 ├── Authentication / User Management
 │
 ├── Conversation Service
 │
 ├── Context / Memory Service
 │
 ▼
AI Orchestrator
 │
 ├── Task Classification
 ├── Model Selection
 ├── Context Reconstruction
 ├── Credential Resolution
 │
 ▼
LLMGateway (LiteLLM)
 │
 ├── OpenAI
 ├── Anthropic
 ├── Gemini
 ├── DeepSeek
 ├── NVIDIA NIM
 └── Ollama
 │
 ▼
Response
```

### Multi-model comparison

```text
                    ┌── Model A ──┐
                    │             │
User Task → Arbiter ├── Model B ──┼──→ AI Judge → Winner + Scores + Reasoning
                    │             │
                    └── Model C ──┘
```

### Provider-agnostic routing

Arbiter does not hardcode provider names into routing logic.

```text
Provider
   ↓
Model
   ↓
Capabilities
   ↓
User Authorization
   ↓
Routing Decision
   ↓
AI Execution
```

This keeps the orchestration layer independent from individual provider SDKs.

---

## 🏗️ Architecture

```text
Client
  │
  ▼
API Server
  │
  ├── Auth / User Management
  ├── Conversation Service
  ├── Context / Memory Service
  ├── AI Orchestrator
  │      └── LLMGateway (LiteLLM)
  ├── Model Router
  │      └── Task Classification → Selection → Fallback
  ├── Comparison / Judge Service
  └── Credential / Key Vault
  │
  ├───────────────┐
  ▼               ▼
Turso            Redis
(libSQL)         State / Cache / Queue
```

### AI Orchestrator

For every request, Arbiter:

1. Loads conversation history.
2. Loads only relevant project memory.
3. Determines the task type.
4. Selects the requested or recommended model.
5. Builds a provider-neutral request.
6. Resolves the user's encrypted credential.
7. Sends the request through `LLMGateway`.
8. Stores the response with provider/model metadata.
9. Returns the result to the client.

---

## 🔌 Provider Layer

Every provider is accessed through one application-level interface.

```ts
interface AIProvider {
  chat(request: ChatRequest): Promise<ChatResponse>;
  stream(request: ChatRequest): AsyncIterable<ChatChunk>;
  getModels(): Promise<ModelInfo[]>;
  healthCheck(): Promise<boolean>;
}
```

Arbiter uses **LiteLLM** as the unified gateway, with a thin project-specific wrapper for typing and error normalization.

Application code should not depend directly on individual provider SDKs.

---

## 🔁 Automatic Provider Fallback

```text
Requested Model
      │
      ▼
Health Check / Request
      │
 ┌────┴─────┐
 ▼          ▼
Success    Failure
 │          │
 ▼          ▼
Response   Fallback Router
              │
              ▼
       Authorized Model
              │
              ▼
           Response
```

Fallback rules:

- Only authorized providers/models can be selected.
- Arbiter does not silently violate user configuration or privacy settings.
- Every fallback records the original model, failure reason, fallback model, and timestamp.
- Provider health state can be tracked through Redis-backed status flags.

---

## 🧰 Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| LLM Gateway | LiteLLM |
| Database | Turso / libSQL |
| Cache & Queue | Redis |
| Containerization | Docker / Docker Compose |
| Coding Agent | OpenCode |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 18 + Next.js App Router |
| Styling | Tailwind CSS + CSS variables |
| Server State | TanStack Query |
| UI / Session State | Zustand |
| Realtime | Server-Sent Events (SSE) |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| Authentication | JWT access/refresh |
| Icons | Tabler |

---

## 📁 Repository Structure

```text
arbiter/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── auth/
│   │   │   ├── conversations/
│   │   │   ├── memory/
│   │   │   ├── orchestration/
│   │   │   ├── routing/
│   │   │   ├── comparison/
│   │   │   └── credentials/
│   │   ├── providers/
│   │   │   └── llm_gateway.py
│   │   └── middleware/
│   ├── tests/
│   ├── docker-compose.yml
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── app/
│   │   ├── (marketing)/
│   │   ├── login/
│   │   ├── signup/
│   │   └── app/
│   │       ├── chat/[conversationId]/
│   │       ├── compare/[runId]/
│   │       ├── projects/
│   │       ├── projects/[id]/
│   │       ├── keys/
│   │       └── settings/
│   ├── components/
│   ├── lib/
│   ├── styles/
│   │   └── tokens.css
│   └── tests/
│
├── assets/
│   └── arbiter-logo.jpg
│
└── README.md
```

---

## 🖥️ Main Screens

### Landing

The marketing page introduces Arbiter, explains the workflow, and provides entry points into the workspace and documentation.

### Chat Workspace

```text
┌─────────────────────────────────────────────────────────────┐
│ Model Selector                         Recommend             │
├──────────────┬──────────────────────────────────────────────┤
│ Conversations│                                              │
│              │                 Message Thread               │
│ Project A    │                                              │
│  Chat 1      │  User message                                │
│  Chat 2      │                                              │
│              │  Assistant response                           │
│ Project B    │  model: provider/model                       │
│  Chat 3      │                                              │
│              │                                              │
│ + New Chat   │  ┌────────────────────────────────────────┐  │
│              │  │ Ask anything...                  Send │  │
│              │  └────────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────────┘
```

### Compare

Run a task against multiple authorized models and inspect:

- Individual responses
- Latency
- Token usage
- Judge scores
- Winner
- Judge reasoning
- Provider/model failures

### Projects

Projects keep structured memory separate from raw conversation history.

Supported memory categories include:

- Instructions
- Decisions
- Tech stack
- Preferences
- Notes

### API Key Vault

Users connect provider keys through the application.

The frontend receives only a masked confirmation such as:

```text
sk-••••4f2a
```

Decrypted credentials are never returned to the frontend.

---

## 🗺️ Routes

| Route | Purpose |
|---|---|
| `/` | Landing / marketing |
| `/login` | Login |
| `/signup` | Registration |
| `/app` | Redirect to active workspace |
| `/app/chat/:conversationId` | Main chat workspace |
| `/app/compare/:runId` | Multi-model comparison |
| `/app/projects` | Project list |
| `/app/projects/:id` | Project detail |
| `/app/keys` | API key vault |
| `/app/settings` | Account and model preferences |

---

## 🔗 API Overview

### Core route groups

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

### Example requests

```http
POST /api/conversations/:conversationId/messages
{
  "content": "...",
  "modelId": "model_id"
}
```

```http
POST /api/compare
{
  "conversationId": "...",
  "content": "...",
  "modelIds": ["model_a", "model_b", "model_c"]
}
```

```http
POST /api/route/recommend
{
  "content": "Debug this Python algorithm"
}
```

```http
GET /api/providers
GET /api/models
POST /api/keys
DELETE /api/keys/:providerId
```

Project memory:

```http
POST   /api/projects/:projectId/memory
GET    /api/projects/:projectId/memory
DELETE /api/projects/:projectId/memory/:memoryId
```

---

## 🗄️ Data Model

Arbiter uses Turso / libSQL with the following core tables:

```text
users
sessions
providers
models
user_providers
api_credentials
conversations
messages
projects
project_memory
model_runs
comparisons
fallback_events
usage_records
```

Important relationships:

```text
User
 ├── Sessions
 ├── API Credentials
 ├── Projects
 │     └── Project Memory
 └── Conversations
       ├── Messages
       ├── Model Runs
       └── Comparisons
```

---

## 🛡️ Security

Security is a first-class architectural requirement.

- Provider keys are encrypted at rest using envelope encryption.
- Master encryption keys come from environment variables or a secrets manager.
- Decrypted provider keys are never returned to the frontend.
- Credentials are never logged.
- API keys must never appear in conversation messages or Git commits.
- Passwords are hashed with Argon2 or bcrypt.
- Protected resources verify authenticated ownership on every request.
- Request bodies and model/provider identifiers are validated.
- AI endpoints are rate-limited.
- Request and message sizes are capped.
- Metadata is sanitized and validated.
- Production traffic uses HTTPS.
- CORS is restricted to trusted origins.
- Server secrets remain outside the database and source code.
- Internal stack traces and provider credentials are never exposed to clients.

### Key vault rule

> **The key vault must be written and reviewed before other network-facing features ship.**

---

## ⚠️ Error Handling

Arbiter normalizes provider-specific failures into a consistent API format:

```json
{
  "error": {
    "code": "PROVIDER_UNAVAILABLE",
    "message": "The selected AI provider is temporarily unavailable.",
    "requestId": "req_123"
  }
}
```

Supported error categories include:

```text
AUTH_REQUIRED
FORBIDDEN
INVALID_REQUEST
MODEL_NOT_FOUND
PROVIDER_NOT_FOUND
PROVIDER_UNAUTHORIZED
PROVIDER_UNAVAILABLE
MODEL_UNAVAILABLE
RATE_LIMITED
CONTEXT_TOO_LARGE
AI_REQUEST_FAILED
INTERNAL_ERROR
```

This keeps frontend behavior predictable regardless of which provider fails.

---

## 🎨 Design System

Arbiter uses an editorial/documentation-inspired interface:

- Warm cream background
- Serif headings
- Deep teal-green accent
- Minimal borders
- Rounded cards
- Dark code previews
- Light and dark themes
- Sentence-case UI
- Streaming-first interaction model

### Light palette

| Token | Value |
|---|---|
| `--bg-page` | `#F4F1EA` |
| `--surface-card` | `#FFFFFF` |
| `--text-primary` | `#1A1A1A` |
| `--text-secondary` | `#555555` |
| `--text-muted` | `#888888` |
| `--accent` | `#0F6E56` |
| `--accent-soft` | `#E1F5EE` |
| `--border` | `#E4E1D8` |
| `--code-bg` | `#1E1E1E` |
| `--code-text` | `#9FE1CB` |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd arbiter
```

### 2. Start the backend

```bash
cd backend
cp .env.example .env
```

Configure the required environment values:

```text
Turso URL
Turso token
Redis URL
JWT secret
Encryption master key
```

Then start the backend:

```bash
docker compose up --build
```

### 3. Start the frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open the local application in your browser.

### 4. Connect AI providers

After creating an account, add provider API keys through:

```text
/app/keys
```

> **Never place provider API keys directly in `.env` for application use when the key-vault flow is available.**

---

## 🧪 Testing

The project is designed around testable service boundaries.

Recommended validation areas:

```text
Authentication
       ↓
Credential encryption
       ↓
Conversation CRUD
       ↓
Model routing
       ↓
Provider execution
       ↓
Streaming
       ↓
Fallback
       ↓
Multi-model comparison
       ↓
AI Judge
       ↓
Project memory
```

Before considering a release complete, verify both backend and frontend flows end-to-end.

---

## 🛣️ Roadmap

### Phase 1 — Foundation

- JWT authentication
- Signup / login / refresh / logout
- Encrypted provider key vault
- Core database schema
- Turso / Docker setup
- Frontend authentication
- Key vault UI
- Design tokens and theme

### Phase 2 — Core Chat

- LiteLLM integration
- Conversation engine
- Context preservation during model switching
- SSE/WebSocket streaming
- Provider health monitoring
- Automatic fallback

### Phase 3 — Compare, Judge, Recommend & Memory

- Multi-model fan-out
- AI Judge
- Model recommendation
- Project memory
- Comparison history
- Judge scores and reasoning

### Phase 4 — Post-MVP

- Advanced routing
- Usage analytics
- Cost-aware routing
- Provider health dashboard
- RAG-based memory
- Memory search UI

---

## 🎯 Design Principles

### Backend

**Provider-agnostic · Modular · Secure · Testable · Observable · Extensible · Resilient**

New providers should be addable without rewriting the core orchestration layer.

### Frontend

**Provider-agnostic UI · Streaming-first · Secure-by-default · Route-driven**

The frontend should never render key material and every important screen should correspond to a real backend capability.

---

## 🤝 Contributing

Contributions, bug reports, and architecture discussions are welcome.

Before submitting a change:

1. Keep provider-specific logic inside the provider/gateway layer.
2. Preserve resource ownership checks.
3. Do not expose credentials.
4. Add or update tests for changed behavior.
5. Keep API errors normalized.
6. Avoid coupling UI logic directly to provider implementations.

---

## 📄 License

Add the project's chosen license here before publishing the repository.

---

<p align="center">
  <strong>Arbiter</strong><br />
  One workspace. Multiple models. Better decisions.
</p>
