# AGENTS.md

## Sovereign On-Premise Agentic AI Workbench

> Problem Statement 26117 — MRPL
> Build a self-hosted, air-gapped AI workbench for confidential industrial work
> using open-weight multimodal models.

---

## 1. Idea

A local AI workbench that feels like Claude + Codex + a document-analysis
workspace, with a hard guarantee:

> No confidential data, prompts, documents, artifacts, or inference requests
> leave the organization's infrastructure.

Everything runs on-premise with **Ollama** and **open-weight models**. The user
says *"do this task"*; the system decides the model, documents/tools,
execution, verification, and artifact.

Primary workflows:

```text
Inspection → OCR/vision → Findings → Search SOP → Analyze → Approval Note
Coding request → Generate code → Sandbox → Tests → Verify → Result
```

---

## 2. Architecture

```text
USER → Next.js Web → FastAPI → Agent Orchestrator
     │                        ├─ Planner
     │                        ├─ ModelRouter
     │                        └─ Tools (ToolRegistry)
     │                                │
     OLLAMA ← ModelProvider ←────────┘
     (General / Coding / Vision / Embedding)
```

PostgreSQL, Qdrant, MinIO, Docker sandbox, and local OCR support everything.

### Rules

- **Ollama is a provider, not the architecture.** Never call it directly: go
  `Agent → ModelRouter → ModelProvider → OllamaProvider`. A future
  `VLLMProvider` drops in unchanged.
- **Models**: roles are configuration (`OLLAMA_*_MODEL` + `registry.yaml`),
  never hard-coded: general, reasoning, coding, vision, embedding.
- **Router**: deterministic rule-based (task type, vision/tool support,
  availability). No ML router.
- **Agent**: explicit state machine
  `RECEIVED→CLASSIFYING→PLANNING→EXECUTING→OBSERVING→VERIFYING→COMPLETED/FAILED`,
  capped at `MAX_AGENT_ITERATIONS=12`; no chain-of-thought.
- **Tools**: central registry with schema/permission/risk; LLM may call only
  registered tools.
- **Isolation**: generated code runs only in a Docker sandbox (no network,
  isolated FS, no secrets, timeout + CPU/mem limits) — never the host; each
  task gets an isolated filesystem workspace, path traversal blocked.
- **Multimodal**: PDF text layer or local OCR (RapidOCR) when scanned; images
  via local vision model. OCR is never cloud.
- **RAG**: local embeddings → Qdrant (numpy dev fallback) with citation
  metadata (document, page, section).
- **Artifacts**: real files (DOCX/XLSX/PPTX/PDF), re-opened and verified
  before return.
- **Sovereignty**: no cloud AI/OCR/embeddings, no silent fallback; audit logs
  actions (never secrets/content); real counters.
- **DB entities**: User, Task, AgentRun, AgentStep, Document, DocumentChunk,
  Model, ToolExecution, Artifact, AuditLog.

---

## 3. Tech Stack

pnpm + Turborepo (monorepo); Next.js, React, TypeScript, Tailwind, shadcn/ui,
Lucide (frontend); Python, FastAPI, Pydantic, SQLAlchemy (backend); PostgreSQL
(compose) with SQLite dev fallback; Qdrant with local numpy dev fallback;
Ollama (qwen2.5:3b, qwen2.5-coder:3b, qwen2.5vl:3b, nomic-embed-text); RapidOCR
(local); Docker SDK sandbox (`network_mode=none`); python-docx, openpyxl,
python-pptx, reportlab (artifacts); pdfplumber, pypdfium2, Pillow (docs/PDF );
JWT (PyJWT) + bcrypt (auth); SSE via sse-starlette (real-time); pytest, ruff,
mypy, tsc (quality).

---

## 4. Keeping Docs in Sync

`docs/PROGRESS.md` is the **single source of truth** for done vs. remaining;
read it before starting a task and update it whenever state changes.

Significant architectural changes or major features must update this file,
`README.md`, `docs/PROGRESS.md`, and add a new `docs/adr/` record, in the same
change.

---

## 5. Final Principle

Build for sovereignty first, modularity second, simplicity third, performance
later. No cloud dependencies, no host code execution, no unrestricted
filesystem access, no unbounded agent loops.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
