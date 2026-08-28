# AGENTS.md — Sovereign AI Workbench

## 1. Project Overview

Build a **Sovereign On-Premise Agentic AI Workbench** for confidential industrial and government work.

The system must provide a Claude/Codex-like AI experience while ensuring that:

> **No user data, documents, prompts, generated artifacts, or model requests leave the local infrastructure.**

The system must run entirely on-premise using **Ollama and open-weight models**.

The platform must support:

* Multiple local LLMs
* Automatic model selection
* Agentic multi-step execution
* Tool calling
* Local RAG
* OCR
* Multimodal document/image understanding
* Code execution in a sandbox
* Calculations
* Word/PPT/Excel generation
* Verification
* Audit logging
* Network isolation
* Model/provider abstraction

The architecture must not be tightly coupled to a single model.

---

# 2. Core Product

The product is an **AI Workbench**, not simply a chatbot.

A user should be able to say:

> "Analyze this scanned inspection report, compare the findings against the maintenance SOP, calculate the required values, and generate an approval note."

The system should autonomously:

```text
User Request
    ↓
Task Understanding
    ↓
Task Classification
    ↓
Model Selection
    ↓
Planning
    ↓
Tool Selection
    ↓
Execution
    ↓
Observation
    ↓
Reasoning
    ↓
Verification
    ↓
Artifact Generation
    ↓
Final Response
```

---

# 3. Primary Demonstration Workflow

The primary demo must be:

```text
Scanned Inspection Report
        ↓
Document Detection
        ↓
OCR
        ↓
Vision Understanding
        ↓
Information Extraction
        ↓
Local RAG
        ↓
Maintenance SOP Retrieval
        ↓
Reasoning
        ↓
Risk/Compliance Analysis
        ↓
Approval Note Generation
        ↓
DOCX Verification
        ↓
Final Deliverable
```

The system must show agent execution progress in the UI.

Example:

```text
✓ File received
✓ Document analyzed
✓ Scanned pages detected
✓ OCR completed
✓ Findings extracted
✓ Relevant SOP retrieved
✓ Analysis completed
✓ Approval note generated
✓ Document verified
```

---

# 4. Architecture Principles

Follow these principles strictly.

### 4.1 Local-first

All AI inference must happen locally.

Never send data to:

* OpenAI
* Anthropic
* Google
* OpenRouter
* Hugging Face inference APIs
* Cloud OCR
* Cloud embeddings
* Cloud vector databases
* Any external AI API

unless explicitly enabled by a future administrator-controlled feature.

For the current implementation:

> External AI/API calls are forbidden.

---

### 4.2 Model agnostic

Never directly couple application code to a specific model.

Bad:

```python
ollama.chat(model="qwen...")
```

throughout the codebase.

Good:

```text
Agent
  ↓
ModelRouter
  ↓
ModelProvider
  ↓
OllamaProvider
  ↓
Ollama
```

The agent must not know whether the model is running through Ollama, vLLM, or another provider.

---

### 4.3 Tool isolation

The LLM must never receive unrestricted operating-system access.

All operations must go through controlled tools.

```text
Agent
  ↓
Tool Gateway
  ↓
Permission Check
  ↓
Tool
  ↓
Sandbox / Controlled Resource
```

---

### 4.4 Explicit agent state

Do not implement an uncontrolled infinite agent loop.

Use explicit states:

```text
RECEIVED
CLASSIFYING
PLANNING
EXECUTING
OBSERVING
VERIFYING
COMPLETED
FAILED
```

The agent must have a maximum number of iterations.

---

### 4.5 Everything must be auditable

Every agent execution should produce an audit trail containing:

* Task ID
* User ID
* Timestamp
* Task type
* Models selected
* Tools executed
* Documents accessed
* Execution status
* Verification status
* Generated artifacts

Do not log sensitive document contents or secrets.

---

# 5. Recommended Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* shadcn/ui
* Lucide icons

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy

## AI

* Ollama
* Open-weight LLMs
* Local vision-language model where supported
* Local embedding model

## RAG

* Qdrant
* Local embeddings

## Database

