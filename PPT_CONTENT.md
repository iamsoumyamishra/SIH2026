# PPT Content — Sovereign On-Premise Agentic AI Workbench

> Problem Statement 26117 (MRPL) · Smart India Hackathon 2026
> Slide-ready content for a 5-section build.

---

## 1. Idea

### Project Title
**Sovereign On-Premise Agentic AI Workbench for Confidential Industrial Work**

*A local Claude + Codex + document-analysis workspace that guarantees no
prompt, document, or inference ever leaves the plant.*

### The Problem
MRPL handles confidential industrial data — inspection reports, SOPs, P&ID
drawings, approval notes. Cloud AI, cloud OCR, and cloud embeddings are
unacceptable for data-governance and security reasons, and plants must work
offline.

### Proposed Solution
A fully self-hosted, air-gapped AI workbench. The user says *"do this task"*
and an agent decides the model, the documents/tools, the execution, and the
verification — everything running on-premise with open-weight models (Ollama)
and a **verified output artifact** (approval-note DOCX, tested code, etc.).

### Innovation Highlights
- **Agentic orchestration on a 100% local stack** — Planner → rule-based
  ModelRouter → permission-checked ToolRegistry → Verifier, in an explicit,
  bounded state machine (≤12 iterations).
- **Hard sovereignty guarantee with real telemetry** — a live dashboard shows
  genuine counters (internet probe, external AI calls = 0, cloud uploads = 0);
  nothing is fabricated.
- **Model-provider abstraction** — the agent never calls Ollama directly
  (`ModelProvider → OllamaProvider`); a `VLLMProvider` drops in tomorrow
  without touching agent code. Model names are configuration, not code.
- **Explainable routing** — deterministic rule-based model selection (no ML
  router) keeps every decision auditable per task.
- **Multimodal + RAG + sandbox + verified artifacts in one loop** — scanned
  PDFs (local OCR), images (local vision model), procedural knowledge search
  (local RAG with citations), safe code execution (Docker, no network), and
  artifacts that are reopened and verified before delivery.

---

## 2. Technical Approach

### High-Level Process
```
User task
  → Classify & Plan (Planner)
  → Route to local model (ModelRouter → Ollama)
  → Execute with tools (ToolRegistry, permission-checked)
  → Observe / retry (bounded, ≤ MAX_AGENT_ITERATIONS=12)
  → Verify artifact (Verifier reopens + checks sections)
  → Return result + audit trail (SSE timeline in UI)
```

### Workflow A — Inspection Report → Approval Note (primary)
1. Upload scanned inspection PDF (Next.js → FastAPI).
2. Text extraction: digital PDF → text layer; scanned → render pages
   (pypdfium2) + local OCR (RapidOCR, ONNX — never cloud).
3. Agent extracts findings.
4. RAG: `nomic-embed-text` embeddings → Qdrant (local store fallback in dev),
   retrieves the relevant SOP with citations (document, page, section).
5. Reasoning over findings + SOP (general/reasoning model).
6. Generate `approval_note.docx` (python-docx).
7. Verifier reopens the DOCX, checks required paragraphs/sections/fields.
8. Publish artifact + live progress over SSE.

### Workflow B — Coding Request → Verified Code
1. Task keyword/flag detected → routed to `qwen2.5-coder` coding model.
2. Code generated into an isolated per-task workspace.
3. Executed inside a Docker sandbox — `network_mode=none`, isolated FS, no
   secrets, CPU/memory/pids limits, hard timeout; never on the host.
4. Tests run; results verified; stepwise progress streamed.

### Workflow C — Multimodal Document Analysis
1. Image / scanned engineering document uploaded.
2. Vision model (`qwen2.5vl`) reads it locally; optional OCR for text.
3. Structured understanding → reasoning → response.

### Stack (current)
- Frontend: Next.js + React + TypeScript + Tailwind + shadcn/ui + Lucide
- Backend: FastAPI + Pydantic + SQLAlchemy, SSE (`sse-starlette`)
- Inference: Ollama — qwen2.5:3b, qwen2.5-coder:3b, qwen2.5vl:3b,
  nomic-embed-text
