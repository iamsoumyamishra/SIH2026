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
| Model layer | `✓` |
| Multimodal / OCR | `✓` |
| RAG | `✓` (qdrant verified end-to-end via postgresql+qdrant API) |
| Tools + Artifacts | `✓` |
| Sandbox | `✓` (live-docker validation done) |
| Frontend (Next.js) | `✓` |
| Security / Auth | `✓` (JWT + demo user) |
| Sovereignty | `✓` (audit logs + real counters across full-stack demo) |
| Full production-like stack (compose) | `✓` (postgres/qdrant/minio up; API+web validated) |
| Git tracking | `✓` (initial commit done) |

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
- [x] Verification works — `✓` (`approval_note.docx` verified live; task-6 run logged `model_calls=2`)
- [x] Retry/replanning is bounded — `✓` (`MAX_AGENT_ITERATIONS=12`)

### Multimodal
- [x] PDF upload works — `✓` (pypdfium2)
- [x] Scanned PDF OCR works — `✓` (RapidOCR live end-to-end: scanned-only PDF → OCR → vision-structured findings → DOCX, verified)
- [x] Image understanding works — `✓` (vision model `qwen2.5vl:3b` structures checklist tables straight from the page image)

### RAG
- [x] Documents can be ingested — `✓`
- [x] Local embeddings work — `✓` (nomic-embed-text)
- [ ] Qdrant retrieval works — `✓` (sop-001→2 chunks indexed; search returns page/section citations)
- [x] Sources are displayed — `✓` (UI)

### Tools
- [x] File tools work — `✓`
- [x] Calculator works — `✓`
- [x] Python works — `✓` (via sandbox)
- [x] DOCX generation works — `✓`

### Sandbox
- [x] Docker execution works — `✓`
- [x] Network is disabled — `✓` (`network_mode=none`)
- [x] Filesystem is isolated — `✓` (`/work` mounts only)
- [x] Resources are limited — `✓` (cpu/mem/pids/timeout)
- [ ] Validated against a live container — `✓` (exec+output, network-denied, OOM 137, 30s timeout, file mount)

### Security
- [x] Authentication works — `✓` (JWT, `admin/admin`)
- [x] Permissions work — `✓`
- [x] Audit logging works — `✓`
- [x] Secrets are protected — `✓` (never logged; `.env` gitignored)

### Sovereignty
- [x] No external AI calls — `✓` (all local)
- [x] No cloud uploads — `✓`
- [x] Local inference works — `✓` (embeddings + all role models verified via live agent run)
- [ ] Network status is demonstrable — `✓` (network-denied sandbox proved live; full-stack demo done)

### Demo
- [x] Inspection report → approval note — `✓` (live: `approval_note.docx`, passed)
- [ ] Coding → sandbox → tests → verification — `✓` (live: t-12 `factorial` code+tests executed in sandbox, `TESTS EXECUTED OK`, `model_calls=1`; honest status on burnout)
- [x] Multimodal document analysis — `✓` (live: scanned PDF → RapidOCR → `qwen2.5vl:3b` structured findings → verified DOCX; `model_calls=2`)
- [x] Real DOCX artifact — `✓`
- [x] Agent progress visible in UI — `✓` (SSE timeline)

---

## Development Phases — Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (Next.js, FastAPI, Postgres, Ollama, Compose) | `✓` (full-stack on postgres+compose validated) |
| 2 | Model layer (Provider, OllamaProvider, Registry, Router) | `✓` |
| 3 | Agent (Planner, Executor, State, ToolRegistry, Verifier) | `✓` |
| 4 | Documents (PDF, OCR, images) | `✓` (RapidOCR live, vision-structure live) |
| 5 | RAG (embeddings, Qdrant, ingest, retrieval, citations) | `✓` |
| 6 | Tools (filesystem, calculator, python, DOCX) | `✓` |
| 7 | Sandbox (docker, network isolation, limits) | `✓` (live validation done) |
| 8 | UI (workbench, timeline, sources, artifacts, models) | `✓` |
| 9 | Sovereignty (audit, network monitoring, security dashboard) | `✓` |
| 10 | Demo (inspection→approval, coding→verified, multimodal) | `✓` |

---

## Open Items (actionable)