* PostgreSQL

## Object/File Storage

Development:

```text
Local filesystem
```

Production-like deployment:

```text
MinIO
```

## OCR

Prefer:

```text
PaddleOCR
```

with other local OCR tools allowed where necessary.

## Code Sandbox

```text
Docker
```

## Authentication

For MVP:

```text
JWT-based authentication
```

Future enterprise deployment:

```text
Keycloak / enterprise identity provider
```

## Deployment

```text
Docker Compose
```

Do not introduce Kubernetes unless there is a genuine requirement.

---

# 6. Repository Structure

Use this structure:

```text
sovereign-ai-workbench/
│
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── apps/
│   │
│   ├── web/
│   │   └── Next.js application
│   │
│   └── api/
│       │
│       ├── main.py
│       │
│       ├── api/
│       │   ├── auth/
│       │   ├── tasks/
│       │   ├── agents/
│       │   ├── documents/
│       │   ├── knowledge/
│       │   ├── artifacts/
│       │   └── system/
│       │
│       ├── agent/
│       │   ├── orchestrator.py
│       │   ├── planner.py
│       │   ├── executor.py
│       │   ├── verifier.py
│       │   ├── state.py
│       │   ├── memory.py
│       │   └── context.py
│       │
│       ├── models/
│       │   ├── router.py
│       │   ├── registry.py
│       │   ├── schemas.py
│       │   └── providers/
│       │       ├── base.py
│       │       └── ollama.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── permissions.py
│       │   ├── filesystem/
│       │   ├── documents/
│       │   ├── vision/
│       │   ├── python/
│       │   ├── code/
│       │   ├── calculator/
│       │   └── rag/
│       │
│       ├── multimodal/
│       │   ├── pdf.py
│       │   ├── ocr.py
│       │   ├── images.py
│       │   ├── tables.py
│       │   └── pipeline.py
│       │
│       ├── rag/
│       │   ├── ingestion.py
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   ├── retrieval.py
│       │   └── qdrant.py
│       │
│       ├── sandbox/
│       │   ├── manager.py
│       │   ├── docker.py
│       │   └── policies.py
│       │
│       ├── artifacts/
│       │   ├── docx.py
│       │   ├── pptx.py
│       │   ├── xlsx.py
│       │   └── pdf.py
│       │
│       ├── security/
│       │   ├── auth.py
│       │   ├── permissions.py
│       │   ├── policies.py
│       │   └── audit.py
│       │
│       ├── db/
│       │   ├── models.py
│       │   ├── session.py
│       │   └── repositories/
│       │
│       └── config/
│           └── settings.py
│
├── infrastructure/
│   ├── ollama/
│   ├── postgres/
│   ├── qdrant/
│   ├── minio/
│   ├── sandbox/
│   └── monitoring/
│
├── sample_documents/
├── datasets/
├── tests/
└── scripts/
```

---

# 7. Ollama Architecture

Ollama is the initial inference backend.

Use:

```text
Agent
 ↓
Model Router
 ↓
Ollama Provider
 ↓
Ollama
 ↓
Local Model
```

Do not directly call Ollama from agent code.

Create:

```python
class ModelProvider:
    async def generate(...):
        ...

    async def stream(...):
        ...

    async def health_check(...):
        ...

    async def capabilities(...):
        ...
```

Then implement:

```text
ModelProvider
     │
     └── OllamaProvider
```

This allows a future:

```text
VLLMProvider
```

without changing the agent.

---

# 8. Model Registry

Maintain a registry of available models.

Example:

```yaml
models:

  - id: general
    provider: ollama
    model: <local-general-model>
    capabilities:
      - text
      - reasoning
      - tool_calling

  - id: coding
    provider: ollama
    model: <local-coding-model>
    capabilities:
      - text
      - coding
      - tool_calling

  - id: vision
    provider: ollama
    model: <local-vision-model>
    capabilities:
      - text
      - image
      - vision
```

Do not hard-code model names throughout the application.

---

# 9. Model Router

The router receives a task and determines which model is appropriate.

Example:

```text
Task:
"Write and test Python code"

Required capabilities:
coding
tool_calling

        ↓

Coding Model
```

Another:

```text
Task:
"Analyze this engineering drawing"

Required capabilities:
vision
reasoning

        ↓

Vision Model
```

The router should consider:

* Task type
* Required capabilities
* Context size
* Vision support
* Tool-calling support
* Model availability
* Hardware constraints

Start with rule-based routing.

Do not build an unnecessarily complicated ML-based router for the MVP.

---

# 10. Agent Architecture

The agent consists of:

```text
Orchestrator
    │
    ├── Planner
    ├── Model Router
    ├── Tool Manager
    ├── Context Manager
    ├── Memory
    ├── Executor
    └── Verifier
```

---

# 11. Agent Execution Loop

Use this pattern:

```text
RECEIVE
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
EXECUTE
   ↓
OBSERVE
   ↓
VERIFY
   ↓
SUCCESS?
 ┌─┴─┐
NO  YES
│    │
▼    ▼
REPLAN COMPLETE
```

Every execution must have:

```text
MAX_AGENT_ITERATIONS
```

Example:

```text
MAX_AGENT_ITERATIONS = 12
```

Never allow unlimited execution.

---

# 12. Planning

The planner should convert the user's request into structured steps.

Example:

```json
{
  "goal": "Prepare inspection approval note",
  "steps": [
    {
      "id": "1",
      "action": "read_document"
    },
    {
      "id": "2",
      "action": "perform_ocr"
    },
    {
      "id": "3",
      "action": "extract_findings"
    },
    {
      "id": "4",
      "action": "search_knowledge_base"
    },
    {
      "id": "5",
      "action": "analyze_findings"
    },
    {
      "id": "6",
      "action": "generate_docx"
    },
    {
      "id": "7",
      "action": "verify_document"
    }
  ]
}
```

---

# 13. Tool System

Every tool must have:

```text
name
description
input schema
output schema
permissions
risk level
```

Example:

```text
Tool:
read_file

Permission:
document.read

Risk:
low
```

Another:

```text
Tool:
execute_python

Permission:
code.execute

Risk:
high
```

---

# 14. Tool Registry

All tools should be registered centrally.

```text
ToolRegistry

├── read_file
├── write_file
├── search_files
├── read_pdf
├── OCR
├── search_knowledge
├── python
├── execute_code
├── create_docx
├── create_pptx
├── create_xlsx
└── analyze_image
```

The agent should only be able to call registered tools.

---

# 15. File System Security

Never give the agent unrestricted filesystem access.

Create a workspace:

```text
/workspaces/
    task-001/
        input/
        working/
        output/
```

The agent can only access the current task workspace unless explicitly authorized.

Never allow arbitrary paths such as:

```text
/
etc/
home/
var/
```

from an LLM-generated tool call.

Normalize and validate every path.

Prevent:

```text
../
```

path traversal.

---

# 16. Code Execution Sandbox

Code execution must happen inside Docker.

```text
Agent
 ↓
Code Tool
 ↓
Sandbox Manager
 ↓
Docker Container
 ↓
Execute
 ↓
Return stdout/stderr/result
```

Sandbox restrictions:

```text
Network: disabled
Filesystem: isolated
Secrets: unavailable
Host filesystem: unavailable
Timeout: required
CPU limit: required
Memory limit: required
```

Never execute LLM-generated code directly on the host.

---

# 17. Multimodal Pipeline

All uploaded documents must pass through a document processing pipeline.

```text
Input
 ↓
File Type Detection
 ↓
Document Parser
 ↓
Is scanned?
 ├── No → Text extraction
 └── Yes → OCR
 ↓
Image extraction
 ↓
Table extraction
 ↓
Vision model if required
 ↓
Normalized representation
 ↓
Agent
```

Support:

* PDF
* Images
* DOCX
* XLSX
* TXT

Prioritize PDF and images for the MVP.

---

# 18. OCR

OCR must be completely local.

Pipeline:

```text
Scanned PDF
 ↓
Render pages
 ↓
OCR
 ↓
Extract text + bounding boxes
 ↓
Normalize
 ↓
Agent
```