- Data: PostgreSQL (compose) / SQLite dev fallback; Qdrant / local numpy store
- Code execution: Docker SDK sandbox; Artifacts: python-docx, openpyxl,
  python-pptx, reportlab; Docs: pdfplumber, pypdfium2, Pillow
- Auth/audit: JWT + bcrypt, non-sensitive audit log, sovereignty monitor
- Monorepo: pnpm + Turborepo; Quality: pytest, ruff, mypy, tsc

---

## 3. Feasibility and Viability

### Feasibility (we have proven the core already)
- Working agent core: planning, multi-step execution, tool calling, state,
  bounded retries — verified.
- Live Demo 1: inspection report → `approval_note.docx`, verified. ✓
- Models, OCR, and vision installed and verified on local hardware. ✓
- RAG, tools, artifacts, auth, audit, UI all built. ✓
- Dev fallbacks (SQLite + local vector store) make the backend runnable with
  zero external services; Docker Compose provides the production-like path.

### Challenges and Risks
| Challenge | Risk | Mitigation |
|-----------|------|-----------|
| Limited GPU (~4 GB VRAM) | Small models (3B) limit output quality | Configurable model names; 7B+ on better hardware; verification gate + bounded retries |
| Air-gapped deployment | Models/containers must exist before going offline | Ship `scripts/pull_models.*` as an operator step; no auto-download |
| OCR dependency weight | Scanned-doc handling may stall | RapidOCR (pure Python ONNX) chosen; explicit *“OCR unavailable”* message, no cloud fallback |
| Docker required for sandbox | Coding demo blocked on host | Structured failure + clear troubleshooting; never run code on host |
| Small-model hallucinations | Reports/code may be wrong | Deterministic Verifier reopens artifacts; bounded replan (≤12) |
| Infra setup (Postgres/Qdrant) | Onboarding friction | One command `docker compose up`; dev fallbacks keep dev loop fast |
| Latency (local CPU/GPU inference) | Slower than cloud | Streaming/SSE progress; 3B models sized for the target GPU |

### Viability
- Zero recurring cloud AI/API cost; runs on commodity hardware already owned.
- Compliance-ready: audit trail + sovereign telemetry → demonstrable
  data-governance posture for a PSU/refinery environment.
- Modular monolith + provider abstraction → low maintenance and a clear path
  to larger models, more tools, and richer UI.

---

## 4. Impact and Benefits

### Target Audience
- **Inspection & maintenance engineers** — fast, SOP-grounded findings and
  draft approval notes.
- **Process / reliability engineers** — search procedural manuals, analyze
  drawings/documents, generate engineering notes.
- **Reviewers & approvers** — trusted, verifiable artifacts with visible model,
  tools, sources, and verification status.
- **Developers / analysts** — sandbox-verified code for ad-hoc computation.
- **IT / security / compliance** — a sovereignty dashboard and audit trail to
  prove nothing left the building.

### Benefits
- **Confidentiality & sovereignty** — no external AI/OCR/embeddings; works
  fully air-gapped; data never leaves the organization.
- **Trust & verifiability** — every artifact is reopened and checked before
  delivery; every action is audited; models/sources are shown in the UI.
- **Productivity** — inspection-to-approval, SOP search, and code tasks move
  from hours/days to minutes.
- **Multimodal coverage** — legacy paper + scanned engineering docs become
  queryable digital knowledge.
- **Cost & independence** — no cloud subscriptions or data-export clauses;
  open-weight models keep the stack vendor-neutral.
- **Explainability** — deterministic routing + explicit agent states make the
  system auditable in a regulated industrial environment.

---

## 5. Research and References

### Concepts grounding the design
- **RAG (Retrieval-Augmented Generation)** for grounded answers with
  citations; local embeddings (nomic-embed-text).
- **Agentic workflows / tool use** with an explicit state machine and bounded
  iteration (ReAct-style loop, local-only).
- **Air-gapped / sovereign AI deployment** with open-weight models (Qwen2.5
  family) and no cloud fallback.

