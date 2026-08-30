# Product Requirements Document (PRD)

## Sovereign On-Premise Agentic AI Workbench

| Field | Value |
|-------|-------|
| **Project** | Sovereign On-Premise Agentic AI Workbench |
| **Hackathon** | Smart India Hackathon (SIH) 2026 |
| **Problem Statement** | PS 26117 — MRPL (Mangalore Refinery and Petrochemicals Limited) |
| **Document version** | 0.1.0 |
| **Date** | 2026-08-30 |
| **Status** | Target state (planned); in-flight items flagged per `docs/PROGRESS.md` |
| **Companion docs** | `AGENTS.md` (engineering contract), README.md, `docs/adr/ADR-001..005`, `docs/PROGRESS.md` |

---

## 1. Background

MRPL operates critical refining and petrochemical infrastructure. Much of its
routine work is **confidential**: maintenance and inspection reports, SOPs,
engineering drawings (P&IDs), plant records, and approval notes with commercial
and operational sensitivity.

Industrial teams increasingly want AI assistance — explain documents, extract
findings, search procedure manuals, generate draft reports, and even request
working code. However, mainstream AI products route prompts, files, and
inference through **cloud services**. For a refinery operator that is
unacceptable:

- Confidential plant data would leave organization infrastructure.
- Cloud OCR / embedding / inference breaks data-governance and security policy.
- Offline plants and control networks cannot depend on internet access.

The requirement is therefore to build a **sovereign, on-premise AI workbench**:
full agentic capability using local, open-weight models, with a guarantee that
no prompt, document, artifact, or inference request ever leaves the
organization's infrastructure.

---

## 2. Problem Statement

> Build a self-hosted, air-gapped AI workbench for confidential industrial work
> using open-weight multimodal models. (PS 26117, MRPL)

### 2.1 Pain points

1. **Confidentiality** — plant data (inspection findings, drawings, SOPs)
   cannot be transmitted to external AI services.
2. **Data governance** — no cloud OCR, cloud embeddings, or cloud LLMs is
   permissible; even a "silent fallback" to cloud is a violation.
3. **Verifiability** — AI output (reports, code) must be checked before use;
   generated documents must be real files, verified against required content.
4. **Explainability / audit** — every AI action (model, tools, documents,
   artifacts) must be traceable for compliance.
5. **Offline operation** — capability must exist even with no internet access to
   the outside world.
6. **Heterogeneous work** — the same system must handle reports, scanned
   documents, engineering drawings, knowledge search, and coding.

### 2.2 Why not just "use a chatbot"?

A chatbot answers a question. The target use cases require **multi-step
execution**: read a scanned report → OCR it → search the maintenance SOP →
reason over findings → generate an approval-note DOCX → verify it. That
requires an **agent** with planning, tool routing, local retrieval, artifact
generation, and verification — not a single-turn chat.

---

## 3. Vision

One sentence:

> The user says **"do this task"** and the system automatically determines what
> must be done, which local model to use, which documents/tools are required,
> how to execute and verify the work, and what artifact to produce — all
> **on-premise**.

The experience should feel like a professional enterprise application
(Claude + Codex + document-analysis workspace), not a toy chatbot:
live execution timeline, model identity, sources shown, downloadable verified
artifacts, and a sovereignty dashboard proving nothing left the box.

---

## 4. Goals

| # | Goal |
|---|------|
| G1 | **Sovereignty** — zero external AI calls, zero cloud uploads at runtime. |
| G2 | **Local inference** — all generation, embeddings, OCR, and retrieval run on local infrastructure via Ollama. |
| G3 | **Agentic multi-step execution** — plan → route → execute → verify within a bounded loop. |
| G4 | **Multimodal input** — PDF (digital and scanned), images, DOCX, XLSX, TXT. |
| G5 | **Local RAG** — organizational knowledge searchable with citations (document, page, section). |
| G6 | **Real, verified artifacts** — DOCX/XLSX/PPTX/PDF files, re-opened and checked before delivery. |
| G7 | **Safe code execution** — LLM-generated code runs only in an isolated, networkless Docker sandbox. |
| G8 | **Auditable & observable** — non-sensitive audit trail + live sovereignty monitor. |

## 5. Non-Goals (explicitly out of scope for MVP)

Per `AGENTS.md` §31 and the architecture rules:

