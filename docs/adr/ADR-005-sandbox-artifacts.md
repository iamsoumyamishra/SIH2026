# ADR-005: Sandboxed Code Execution and Real Artifact Generation

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

AGENTS.md: never run LLM-generated code on the host; execute inside Docker with
no network, isolated filesystem, resource limits, and timeouts. Artifacts must
be real files (DOCX priority), and verified before return.

## Decision

- **Sandbox** (`sandbox/docker.py`): every execution goes through Docker with
  `network_mode=none`, CPU/memory/pids limits, a hard timeout, and read-only
  mounts for helper files. If the Docker daemon is unavailable, `SandboxManager`
  returns a structured failure (never runs on host, never a cloud fallback).
- **Artifacts** (`artifacts/`): real DOCX (python-docx), XLSX (openpyxl),
  PPTX (python-pptx), PDF (reportlab) generators. `Verifier` re-opens and
  checks required paragraphs/fields / file existence before the artifact is
  accepted.
- Tools (`execute_code`, `run_tests`, `create_docx`, ...) are registered in the
  `ToolRegistry`; high-risk code permissions are granted only when a task
  explicitly needs them.

## Consequences

- Code and documents are real and verifiable, satisfying the demo acceptance
  criteria.
- Without Docker the coding demo degrades gracefully with a clear message.
- The artifact/verifier path is deterministic and testable.