### Local project references
- `AGENTS.md` — idea, architecture contract, tech stack
- `PRD.md` — problem statement, scope, requirements, acceptance criteria
- `docs/adr/ADR-001..005` — records for dev fallbacks, model provider,
  document pipeline, RAG, sandbox/artifacts
- `docs/PROGRESS.md` — status of Definition-of-Done items

### Tool/library documentation (all local-friendly, open-source)
- Ollama — local model serving · https://ollama.com
- Qwen2.5 / Qwen2.5-VL, coding & vision models · https://qwenlm.github.io
- nomic-embed-text (embeddings) · https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- Qdrant — local vector DB · https://qdrant.tech
- RapidOCR / rapidocr-onnxruntime — local OCR · https://github.com/RapidAI/RapidOCR
- FastAPI — Python API framework · https://fastapi.tiangolo.com
- Next.js — React framework · https://nextjs.org
- Docker — sandboxed, networkless code execution · https://docs.docker.com
- python-docx / openpyxl / python-pptx / reportlab — document generation

---

*Prepared from the built codebase: agent orchestrator, model router/providers,
multimodal pipeline, RAG, tools, sandbox, verifier, and live demo workflows.*
---

## Appendix A — Whole Architecture & Workflow (Detailed)

### A.1 System Architecture

```
┌──────────────────────────┐
│      NEXT.JS WEB UI      │  Workspace, Documents, Knowledge, Models,
│  (apps/web, App Router)  │  Artifacts, Audit, Sovereignty pages
└────────────┬─────────────┘
             │  REST (JWT) + SSE (live timeline)
┌────────────▼─────────────┐
│      FASTAPI BACKEND     │  Routers: tasks, documents, knowledge,
│   (apps/api main.py)     │  models, agents, artifacts, audit, system
└────────────┬─────────────┘
             │ submit / run
┌────────────▼─────────────┐
│     AGENT ORCHESTRATOR   │  classify → plan → route → execute → verify
│   (agent/orchestrator.py)│  explicit state machine, ≤12 iterations
└───────┬─────────┬────────┘
        │         │
   ┌────▼────┐ ┌──▼─────────────┐
   │ PLANNER │ │  MODEL ROUTER  │ deterministic rule-based selection
   │(planner)│ │ (models/router)│ (vision/code/document/general)
   └─────────┘ └──┬─────────────┘
                  ▼
        ┌───────────────────┐        ┌──────────────────┐
        │   MODEL REGISTRY   │  role→model config     │   OLLAMA           │
        │ (models/registry)  │ ────────► OLLAMA        │  qwen2.5:3b       │
        └───────────────────┘        │  PROVIDER        │  qwen2.5-coder:3b │
                                     │ (providers/      │  qwen2.5vl:3b     │
                                     │  ollama.py)      │  nomic-embed-text │
                                     └──────────────────┘
        ┌───────────────────┐
        │    EXECUTOR        │ runs plan via permission-checked tools
        │  (agent/executor)  │
        └─────────┬─────────┘
                  ▼
        ┌──────────────────────────── TOOL REGISTRY (tools/registry.py)
        │  file.read/write/list/search │ calculator │ extract_document
        │  search/ingest knowledge     │ execute_code (sandbox) │ run_tests
        │  create_docx/xlsx/pptx/pdf   └──────────────┬──────────────┘
        └──────────────┬───────────────┬──────────────┼─────────────┐
              ┌────────▼──────┐  ┌─────▼──────┐  ┌────▼─────┐  ┌────▼──────┐
              │ MULTIMODAL     │  │ LOCAL RAG   │  │ DOCKER   │  │ ARTIFACT  │
              │ pipeline       │  │ nomic-embed │  │ SANDBOX  │  │ generators│
              │ PDF/OCR(img)   │  │ + Qdrant    │  │ no net   │  │ DOCX/XLSX│
              │ RapidOCR       │  │ citations   │  │ limits   │  │ PPTX/PDF │
              └────────┬──────┘  └─────┬──────┘  └───────────┘  └────┬──────┘
                       └───────────────┴───────────────┬─────────────┘
                                                       ▼
                                             ┌──────────────────┐
                                             │     VERIFIER      │ reopens artifact
                                             │ (agent/verifier)  │ checks sections/fields
                                             └──────────────────┘
        ┌────────────────────────────────────────────┐
        │ CONTROL PLANE: JWT auth · audit log ·       │
        │ event bus (SSE) · sovereignty monitor       │
        │ + STORAGE: PostgreSQL/SQLite · workspaces/  │
        │   (isolated per-task dirs) · Qdrant/local   │
        └────────────────────────────────────────────┘
```

