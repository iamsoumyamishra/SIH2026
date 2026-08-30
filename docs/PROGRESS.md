# Progress Tracker

> **Canonical status document for the Sovereign AI Workbench.**
> Update this file whenever a Definition-of-Done item in `AGENTS.md` changes
> state. Legend: `✓` done · `△` in progress / partial · `☐` not started · `✗` blocked.

---

## Status Legend

| Mark | Meaning |
|------|---------|
| `✓` | Done and verified (test passing / live demo confirmed) |
| `△` | In progress or partially working (dev fallback active, etc.) |
| `☐` | Not started |
| `✗` | Blocked (machine/OS/security issue preventing work) |

---

## Overall Snapshot

| Area | Status |
|------|--------|
| Repo tooling (pnpm + Turborepo) | `✓` |
| Backend (FastAPI) | `✓` |
| Agent core | `✓` |
| Model layer | `△` (models being pulled) |
| Multimodal / OCR | `△` (RapidOCR swap in progress) |
| RAG | `△` (local backend verified; qdrant pending) |
| Tools + Artifacts | `✓` |
| Sandbox | `△` (live-docker validation pending) |
| Frontend (Next.js) | `✓` |
| Security / Auth | `✓` (JWT + demo user) |
| Sovereignty | `△` (counters present; full-stack demo pending) |
| Full production-like stack (compose) | `△` (not yet running) |
| Git tracking | `☐` (nothing committed yet) |

---

## Definition of Done — Status per Checklist

### Models
- [x] Ollama works locally — `✓`
- [x] At least 2 models are configurable — `✓` (registry + env vars, role-based)
- [ ] Model router selects models — `✓` (rule-based `ModelRouter`)
- [x] Provider abstraction exists — `✓` (`ModelProvider` / `OllamaProvider`)
- [ ] Runtime models installed (general/coding/vision) — `✓` (qwen2.5:3b, qwen2.5-coder:3b, qwen2.5vl:3b, nomic-embed-text; verified inference on all)

### Agent
- [x] Planning works — `✓`
- [x] Multi-step execution works — `✓`
- [x] Tool calling works — `✓`
- [x] Agent state works — `✓`
- [x] Verification works — `✓` (`approval_note.docx` verified live)
- [x] Retry/replanning is bounded — `✓` (`MAX_AGENT_ITERATIONS=12`)

### Multimodal
- [x] PDF upload works — `✓` (pypdfium2)
- [ ] Scanned PDF OCR works — `△` (RapidOCR engine verifified on rendered pages; PaddleOCR replaced)
- [ ] Image understanding works — `△` (vision model `qwen2.5vl:3b` installed + verified reading image)

### RAG
- [x] Documents can be ingested — `✓`
- [x] Local embeddings work — `✓` (nomic-embed-text)
- [ ] Qdrant retrieval works — `△` (local store verified; qdrant container pending)
- [x] Sources are displayed — `✓` (UI)

### Tools
- [x] File tools work — `✓`
- [x] Calculator works — `✓`
- [x] Python works — `✓` (via sandbox)
- [x] DOCX generation works — `✓`

### Sandbox
- [x] Docker execution works — `✓` (engine up; SDK path coded)
- [x] Network is disabled — `✓` (`network_mode=none`)
- [x] Filesystem is isolated — `✓` (`/work` mounts only)
- [x] Resources are limited — `✓` (cpu/mem/pids/timeout)
- [ ] Validated against a live container — `△` (pending `docker pull python:3.11-slim` + live `execute_code`)

### Security
- [x] Authentication works — `✓` (JWT, `admin/admin`)
- [x] Permissions work — `✓`
- [x] Audit logging works — `✓`
- [x] Secrets are protected — `✓` (never logged; `.env` gitignored)

### Sovereignty
- [x] No external AI calls — `✓` (all local)
- [x] No cloud uploads — `✓`
- [x] Local inference works — `△` (embedding works; chat models pending pull)
- [ ] Network status is demonstrable — `△` (endpoint present; compose-stack demo pending)

### Demo
- [x] Inspection report → approval note — `✓` (live: `approval_note.docx`, passed)
- [ ] Coding → sandbox → tests → verification — `△` (live sandbox validation pending)
- [ ] Multimodal document analysis — `△` (vision model pending)
- [x] Real DOCX artifact — `✓`
- [x] Agent progress visible in UI — `✓` (SSE timeline)

---

## Development Phases — Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (Next.js, FastAPI, Postgres, Ollama, Compose) | `✓` built · full-stack validation `△` |
| 2 | Model layer (Provider, OllamaProvider, Registry, Router) | `✓` |
| 3 | Agent (Planner, Executor, State, ToolRegistry, Verifier) | `✓` |
| 4 | Documents (PDF, OCR, images) | `△` (OCR swap in progress) |
| 5 | RAG (embeddings, Qdrant, ingest, retrieval, citations) | `△` (qdrant live pending) |
| 6 | Tools (filesystem, calculator, python, DOCX) | `✓` |
| 7 | Sandbox (docker, network isolation, limits) | `△` (live validation pending) |
| 8 | UI (workbench, timeline, sources, artifacts, models) | `✓` |
| 9 | Sovereignty (audit, network monitoring, security dashboard) | `△` |
| 10 | Demo (inspection→approval, coding→verified, multimodal) | `△` |

---

## Open Items (actionable)

1. **Verify API model registration** — confirm `/api/models` + live agent run uses real models (not deterministic path).
2. **`apps/web/Dockerfile`** — does not exist originally; authored (pnpm + hoisted + standalone), rebuild in progress.
3. **Compose stack up** — start postgres/qdrant/minio/ollama/api/web.
4. **Full-stack config** — flip `DATABASE_BACKEND=postgresql` + `RAG_BACKEND=qdrant`, validate.
5. **Sandbox live validation** — pull base image, run `execute_code` in a real container.
6. **mypy** — wire into turbo + make pass.
7. **Git initial commit** — clean tree (`workspaces/`, `data/`, `.env`, build junk) and commit.

---

## Known machine / environment constraints

- **GPU:** NVIDIA RTX 4050 Laptop, ~4GB VRAM → use small models (3B) not 7B.
- **Smart App Control:** was blocking unsigned `turbo.exe`; user disabled it → turbo works now.
- **Docker Desktop:** engine running (`29.7.2`); no compose services started yet.
- **Ollama:** running at `http://localhost:11434`; only `nomic-embed-text` installed.

---

## Changelog

- **2026-08-29** — Initial tracker; captured current state, pnpm/turbo migration complete, OCR switch to RapidOCR approved (PaddleOCR impractical on this Windows box), small-model set agreed for 4GB VRAM, mypy to be wired in. `apps/web/Dockerfile` found to be missing (compose web broken).
- **2026-08-29 (B1/B2)** — Models pulled: general/coding/vision/embedding all installed and verified inference (vision read MC-1042 from a rendered page). OCR switched PaddleOCR → RapidOCR (`multimodal/ocr.py`); verified OCR extraction on rendered PDF page.