> **Resolved 2026-08-30 (full-stack):** All three open items below closed.
> 1. **Compose stack up** — `saw-postgres` (healthy) / `saw-qdrant` (6333) / `saw-minio` (9000,9001) running from `docker-compose.yml` (name `sovereign-ai-workbench`). postgres created all 10 tables.
> 2. **Full-stack config** — API flipped to `DATABASE_BACKEND=postgresql` + `RAG_BACKEND=qdrant` + Postgres (verified via separate dev-backend API kept for warm-pooling). End-to-end live: inspection PDF (t-2) → `completed`, `model_calls=2`, DOCX with 5 findings + `Maintenance SOP §maintenance` citations from qdrant, full rows in postgres (users/tasks/agent_runs/agent_steps/artifacts/audit_logs). Qdrant point-ID fix (`_as_point_id` uuid5) for qdrant ≥1.9.
> 3. **Sandbox live validation** — docker-py 7 fixes (pass `network_mode`/`nano_cpus`/`mem_limit`/`pids_limit` directly; no `host_config`/`cpus`; no auto-remove). Live: exec+output ✓, network denied (exit 1) ✓, OOM 512MB→137 ✓, 30s timeout ✓, file mount ✓. Coding demo (t-12): `factorial` code+tests → sandbox exec + `run_tests` (real asserts; unittest + `test_*` + no-tests→exit 2), `TESTS EXECUTED OK`, artifacts `code`/`PASSED`, `model_calls=1`.
> **Also fixed:** 3B coder persona chatter → retry parse up to 3 draws + no persona system prompt + `temperature=0.1`; code-task failure honesty — iteration burnout now marks task/run FAILED (was masked as COMPLETED).

> **Resolved 2026-08-30:** mypy is wired into turbo (`@sovereign/api` `typecheck` script, `sqlalchemy.ext.mypy.plugin`) and passes clean (`Success: no issues found in 86 source files`). Done with the OCR/`_parse_findings`/vision work it covered.

> **Resolved 2026-08-30:** API model registration + live agent run now uses real models —
> `/api/models` reports all roles `available`; task-6 inspection→approval run selected
> `qwen2.5:3b`, logged `model_calls=2` (real inference wired into `analyze_findings` /
> `generate_code` handlers in `services/task_service.py` via `ModelProvider`), verified DOCX.

---

## Known machine / environment constraints

- **GPU:** NVIDIA RTX 4050 Laptop, ~4GB VRAM → use small models (3B) not 7B.
- **Smart App Control:** was blocking unsigned `turbo.exe`; user disabled it → turbo works now.
- **Docker Desktop:** engine running (`29.7.2`); compose services postgres/qdrant/minio up (see resolution above).
- **Ollama:** running at `http://localhost:11434`; `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5vl:3b`, `nomic-embed-text` installed.
- **WSL quirks:** Windows interop disabled → Docker Desktop credsStore fails; use `DOCKER_CONFIG=/tmp/opencode/docker-config` (config `{}`) for pulls/compose. pydantic-settings `env_file=".env"` is CWD-relative → launch with explicit env (postgres creds in repo `.env`, CRLF; source via `tr -d '\r'`).

---

## Changelog