### A.2 Layer-by-layer breakdown

1. **Client / UI layer** — Next.js 15 + React + TS. Pages: Workspace (task
   submission + live agent timeline), Documents, Knowledge, Models,
   Artifacts, Audit, Sovereignty, Login. Talks to the API with a JWT; the
   Workspace page subscribes to an **SSE stream** so users watch the run
   update in real time.

2. **API layer** — FastAPI routers under `apps/api/api/`:
   `tasks` (submit, list, detail, cancel, SSE events), `documents` (upload,
   list), `knowledge` (ingest, search), `models` (list, test), `agents`
   (run detail), `artifacts` (download), `audit`, `system` (health,
   sovereignty). Multipart upload lets a task carry one input file.

3. **Orchestration layer** — `agent/orchestrator.py` owns the run: it
   instantiates the state machine
   `RECEIVED → CLASSIFYING → PLANNING → EXECUTING → OBSERVING → VERIFYING →
   COMPLETED | FAILED`, invokes the Planner, routes the model, then runs the
   plan inside a bounded loop (`MAX_AGENT_ITERATIONS=12`). It streams every
   transition and tool result to the event bus.

4. **Decision layer**
   - **Planner** (`agent/planner.py`) — classifies the prompt (`code`,
     `document`, `multimodal`, `general`) and computes required capabilities
     (vision, tool calling). No LLM is needed for planning.
   - **ModelRouter** (`models/router.py`) — deterministic rules: vision
     task → vision model; code keywords/task → coding model; document /
     complex reasoning → reasoning model; else general. Falls back across
     roles; raises a clear error if nothing is configured (no silent cloud
     fallback).

5. **Model layer** — `ModelRegistry` maps roles (`general, reasoning,
   coding, vision, embedding`) to concrete Ollama model names from
   `registry.yaml` + `OLLAMA_*_MODEL` env vars. `OllamaProvider` implements
   the `ModelProvider` interface (`generate`, `stream`, `health_check`,
   `list_models`, `embeddings`) against local Ollama. Higher layers only see
   the interface, so a future `VLLMProvider` swaps in without agent changes.

6. **Knowledge layer**
   - **Multimodal pipeline** (`multimodal/pipeline.py`) — detects file type;
     PDF → text layer via pdfplumber/pypdfium2; scanned → render pages +
     local **RapidOCR** (`ocr.py`); images via `images.py` and the vision
     model; DOCX/XLSX/PPTX/TXT extracted directly. Returns a normalized
     `ExtractedDocument` (text, pages, tables, warnings).
   - **Local RAG** (`rag/`) — chunks with metadata (document, page, section,
     version, classification) → embeddings via Ollama
     (`nomic-embed-text`) → Qdrant (dev fallback: local numpy cosine store).
     Retrieval (`retrieval.py`) returns chunks with citations so the UI can
     show sources.

7. **Execution layer** — `ToolRegistry` is a central, permission-checked
   registry. Each tool declares schema, permission, and risk. Tools:
   read/write/list/search files (restricted to the per-task isolated
   workspace, path traversal blocked), calculator, `extract_document`,
   `search_knowledge` / `ingest_knowledge`, `execute_code` / `run_tests`,
   and artifact creators (`create_docx|xlsx|pptx|pdf`). High-risk
   `code.execute`/`code.run_tests` permissions are granted only for explicit
   code tasks. Tool runs are recorded (name, risk, duration) for audit.

8. **Sandbox layer** — `sandbox/docker.py` executes generated code inside a
   Docker container with `network_mode=none`, isolated filesystem, no
   secrets, CPU/memory/pids limits, and a hard timeout. If the Docker daemon
   is unavailable it returns a structured failure — it never runs on the
   host and never calls a cloud.