Never use cloud OCR.

---

# 19. Vision

For visual content:

```text
Image
 ↓
Local Vision Model
 ↓
Structured description
 ↓
Agent Context
```

Use vision models for:

* Engineering drawings
* P&IDs
* Inspection photographs
* Scanned handwritten notes
* Tables
* Diagrams

Do not pretend a text-only model can understand an image.

---

# 20. RAG Architecture

Knowledge ingestion:

```text
Document
 ↓
Parser
 ↓
Text extraction
 ↓
Chunking
 ↓
Local Embedding Model
 ↓
Qdrant
```

Query:

```text
Agent
 ↓
RAG Tool
 ↓
Embedding
 ↓
Qdrant Search
 ↓
Relevant Chunks
 ↓
Agent Context
```

Everything must remain local.

---

# 21. RAG Metadata

Each chunk should retain:

```text
document_id
document_name
page_number
section
department
version
classification
chunk_id
```

This allows citations such as:

```text
Maintenance SOP
Page 14
Section 4.2
```

The final answer should cite retrieved internal sources whenever appropriate.

---

# 22. Artifact Generation

The system must generate actual files.

Supported:

```text
DOCX
PPTX
XLSX
PDF
TXT
```

Priority:

```text
1. DOCX
2. XLSX
3. PPTX
4. PDF
```

For the primary demo, DOCX is mandatory.

---

# 23. Artifact Verification

Never blindly return generated files.

Use:

```text
Generate
 ↓
Validate
 ↓
Verify
 ↓
Return
```

For DOCX:

```text
✓ File exists
✓ File opens
✓ Required sections exist
✓ No empty critical fields
✓ Formatting is valid
```

For calculations:

```text
✓ Code executes
✓ Tests pass
✓ Result is present
```

---

# 24. Security Boundary

The entire application must operate within:

```text
┌───────────────────────────────────────────┐
│         ORGANIZATION NETWORK              │
│                                           │
│ Frontend                                  │
│ Backend                                   │
│ Ollama                                   │
│ Models                                    │
│ PostgreSQL                                │
│ Qdrant                                    │
│ MinIO                                     │
│ OCR                                       │
│ Sandbox                                   │
│                                           │
└───────────────────────────────────────────┘
                     │
                     X
                  INTERNET
```

The application must not make external calls.

---

# 25. No External Dependencies at Runtime

Runtime services must not depend on:

* Cloud LLM APIs
* Cloud OCR
* Cloud vector databases
* External embedding APIs
* External search APIs
* External telemetry services

Package installation can happen during development.

Runtime inference and document processing must remain local.

---

# 26. Network Monitoring

Implement a visible sovereignty monitor.

Display:

```text
Sovereignty Status

Internet:
BLOCKED

External API calls:
0

External AI requests:
0

Cloud uploads:
0

Local model requests:
XX

Local tool executions:
XX
```

The UI must not simply fake these values.

Use actual system/network information where possible.

---

# 27. Audit Logging

Every agent execution should create:

```text
AgentRun
├── task_id
├── user_id
├── started_at
├── completed_at
├── model_calls
├── tool_calls
├── documents_accessed
├── artifacts_generated
├── verification_result
└── status
```

Never log:

* passwords
* API keys
* document contents
* sensitive prompts unnecessarily
* secrets

---

# 28. Database Models

At minimum:

```text
User
Task
AgentRun
AgentStep
Document
DocumentChunk
Model
ToolExecution
Artifact
AuditLog
```

Relationships:

```text
User
 │
 └── Tasks
       │
       └── AgentRun
              │
              ├── AgentSteps
              ├── ToolExecutions
              └── Artifacts
```

---

# 29. API Design

Example endpoints:

```text
POST   /api/auth/login

POST   /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks/{id}/cancel

POST   /api/documents/upload
GET    /api/documents
GET    /api/documents/{id}

POST   /api/knowledge/ingest
POST   /api/knowledge/search

GET    /api/models
POST   /api/models/test

GET    /api/agents/runs/{id}

GET    /api/artifacts/{id}

GET    /api/audit
GET    /api/system/sovereignty
GET    /api/system/health
```

