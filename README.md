# Sovereign AI Workbench

A **Sovereign On-Premise Agentic AI Workbench** for confidential industrial and
government work. It provides a Claude/Codex-like experience while guaranteeing:

> **No user data, documents, prompts, generated artifacts, or model requests
leave the local infrastructure.**

Everything runs on-premise using **Ollama** and **open-weight models**.

---

## Architecture

```
                         USER
                           │
                           ▼
                    NEXT.JS WORKBENCH
                           │
                           ▼
                     FASTAPI API
                           │
                           ▼
                  AGENT ORCHESTRATOR
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
           PLANNER     MODEL ROUTER   TOOLS
              │            │            │
              │       ┌────┼────┐       │
              │       ▼    ▼    ▼       │
              │     LLM  CODE VISION     │
              │       │    │    │        │
              │       └────┼────┘        │
              │            │             │
              └────────────┼─────────────┘
                           │
                    LOCAL KNOWLEDGE
                           │
                         QDRANT
                           │
                    LOCAL DOCUMENTS
                           │
                           ▼
                       VERIFIER
                           │
                           ▼
                     ARTIFACTS
```

Key principles (see `AGENTS.md` for the full contract):

- **Local-first**: all inference, OCR, embeddings, and retrieval are local.
- **Model-agnostic**: the agent never calls Ollama directly. It goes through
  `ModelRouter → ModelProvider → OllamaProvider`. A future `VLLMProvider` can
  drop in without changing the agent.
- **Tool isolation**: the LLM never gets unrestricted OS/filesystem access.
  All operations go through a permission-checked `ToolRegistry`.
- **Explicit agent state** with a bounded execution loop
  (`MAX_AGENT_ITERATIONS`, default 12).
- **Auditable**: every run records an audit trail (task, model, tools,
  documents, artifacts, verification) — never document contents or secrets.
- **No external calls**: no cloud AI, OCR, embeddings, or vector databases.

---

## Repository Structure

```
sovereign-ai-workbench/
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pnpm-workspace.yaml   # monorepo apps + pnpm config (hoisted linker)
├── turbo.json            # turbo task pipeline (build/dev/lint/test/typecheck)
├── package.json          # root scripts → turbo
├── apps/
│   ├── web/              # Next.js frontend (@sovereign/web)
│   └── api/              # FastAPI backend (@sovereign/api)
├── docs/
│   └── adr/              # Architecture Decision Records
├── infrastructure/     # service config (ollama, postgres, qdrant, minio, sandbox)
├── sample_documents/   # demo input documents
├── datasets/           # sample knowledge-base data
├── tests/              # unit + integration tests
└── scripts/            # helper scripts (model pulls, setup)
```

---

## Prerequisites

- **Docker** + Docker Compose (for full infrastructure and the code sandbox)
- **Ollama** (local inference) with at least one chat model and one embedding
  model, *or* the Ollama Docker service defined in `docker-compose.yml`
- **Python 3.11+** (development: installs `apps/api` dependencies)
- **Node.js 20+** and **pnpm** (development: frontend; `corepack enable pnpm`
  or install pnpm directly)

---

## Environment Setup

```bash
cp .env.example .env
# edit .env — at minimum set a strong JWT_SECRET
```

---

## Ollama Setup — Pull Models

The system works with whatever compatible Ollama models you have installed.
Model names are configured via environment variables
(`OLLAMA_GENERAL_MODEL`, `OLLAMA_CODING_MODEL`, etc.) and the registry
(`apps/api/models/registry.yaml`).

Pull models explicitly (the system will **not** download them on its own):

```bash
# Windows (PowerShell)
.\scripts\pull_models.ps1

# Linux/macOS
./scripts/pull_models.sh
```

Example model set (adjust to your hardware):

| Role             | Example model        |
|------------------|----------------------|
| General/reasoning| `qwen2.5:7b`         |
| Coding           | `qwen2.5-coder:7b`   |
| Vision           | `llava:7b`           |
| Embedding        | `nomic-embed-text`   |

The embedding model (`nomic-embed-text`) is used for RAG and is already
sufficient for local knowledge retrieval.

---

## Running Locally (Development)

The repository uses **pnpm + Turborepo** for monorepo orchestration
(`apps/api` FastAPI backend + `apps/web` Next.js frontend). After the one-time
backend setup, a single command starts the whole stack.

### 1. One-time setup

Install dependencies and prepare the Python backend:

