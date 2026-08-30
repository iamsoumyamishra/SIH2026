# ADR-001: Development Fallbacks for Database and Vector Store

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

The workbench is designed for Docker Compose infrastructure (PostgreSQL + Qdrant).
During initial development the local Docker Desktop daemon is not running, which
would otherwise block running the backend and RAG entirely.

Additionally, AGENTS.md mandates that we never silently fall back to a *cloud*
service, and that the system must remain runnable. We therefore introduce
*local, deterministic* fallbacks that stay fully on-premise.

## Decision

1. **Database:** `settings.database_backend` selects the backend.
   - `sqlite` (default for dev): a local SQLite file at `apps/api/data/`.
   - `postgresql`: the compose PostgreSQL instance.
   This keeps the same SQLAlchemy models in both cases.

2. **Vector store (RAG):** `settings.rag_backend` selects the store.
   - `local` (default for dev): an in-process fallback vector store using numpy
     dot-product similarity. This is a real, deterministic store — not a cloud
     service.
   - `qdrant`: the Qdrant service via the official client.

3. The selection is surfaced in `/api/system/health` so operators can always
   see which backend is active. There is **no silent cloud fallback**.

## Consequences

- The backend and RAG are runnable immediately with zero external services.
- Production-like behavior (Postgres + Qdrant) is available via Docker Compose
  by flipping the two backend variables.
- Some concurrency/scale properties of the local fallbacks differ from the
  containerized services; this is acceptable for the MVP and clearly visible.