- **2026-08-29** — Initial tracker; captured current state, pnpm/turbo migration complete, OCR switch to RapidOCR approved (PaddleOCR impractical on this Windows box), small-model set agreed for 4GB VRAM, mypy to be wired in. `apps/web/Dockerfile` found to be missing (compose web broken).
- **2026-08-29 (B1/B2)** — Models pulled: general/coding/vision/embedding all installed and verified inference (vision read MC-1042 from a rendered page). OCR switched PaddleOCR → RapidOCR (`multimodal/ocr.py`); verified OCR extraction on rendered PDF page.
- **2026-08-30** — Docs milestone: `PRD.md` and `PPT_CONTENT.md` (incl. full architecture/workflow appendix) authored; `AGENTS.md` minimized to ~500 words (idea, architecture, tech stack, docs-sync rule). `.gitignore` hardened (`.turbo/`, `*.log`, `*.err`, `graphify-out/`); junk removed from index; **initial git commit created** (`8601541`). `apps/web/Dockerfile` confirmed present.
- **2026-08-30 (runtime)** — Open item #1 → **verified**: real (non-deterministic) model inference wired into the agent handler layer (`services/task_service.py`: `_generate` → `ModelProvider.generate`, `_model_analysis`, `_model_code`; LLM-fallback keeps runs resilient). Live task-6 (inspection PDF → approval note) reports `model_calls=2`, `selected_models=["qwen2.5:3b"]`, DOCX verified `passed` (`file_exists`, `sections_exist`). 42/42 pytest green; ruff clean on touched file.
- **2026-08-30 (multimodal)** — **Scanned-PDF OCR milestone**: `rapidocr-onnxruntime` installed on runtime env. Image-only (no text layer) scanned PDF built from `inspection_report.pdf` and run live (task-9): pipeline detects `scanned` → local RapidOCR → `qwen2.5vl:3b` reads the rendered page and structures the checklist (JSON-or-markdown-table extraction added to `task_service.py`; deterministic `_parse_findings` extended to OCR split-layout as fallback) → real analysis (`model_calls=2`) → `approval_note.docx` verified `passed` with all 5 findings named correctly. `test_pipeline.py` updated for the now-installed OCR engine.
- **2026-08-30 (mypy)** — Open item #4 → **done**: mypy wired into turbo (`"typecheck": ".venv\\Scripts\\python.exe -m mypy ."`, `apps/api/package.json`; `sqlalchemy.ext.mypy.plugin` enabled). `db/models.py` migrated `Column` → `Mapped`/`mapped_column` (SQLAlchemy 2.0); fixed nits mypy surfaced (helper guards, operator typing, provider stream typing, qdrant version-compat). Result: `mypy .` → `Success: no issues found in 86 source files`; `ruff check .` clean after `ruff format`. Post-rewrite live run (task-10) re-verified: `model_calls=2`, DOCX `passed`.
- **2026-08-30 (frontend)** — Node v24.20.0 LTS installed in WSL (`~/.local/opt/node-v24.20.0-linux-x64`, PATH in `.bashrc`) + pnpm 11.21.0. `@sovereign/web`: `tsc --noEmit` ✓ and `next build` ✓ (10 routes, all static). NOTE: web has no `lint` script (eslint not wired); api `lint`/`typecheck` run on the host venv (validated here via `python3 -m ruff/mypy/pytest`). First WSL `pnpm install` purged the Windows-built `node_modules` (lockfile unchanged) — re-run `pnpm install` on the host before using turbo there.
- **2026-08-30 (ports)** — **API dev port moved 8000 → 8787** to end a recurring WSL2↔Windows localhost conflict: a WSL-side API on 8000 forwards into Windows (WSL2 NAT relay), so the Windows `pnpm dev` uvicorn kept hitting `WinError 10048` (also transient relay lingering after the WSL listener died). Canonical port is now 8787 everywhere (`config/settings.py` `api_port`, `package.json` dev script, `web/lib/api.ts` + `next.config.js` defaults, `.env.example` + repo `.env`, `docker-compose.yml` host mapping `8787:8000`, README). Windows dev API binds 8787; WSL validation API stays on 8001; in-container API remains 8000. Override stays `NEXT_PUBLIC_API_URL` for the web.
- **2026-08-30 (full-stack)** — **Sandbox, compose, and flip all verified live** (open items 1–3 closed). `docker-compose.yml` up: postgres/qdrant/minio (name `sovereign-ai-workbench`; postgres all 10 tables). `apps/api/sandbox/docker.py` made docker-py 7.2-compatible (run kwargs directly, no auto-remove) and validated: exec, network-denied, OOM 137, 30s timeout, file mount. `apps/api/rag/qdrant.py` `_as_point_id` (uuid5) for qdrant ≥1.9. API flipped to postgresql+qdrant (t-2 inspection→DOCX `completed`, 5 findings + `§maintenance` citations, full postgres persistence). **Coding loop made honest & convergent**: `_model_code` returns `(code, tests)` (`<SOLUTION>`/`<TESTS>` + fenced fallback, retry ≤3 draws, no persona system, `temperature=0.1`), `_code_feedback` feeds prior sandbox errors back (t-11: `model_calls` 12→), `RunTestsTool` runs `test_*` + unittest + no-tests→exit 2, iteration burnout now FAILS loudly instead of masking COMPLETED. t-12 code demo: `model_calls=1`, tests genuinely executed (`TESTS EXECUTED OK`), artifacts `code`/`PASSED`. Full sweep green: ruff ✓, mypy 90 files ✓, pytest 42/42 ✓. `sandbox/_mounts/` gitignored.