- No Kubernetes, Kafka, or complex distributed systems.
- No ML-based model routing (router is deterministic/rule-based).
- No agent swarms or complex event buses.
- No unnecessary microservices (modular monolith).
- No cloud infrastructure or silent cloud fallback.
- No auto-download of large models without explicit operator configuration.
- No multi-tenant/multi-org isolation analytics beyond MVP auth.
- No host execution of LLM-generated code (ever).

---

## 6. Target Users & Personas

| Persona | Role | Primary work in the workbench |
|---------|------|-------------------------------|
| **Inspection Engineer** | Plant inspection & maintenance | Upload scanned inspection reports; get findings extraction against SOPs; approve/reject with generated approval note. |
| **Process / Reliability Engineer** | Equipment & safety analysis | Search procedural manuals, analyze multimodal documents, generate engineering notes. |
| **Reviewer / Approver** | Sign-off authority | Review generated artifacts (DOCX), verify content and sources before approval. |
| **Developer / Analyst** | Ad-hoc computation | Request small scripts; receive tested, sandbox-verified code, not raw snippets. |
| **System Admin / Operator** | Deployment & compliance | Manage models, monitor the sovereignty dashboard, review audit trail. |

---

## 7. Scope — MVP

### 7.1 In scope (aligns with AGENTS.md development phases)

1. **Foundation** — Next.js web app, FastAPI backend, PostgreSQL, Ollama,
   Docker Compose.
2. **Model layer** — `ModelProvider` abstraction, `OllamaProvider`,
   `ModelRegistry`, rule-based `ModelRouter`.
3. **Agent** — Planner, Executor, explicit state machine, ToolRegistry,
   Verifier, bounded retries (`MAX_AGENT_ITERATIONS=12`).
4. **Documents** — PDF text extraction, scanned-PDF OCR (local RapidOCR),
   image handling.
5. **RAG** — local embeddings, Qdrant (with local dev fallback), ingestion,
   retrieval, citations.
6. **Tools** — permission-checked filesystem, calculator, document extraction,
   knowledge search/ingest, python code execution, DOCX/XLSX/PPTX/PDF
   generation.
7. **Sandbox** — Docker execution, network isolation, CPU/mem/pids/time limits.
8. **UI** — workspace with agent timeline, sources, artifacts, model
   information, documents, knowledge, models, audit, sovereignty pages.
9. **Sovereignty** — audit logging, network monitoring, security dashboard.
10. **Demo workflows** — inspection→approval note, coding→verified code,
    multimodal document analysis.

### 7.2 Out of scope (MVP)

Auto-downloading models, ML routing, vision-only fine-tuning, mobile apps,
cloud sync, horizontal scaling.

---

## 8. User Stories

| ID | Story |
|----|-------|
| US-1 | As an **inspection engineer**, I upload a scanned inspection report and request *"generate an approval note for findings listed"*, so that the system OCRs it, searches the maintenance SOP, drafts the note, and returns a verified `approval_note.docx`. |
| US-2 | As a **process engineer**, I ask *"write a Python program that calculates X and test it"*, so that the system generates the code, runs it in the sandbox with tests, and returns verified results. |
| US-3 | As an **engineer**, I upload an engineering drawing/image and ask for analysis, so that a vision model reads it and returns structured understanding. |
| US-4 | As a **reviewer**, I see which model, provider, tools, and sources were used, along with artifact verification status, so that I can trust or re-run the work. |
| US-5 | As a **system admin**, I open the sovereignty dashboard and see real counters (internet status, external AI requests = 0, cloud uploads = 0, local model requests, tool executions), so that I can prove compliance. |
| US-6 | As an **operator**, I check the audit page for a non-sensitive trail of tasks, models, tools, and artifacts, so that the deployment is accountable. |
| US-7 | As a **developer**, I run code only inside the sandbox (no network, no host access), so that generated code cannot harm the organization. |

---

## 9. Functional Requirements

Requirements below are the **target state**. Items still in progress are
flagged `(in progress)` per `docs/PROGRESS.md`; the engineering contract that
governs them is `AGENTS.md`.

### 9.1 Model layer