9. **Delivery layer** — `artifacts/` contains real generators (python-docx,
   openpyxl, python-pptx, reportlab). The **Verifier**
   (`agent/verifier.py`) reopens the produced file and checks required
   paragraphs/sections/fields before the artifact is accepted; failures
   trigger bounded re-observation.

10. **Control plane & storage**
    - `security/auth.py` — JWT + bcrypt (demo user `admin/admin`).
    - `security/audit.py` + `audit_logs` table — non-sensitive record of
      actions (task, model, tools, documents accessed, artifacts,
      verification) — never passwords, secrets, or document content.
    - `services/event_bus.py` — SSE fan-out for live progress.
    - `db/models.py` — User, Task, AgentRun, AgentStep, Document,
      DocumentChunk, Model, ToolExecution, Artifact, AuditLog.
    - Storage: `workspaces/task-{id}/{input,working,output}` per-task
      directories; backend selected by env (`sqlite` dev / `postgresql`
      compose; `local` RAG / `qdrant`).

### A.3 Workflow #1 — Inspection Report → Approval Note (primary)

Every task lifecycle (state machine shown in brackets):

1. **Submit** — engineer uploads the scanned inspection PDF with prompt
   *"generate an approval note for the findings"* `[RECEIVED]`.
2. **Classify** — planner labels it a *document* task `[CLASSIFYING]`.
3. **Route** — router selects the reasoning/general model; vision flag if
   scanned pages need reading `[PLANNING]`.
4. **Extract** — `extract_document` tool runs the multimodal pipeline:
   render pages → RapidOCR → findings text (local). If OCR is absent, an
   explicit warning is surfaced — never a cloud call.
5. **RAG** — `search_knowledge` embeds the findings and retrieves the
   relevant maintenance SOP chunks from Qdrant with citations (page/section).
6. **Reason** — the model cross-references findings against SOP requirements.
7. **Generate** — `create_docx` writes a real `approval_note.docx` into the
   task's output directory `[EXECUTING]`.
8. **Verify** — the Verifier reopens the DOCX and checks required headings
   and fields; if missing, the agent re-observes and retries (bounded) 
   `[VERIFYING → OBSERVING]`.
9. **Deliver** — state becomes `COMPLETED`; run + steps + tool executions +
   artifact + verification result are persisted, the artifact is downloadable,
   and the sovereignty counter for local model requests/tool executions is
   updated. The whole run streamed live via SSE to the Workspace page.

### A.4 Workflow #2 — Coding Request → Verified Code

- Planner classifies as *code* → router picks `qwen2.5-coder`; `code.execute`
  + `code.run_tests` permissions granted.
- Code is written into the task's isolated workspace.
- `execute_code` runs it in the Docker sandbox: `network_mode=none`, resource
  limits, timeout. No network, no host FS, no secrets.
- `run_tests` executes the tests in the same sandbox; results are read back.
- The Verifier confirms output/tests; the task completes and the code +
  results are returned as artifacts. Without Docker, a clear structured
  failure is shown (no host execution, no cloud).

### A.5 Workflow #3 — Multimodal Document Analysis

- Upload image or scanned engineering document → vision/OCR path.
- `qwen2.5vl` (local vision model) reads the image; optional RapidOCR pulls
  text; structured fields/understanding are extracted.
- Findings are reasoned over and answered with sources; if required, an
  artifact is produced and verified exactly as in Workflow #1.

### A.6 Supporting flows

- **Knowledge base** — `/documents/upload` stores the file; `/knowledge/ingest`
  chunks + embeds + indexes it; `/knowledge/search` answers grounded queries
  with citations.
- **Models page** — lists router-visible models and live availability;
  `/models/test` runs a mini inference check.
- **Audit page** — non-sensitive trail of every run's actions.
- **Sovereignty page** — live probe + real counters (internet reachable,
  external AI requests = 0, cloud uploads = 0, local tool executions,
  local model requests). Numbers are real, never fabricated.