Use WebSockets or Server-Sent Events for live agent execution updates.

---

# 30. Frontend UX

The main workspace should show:

```text
┌─────────────────────────────────────────────┐
│ Sovereign AI Workbench                      │
├─────────────┬───────────────────────────────┤
│ Workspace   │                               │
│             │ Agent                         │
│ Chat        │                               │
│ Documents   │ User request                  │
│ Knowledge   │                               │
│ Tasks       │ Agent execution               │
│ Artifacts   │                               │
│ Models      │ ✓ Reading document            │
│ Audit       │ ✓ Searching SOP               │
│             │ ✓ Analyzing                   │
│             │ ✓ Generating document         │
│             │                               │
│             │ [Download Artifact]            │
└─────────────┴───────────────────────────────┘
```

The UI should emphasize:

* Agent progress
* Tool usage
* Model used
* Retrieved sources
* Generated artifacts
* Sovereignty status

---

# 31. Model Visibility

When the agent performs a task, show:

```text
Model:
Local Reasoning Model

Provider:
Ollama

Location:
On-Premise

Tools:
OCR
Knowledge Search
DOCX Generator
```

This helps demonstrate the sovereign architecture to judges.

---

# 32. Error Handling

Every component must fail gracefully.

If Ollama is unavailable:

```text
Model unavailable
```

Do not crash the entire API.

If OCR fails:

```text
OCR failed
 ↓
Attempt fallback
 ↓
If unsuccessful:
Ask user for a clearer document
```

If a tool fails:

```text
Tool failure
 ↓
Agent observes failure
 ↓
Retry or replan
```

All retries must have limits.

---

# 33. Secrets

Never hard-code:

```text
passwords
JWT secrets
database credentials
model credentials
```

Use environment variables.

Provide:

```text
.env.example
```

Never commit `.env`.

---

# 34. Testing Requirements

Every major subsystem requires tests.

## Unit tests

Test:

* Model router
* Agent state machine
* Tool registry
* Path validation
* RAG retrieval
* Artifact generation
* Permission system

## Integration tests

Test:

```text
Agent → Ollama
Agent → Tool
Agent → RAG
Agent → Sandbox
Agent → Artifact
```

## End-to-end test

Test:

```text
Upload scanned PDF
 ↓
OCR
 ↓
RAG
 ↓
Reasoning
 ↓
DOCX generation
 ↓
Verification
```

---

# 35. MVP Priority

Build in this exact order.

## Phase 1 — Infrastructure

```text
Docker Compose
PostgreSQL
Ollama
Qdrant
FastAPI
Next.js
```

## Phase 2 — Basic AI

```text
Ollama Provider
Model Registry
Model Router
Chat
```

## Phase 3 — Agent

```text
Planner
Executor
Tool Registry
Agent State
Verifier
```

## Phase 4 — Documents

```text
PDF parsing
OCR
Document extraction
```

## Phase 5 — RAG

```text
Ingestion
Embeddings
Qdrant
Retrieval
Citations
```

## Phase 6 — Tools

```text
File tools
Python
Calculator
DOCX
```

## Phase 7 — Sandbox

```text
Docker execution
Network isolation
Resource limits
```

## Phase 8 — UI

```text
Agent timeline
Artifacts
Sources
Model information
```

## Phase 9 — Sovereignty

```text
Firewall
Network monitoring
Audit logs
Security dashboard
```

## Phase 10 — Demo

Implement:

```text
Inspection Report
        ↓
OCR
        ↓
RAG
        ↓
Reasoning
        ↓
Approval Note
```

and:

```text
Coding Request
        ↓
Coding Model
        ↓
Sandbox
        ↓
Tests
        ↓
Verified Code
```

---

# 36. Development Rules for AI Coding Agents

When modifying the repository:

1. Read `AGENTS.md` first.
2. Understand existing architecture before creating new modules.
3. Do not duplicate functionality.
4. Prefer small, composable services.
5. Do not hard-code model names.
6. Do not call Ollama directly from business logic.
7. Do not expose arbitrary filesystem access.
8. Do not execute generated code on the host.
9. Do not introduce cloud APIs.
10. Do not add unnecessary dependencies.
11. Write tests for important functionality.
12. Preserve type safety.
13. Validate all external/user inputs.
14. Keep secrets out of source code.
15. Never bypass the security layer for convenience.
16. Never silently fall back to a cloud service.
17. Do not create fake sovereignty/network statistics.
18. Keep the system runnable using Docker Compose.
19. Prefer deterministic workflows for sensitive operations.
20. Document architectural changes.

---

# 37. Important Anti-Patterns

Never build:

```text
Frontend → Ollama directly
```

Instead:

```text
Frontend → API → Agent → Model Router → Provider → Ollama
```

Never build:

```text
Agent → OS shell
```

Instead:

```text
Agent → Tool → Permission → Sandbox
```

Never build:

```text
Agent → Cloud API fallback
```

Instead:

```text
Agent → Local fallback model
```

Never build:

```text
LLM → unrestricted filesystem
```

Instead:

```text
LLM → File Tool → Workspace Validation
```

---

# 38. Definition of Done

The MVP is complete only when all of the following work:

### AI

* [ ] Ollama runs locally
* [ ] At least two local models work
* [ ] Model router selects models
* [ ] Provider abstraction exists

### Agent

* [ ] Planner works
* [ ] Multi-step execution works
* [ ] Tool calling works
* [ ] Agent state is tracked
* [ ] Verification works
* [ ] Retry/replanning works

### Multimodal

* [ ] PDF processing works
* [ ] Scanned PDF OCR works
* [ ] Image understanding works

### RAG

* [ ] Documents can be ingested
* [ ] Embeddings are local
* [ ] Qdrant retrieval works
* [ ] Sources can be displayed

### Tools

* [ ] File tools work
* [ ] Calculator works
* [ ] Python works
* [ ] DOCX generation works

### Security

* [ ] Code executes in Docker
* [ ] Sandbox has no network
* [ ] Filesystem access is restricted
* [ ] Authentication works
* [ ] Audit logs work
* [ ] No cloud API calls occur

### Sovereignty

* [ ] Internet access is blocked
* [ ] External calls can be monitored
* [ ] UI displays real network status
* [ ] All inference occurs locally

### Demo

* [ ] Inspection report workflow works end-to-end
* [ ] Approval note DOCX is generated
* [ ] Coding workflow works
* [ ] Generated code is executed and verified
* [ ] Multimodal document is demonstrated

---

# 39. Final Product Flow

The final system must behave like:

```text
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
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
                   DOCX   PPTX   XLSX

                 ╔═══════════════════╗
                 ║   ON-PREMISE     ║
                 ║                  ║
                 ║  Ollama          ║
                 ║  PostgreSQL      ║
                 ║  Qdrant          ║
                 ║  Storage         ║
                 ║  Docker          ║
                 ║  OCR             ║
                 ║                  ║
                 ╚═══════════════════╝
                         │
                         X
                      INTERNET
```

---

# 40. Final Architectural Goal

The final product should satisfy this principle:

> **The user should not need to understand AI models, RAG, OCR, agents, tools, or infrastructure. They simply give the workbench a confidential task, and the system figures out how to complete it locally.**

The architecture should therefore hide the complexity:

```text
                  USER
                    │
                    ▼
            "Do this task."
                    │
                    ▼
            ┌───────────────┐
            │ SOVEREIGN AI  │
            │   WORKBENCH   │
            └───────┬───────┘
                    │
             Automatically
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
    Models        Tools         Knowledge
       │            │             │
       └────────────┼─────────────┘
                    ▼
                  AGENT
                    │
                    ▼
                VERIFY
                    │
                    ▼
               DELIVERABLE
```

**Build the MVP around Ollama now, but keep `ModelProvider` and `ModelRouter` as hard architectural boundaries.** This lets you start extremely quickly on a workstation while keeping the same application architecture ready for a future vLLM-based MRPL deployment.