| FR | Requirement |
|----|-------------|
| FR-1 | Provide a `ModelProvider` abstraction with `generate`, `stream`, `health_check`, `list_models`, `embeddings`. |
| FR-2 | Implement `OllamaProvider` as the only inference transport to local Ollama (`OLLAMA_BASE_URL`). |
| FR-3 | `ModelRegistry` assigns roles to configurable model names (env vars `OLLAMA_*_MODEL` + `registry.yaml`); no hard-coded model names in code. |
| FR-4 | `ModelRouter` deterministically selects: vision task → vision model; code → coding model; document/complex → reasoning; default → general. |
| FR-5 | Raise a clear `ModelUnavailableError` instead of silently falling back to cloud when a model is missing. |
| FR-6 | Support ≥ 2 configurable models; current set (4GB VRAM): `qwen2.5:3b` (general/reasoning), `qwen2.5-coder:3b` (coding), `qwen2.5vl:3b` (vision), `nomic-embed-text` (embedding). |

### 9.2 Agent

| FR | Requirement |
|----|-------------|
| FR-7 | Explicit state machine: `RECEIVED → CLASSIFYING → PLANNING → EXECUTING → OBSERVING → VERIFYING → COMPLETED/FAILED`. |
| FR-8 | Bounded execution loop (`MAX_AGENT_ITERATIONS`, default 12) with limited retry/replan on tool failure. |
| FR-9 | Planner classifies task type (code, document, multimodal, general) and required capabilities (vision, tools). |
| FR-10 | Executor runs the plan via permission-checked `ToolRegistry` handlers. |
| FR-11 | Verifier re-opens and checks generated artifacts (required sections/fields) before completion. |
| FR-12 | Never expose chain-of-thought to the user; stream concise progress labels instead. |

### 9.3 Multimodal / OCR

| FR | Requirement |
|----|-------------|
| FR-13 | Pipeline detects file type (PDF, image, DOCX, XLSX, TXT/CSV) and normalizes to `ExtractedDocument` (text, pages, tables, warnings). |
| FR-14 | Digital PDFs: extract text layer directly. Scanned PDFs: render pages (pypdfium2) and run OCR. |
| FR-15 | OCR runs **locally** via RapidOCR (`rapidocr-onnxruntime`) — never cloud. `(in progress: engine verified on rendered pages)` |
| FR-16 | `OcrUnavailableError` surfaces an explicit UI warning rather than silent failure. |
| FR-17 | Vision-capable model reads images/drawings/P&IDs/scanned notes locally. `(in progress: qwen2.5vl:3b verified reading image)` |

### 9.4 RAG (local knowledge)

| FR | Requirement |
|----|-------------|
| FR-18 | Ingestion: parse → chunk → embed locally (Ollama embedding model) → store (Qdrant, or local in-process store as dev fallback). |
| FR-19 | Retrieval returns chunks with citation metadata: `document_id`, `document_name`, `page_number`, `section`, `version`, `classification`, `chunk_id`. |
| FR-20 | UI displays source references (e.g., *Maintenance SOP · Page 14 · Section 4.2*). |
| FR-21 | `RAG_BACKEND=local|qdrant`; Qdrant container path pending verification. `(in progress: local store verified; qdrant pending)` |

### 9.5 Tools

| FR | Requirement |
|----|-------------|
| FR-22 | Central `ToolRegistry` with registered tools: read/write/list/search files, calculator, document extraction, knowledge search/ingest, code execute, run tests, create DOCX/XLSX/PPTX/PDF. |
| FR-23 | Every tool defines name, description, input/output schema, permission, risk level. |
| FR-24 | Execution is permission-checked; `code.execute`/`code.run_tests` granted only for explicitly requested code tasks. |
| FR-25 | Filesystem access confined to per-task workspace; path traversal and absolute-path escapes blocked. |

### 9.6 Sandbox

| FR | Requirement |
|----|-------------|
| FR-26 | LLM-generated code executes only inside Docker (`network_mode=none`, isolated filesystem, no host mounts, no secrets). |
| FR-27 | Enforced CPU, memory, pids, and hard timeout. |
| FR-28 | Docker-unavailable returns a structured failure — never host execution, never a cloud fallback. `(in progress: live container validation pending)` |

### 9.7 Artifacts

| FR | Requirement |
|----|-------------|
| FR-29 | Generate real files: DOCX (priority), XLSX, PPTX, PDF, TXT. |
| FR-30 | Primary demo artifact: `approval_note.docx`. |
| FR-31 | Verification: file exists → parse/open → required sections present → critical fields present → return. On failure, bounded replan. |

### 9.8 Security, audit, sovereignty