```bash
pnpm install                # installs JS/tooling for all apps

cd apps/api
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

Dev defaults: `DATABASE_BACKEND=sqlite` and `RAG_BACKEND=local`, so the API
runs without requiring Postgres/Qdrant containers.

### 2. Run everything (recommended)

```bash
pnpm dev        # runs FastAPI (:8787) and Next.js (:3000) together via turbo
```

### 3. Run a single app

```bash
pnpm dev:web    # frontend only
pnpm dev:api    # backend only
```

Open http://localhost:3000 — the API is expected at http://localhost:8787
(override with `NEXT_PUBLIC_API_URL`).

### 4. Build / check

```bash
pnpm build       # production builds (turbo)
pnpm lint        # API ruff
pnpm typecheck   # web tsc --noEmit
pnpm test        # API pytest
```

Demo login: **admin / admin** (configurable via `DEMO_USERNAME`/`DEMO_PASSWORD`).

Frontend pages (App Router, `apps/web/app`):

| Route | Purpose |
|-------|---------|
| `/login` | JWT sign-in |
| `/` | Workspace — task submission + **live agent timeline** (SSE) with model/tools/artifacts |
| `/documents` | Upload & list local documents |
| `/knowledge` | Local RAG ingest + semantic search |
| `/models` | Router-visible local models + availability |
| `/artifacts` | Generated files with verification status + download |
| `/audit` | Non-sensitive audit trail |
| `/sovereignty` | Live sovereignty monitor (internet probe, external-call counters) |

---

## Running with Docker Compose

```bash
docker compose up --build
```

This starts the API, web, Ollama, PostgreSQL, Qdrant, and MinIO. Set
`DATABASE_BACKEND=postgresql` and `RAG_BACKEND=qdrant` in `.env` for the
full-stack configuration.

---

## Running Tests

```bash
pnpm test        # API pytest (turbo)
pnpm lint        # API ruff (turbo)
pnpm typecheck   # web tsc --noEmit (turbo)
```

Or run a single app's task directly:

```bash
pnpm --filter @sovereign/api test
pnpm --filter @sovereign/web typecheck
```

---

## Demo Workflows

### Demo 1 — Inspection → Approval Note (primary)

Upload a scanned inspection report → OCR → RAG over the maintenance SOP →
reasoning → approval-note DOCX → verification.

```text
sample_documents/inspection_report.pdf
        ↓ OCR → findings → RAG(SOP) → analyze → approval_note.docx → verify
```

### Demo 2 — Coding

"Write a Python program that calculates X and test it." → coding model →
Docker sandbox → execute → test → verified code.

### Demo 3 — Multimodal

Image / scanned engineering document → OCR / vision → structured understanding
→ reasoning → response.

---

## Sovereignty Dashboard

`GET /api/system/sovereignty` reports real counters:

- Internet: `BLOCKED` / `CHECK`
- External AI requests: `0`
- Cloud uploads: `0`
- Local model requests: `N`
- Tool executions: `N`

Counters come from actual application activity and a live network check — they
are **not fabricated**.

---

## API Overview

```
POST /api/auth/login
POST /api/tasks
GET  /api/tasks/{id}
POST /api/documents/upload
GET  /api/documents
POST /api/knowledge/ingest
POST /api/knowledge/search
GET  /api/models
POST /api/models/test
GET  /api/agents/runs/{id}
GET  /api/artifacts/{id}
GET  /api/system/health
GET  /api/system/sovereignty
GET  /api/audit
```

Live agent progress is streamed via Server-Sent Events.

---

## Security & Sovereignty Notes

- Code executes only inside the Docker sandbox with **no network**, isolated
  filesystem, no secrets/host access, and enforced timeout/CPU/memory limits.
- The agent only reads/writes inside its per-task workspace; path traversal is
  blocked and every path is validated.
- Never log document contents, passwords, API keys, or secrets.
- No cloud APIs, no silent cloud fallback, no auto-downloading of large models.

---

## Troubleshooting

- **"Docker unavailable"** in the sandbox/tools → start Docker Desktop.
- **"Model unavailable"** → pull models (`scripts/pull_models.*`) and verify
  with `GET /api/models`.
- **RAG falls back to local store** → set `RAG_BACKEND=qdrant` and start the
  Qdrant container.
- **OCR unavailable** → install `paddleocr` (heavy) or check the logs for the
  specific failure; a clear message is surfaced rather than a silent cloud call.

---

## Architecture Decision Records

See [docs/adr/](docs/adr/) for major architectural decisions as the project
evolves.