| FR | Requirement |
|----|-------------|
| FR-32 | JWT-based authentication with seeded demo user (`admin/admin`, configurable). |
| FR-33 | Audit log records task, user, model/provider, tool executions, documents accessed, artifacts, verification status — never passwords, keys, secrets, or full document contents. |
| FR-34 | Sovereignty endpoint reports real, non-fabricated counters: internet status probe, external AI requests = 0, cloud uploads = 0, local tool executions, inference = local. `(in progress: counters present; full-stack composition demo pending)` |
| FR-35 | Secrets never logged; `.env` gitignored; no hard-coded credentials. |

### 9.9 API

| FR | Requirement |
|----|-------------|
| FR-36 | Endpoints: auth/login, tasks CRUD + cancel, documents upload/list, knowledge ingest/search, models list/test, agent runs detail, artifact download, system health/sovereignty, audit. |
| FR-37 | Live agent progress streamed via Server-Sent Events (SSE). |

### 9.10 Frontend UI

| FR | Requirement |
|----|-------------|
| FR-38 | Pages: Workspace (task submission + live agent timeline), Documents, Knowledge Base, Models, Artifacts, Audit, Sovereignty, Login. |
| FR-39 | Timeline shows: ✓ understanding/classifying/planning, ✓ selecting model, ✓ reading document, ✓ running OCR, ✓ searching knowledge base, ✓ analyzing, ✓ generating artifact, ✓ verifying; plus model, provider, tools, sources, artifacts, status. |
| FR-40 | Professional enterprise look and feel (Tailwind, shadcn-style components, Lucide icons). |

---

## 10. Non-Functional Requirements

### 10.1 Security

- NFR-1: No external AI APIs, cloud OCR, cloud embeddings, or cloud vector stores — with no silent cloud fallback of any kind.
- NFR-2: All paths, tool args, model responses, artifact paths, and uploads validated.
- NFR-3: Sandbox has no network, no host filesystem, no secrets, no host code execution.
- NFR-4: Secrets and document contents never logged.

### 10.2 Sovereignty / compliance

- NFR-5: Run entirely inside the organization network; runtime AI/data traffic stays local.
- NFR-6: Sovereignty stats must be real (live probe + actual counters), never fabricated.
- NFR-7: Audit trail is complete for actions, but content-agnostic.

### 10.3 Performance & hardware

- NFR-8: Target GPU: NVIDIA RTX 4050 Laptop, ~4 GB VRAM → small 3B models (7B optional on better hardware).
- NFR-9: Agent loop bounded (12 iterations) to cap latency and resource use.
- NFR-10: OCR, embedding, and inference run on local CPU/GPU as available.

### 10.4 Reliability & developer experience

- NFR-11: Backend runnable with zero external services in dev (`DATABASE_BACKEND=sqlite`, `RAG_BACKEND=local`) and production-like via Docker Compose by flipping backend vars.
- NFR-12: Tooling: `pnpm build`, `pnpm lint`, `pnpm typecheck`, `pnpm test` (pytest + ruff + tsc; mypy to be wired in).
- NFR-13: `docs/PROGRESS.md` is the single source of truth for done / in-progress status.

---

## 11. System Architecture

### 11.1 Logical architecture

```text
                    USER
                     │
                     ▼
               Next.js Web
                     │
                     ▼
                 FastAPI
                     │
                     ▼
             Agent Orchestrator
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Planner      Model Router    Tools (ToolRegistry)
                     │
                     ▼
                Model Provider
                     │
                     ▼
                  Ollama
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       General     Coding     Vision
        Model       Model      Model
```

### 11.2 Supporting infrastructure

```text
PostgreSQL / SQLite (dev) ── metadata, audit, tasks
Qdrant / local numpy store ── RAG vectors
Local storage (workspaces/) ── documents, artifacts
Docker Sandbox ── networkless code execution
Local OCR (RapidOCR) ── scanned PDF / image text
Ollama ── local inference + embeddings
MinIO (compose) ── object storage
```

### 11.3 Primary data flows

**Flow 1 — Inspection Report → Approval Note (primary demo):**

```text
Upload scanned inspection PDF
  → text layer / OCR (local)
  → extract findings
  → RAG over maintenance SOP (local embeddings → Qdrant)
  → agent reasoning
  → generate approval_note.docx
  → verifier re-opens + checks required sections
  → return verified artifact
```

**Flow 2 — Coding Request → Verified Code:**

```text
Request (code keywords / explicit code_request)
  → route to coding model
  → generate code
  → execute in Docker sandbox (no network)
  → run tests
  → verify
  → return result
```

**Flow 3 — Multimodal Document Analysis:**

```text
Upload image / scanned engineering document
  → OCR / vision model (local)
  → structured understanding
  → reasoning
  → response
```

### 11.4 Repository layout

```text
apps/
├── web/      # Next.js 15, React 19, TS, Tailwind (@sovereign/web)
├── api/      # FastAPI + SQLAlchemy (@sovereign/api)
│   ├── agent/       # orchestrator, planner, executor, state, memory, verifier
│   ├── models/      # providers (base/ollama), registry, router, schemas
│   ├── tools/       # registry + filesystem/calculator/code/documents/rag/artifacts/vision
│   ├── multimodal/  # pdf, ocr, images, tables, pipeline
│   ├── rag/         # chunking, embeddings, qdrant, ingestion, retrieval
│   ├── sandbox/     # docker, manager, policies
│   ├── artifacts/   # docx, xlsx, pptx, pdf generators
│   ├── security/    # auth, audit
│   ├── db/          # SQLAlchemy models, session
│   └── api/         # routers: tasks, documents, knowledge, models, agents, artifacts, audit, system
├── infrastructure/  # ollama, postgres, qdrant, minio, sandbox configs
├── sample_documents/
├── datasets/
├── tests/           # unit + integration
└── scripts/         # model pulls, setup
```

---

## 12. Tech Stack (as built)

| Layer | Technology |
|-------|-----------|
| Monorepo / orchestration | pnpm + Turborepo |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, lucide-react |
| Backend | Python 3.11+, FastAPI 0.115, Pydantic 2, SQLAlchemy 2, Uvicorn |
| Auth | JWT (PyJWT) + passlib/bcrypt |
| Database | PostgreSQL 16 (prod, compose) · SQLite (dev fallback, `DATABASE_BACKEND`) |
| Vector store | Qdrant (prod, compose) · in-process numpy store (dev fallback, `RAG_BACKEND`) |
| Inference | Ollama — qwen2.5:3b, qwen2.5-coder:3b, qwen2.5vl:3b, nomic-embed-text |
| OCR | RapidOCR (`rapidocr-onnxruntime`) — local only |
| Code sandbox | Docker SDK (`docker`), `network_mode=none`, CPU/mem/pids/time limits |
| Artifacts | python-docx, openpyxl, python-pptx, reportlab |
| Doc parsing | pdfplumber, pypdfium2, Pillow |
| Real-time | SSE (`sse-starlette`) |
| Quality | pytest, ruff, mypy, `tsc --noEmit` |
| Infrastructure | Docker Compose — api, web, ollama, postgres, qdrant, minio |

---

## 13. Data Model

Database entities (per `apps/api/db/models.py`); full document contents are
stored on disk, the DB keeps metadata/paths/previews only.

| Entity | Purpose | Key fields |
|--------|---------|-----------|
| `User` | Auth identity | username, password_hash, is_active |
| `Task` | User request | prompt, task_type, status, workspace |
| `AgentRun` | One execution of a task | status, model_calls, selected_models, verification_result |
| `AgentStep` | Progress step | label, detail, status |
| `Document` | Uploaded file metadata | filename, stored_path, mime_type, content_type, text_preview, page_count |
| `DocumentChunk` | RAG chunk | document_name, page_number, section, version, classification, chunk_id, text |
| `Model` | Registry snapshot | name, provider, capabilities, context_length, vision/tool support, enabled |
| `ToolExecution` | Tool audit record | tool_name, status, risk_level, duration_ms |
| `Artifact` | Generated file | name, kind, stored_path, verification_status |
| `AuditLog` | Non-sensitive audit | action, model_selected, tool_name, documents_accessed, artifact_generated, verification_status |

---

## 14. API Surface

```text
POST /api/auth/login
POST /api/tasks                          # multipart: prompt, code_request, file
GET  /api/tasks
GET  /api/tasks/{id}                     # task + run + steps + tools + artifacts
GET  /api/tasks/{id}/events              # SSE live progress
POST /api/tasks/{id}/cancel
POST /api/documents/upload
GET  /api/documents
POST /api/knowledge/ingest
POST /api/knowledge/search
GET  /api/models
POST /api/models/test
GET  /api/agents/runs/{id}
GET  /api/artifacts/{id}
GET  /api/system/health                  # backend, db, rag, ollama url
GET  /api/system/sovereignty             # internet probe + real counters
GET  /api/audit
```

---

## 15. Acceptance Criteria (Definition of Done)

Mirrors `AGENTS.md` §32. Status reflects `docs/PROGRESS.md` (✓ = verified,
△ = in progress, per the tracker).

| Area | Criterion | Status |
|------|-----------|--------|
| Models | Ollama works locally | ✓ |
| Models | ≥ 2 configurable models | ✓ |
| Models | Router selects models | ✓ |
| Models | Provider abstraction exists | ✓ |
| Agent | Planning, multi-step execution, tool calling, state, verification | ✓ |
| Agent | Retry/replan bounded (12) | ✓ |
| Multimodal | PDF upload works | ✓ |
| Multimodal | Scanned-PDF OCR works | △ |
| Multimodal | Image understanding works | △ |
| RAG | Ingest documents, local embeddings, sources displayed | ✓ |
| RAG | Qdrant retrieval works | △ |
| Tools | File tools, calculator, python, DOCX generation | ✓ |
| Sandbox | Docker execution, network off, fs isolated, limits | ✓ coded · △ live validation |
| Security | Auth, permissions, audit, secrets | ✓ |
| Sovereignty | No external AI calls/uploads, local inference | ✓ |
| Sovereignty | Network status demonstrable | △ |
| Demo | Inspection → approval note (live, `approval_note.docx` verified) | ✓ |
| Demo | Coding → sandbox → tests → verification | △ |
| Demo | Multimodal document analysis | △ |
| Demo | Real DOCX artifact + agent progress in UI | ✓ |

**Gate to call the product "MVP-complete":** every `△` above resolves to ✓
with a passing test or a live demo.

---

## 16. Milestones (Development Phases)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation — Next.js, FastAPI, Postgres, Ollama, Compose | ✓ built · full-stack validation △ |
| 2 | Model layer — Provider, OllamaProvider, Registry, Router | ✓ |
| 3 | Agent — Planner, Executor, State, ToolRegistry, Verifier | ✓ |
| 4 | Documents — PDF, OCR, images | △ |
| 5 | RAG — embeddings, Qdrant, ingest, retrieval, citations | △ |
| 6 | Tools — filesystem, calculator, python, DOCX | ✓ |
| 7 | Sandbox — Docker, network isolation, limits | △ (live validation) |
| 8 | UI — workbench, timeline, sources, artifacts, models | ✓ |
| 9 | Sovereignty — audit, network monitoring, dashboard | △ |
| 10 | Demo — inspection→approval, coding→verified, multimodal | △ |

**Open actions** (from `docs/PROGRESS.md`): live sandbox validation with a real
container, flip full-stack config (`postgresql` + `qdrant`) and validate,
stand up the compose stack, wire `mypy` into turbo, initial git commit, and
complete the three demo workflows end-to-end.

---

## 17. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Limited VRAM (~4 GB) | Large models unusable | Use 3B-class models; configurable names allow 7B+ on better hardware. |
| OCR dependency weight | Scanned PDF handling blocked | RapidOCR (pure Python ONNX) preferred; clear "OCR unavailable" message, no cloud fallback. |
| Docker daemon unavailable | Coding demo blocked | Structured failure surfaced; no host execution; README troubleshooting covers starting Docker. |
| Chat models not pulled yet | Live agent inference `△` | `scripts/pull_models.*`; `/api/models` availability check; no auto-download. |
| Qdrant/Postgres not running | Production-path config blocked | Local dev fallbacks (sqlite / numpy store) keep dev runnable; compose path for prod-like runs. |
| Scope creep (cloud, ML router, orchestration) | Sovereignty + timeline | Non-goals locked in §5; modular monolith first. |

---

## 18. Success Metrics / KPIs

- **Runtime external-call count = 0** (sovereignty dashboard, verified live).
- **Demo completion rate**: all three demo workflows pass with tests/live runs.
- **Artifact verification pass rate**: generated DOCX/code passes the verifier on
  first or bounded-retry attempt.
- **Agent boundedness**: no run exceeds `MAX_AGENT_ITERATIONS`.
- **UI adoption**: agent progress (model, tools, sources, artifacts) visible
  during every task run.
- **Test health**: `pnpm test`, `pnpm lint`, `pnpm typecheck` green.

---

## 19. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2026-08-30 | Initial PRD derived from `AGENTS.md`, README, ADR-001..005, `docs/PROGRESS.md`, and the as-built codebase. Target-state scope; in-progress items flagged. |