"""Sovereign AI Workbench — FastAPI application entrypoint.

Wires all API routers behind JWT auth and streams live agent progress via SSE.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agents.router import router as agents_router
from api.artifacts.router import router as artifacts_router
from api.audit.router import router as audit_router
from api.auth.router import router as auth_router
from api.documents.router import router as documents_router
from api.knowledge.router import router as knowledge_router
from api.models.router import router as models_router
from api.system.router import router as system_router
from api.tasks.router import router as tasks_router
from config.settings import settings
from db.session import SessionLocal, init_db
from security.auth import ensure_demo_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        ensure_demo_user(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Sovereign AI Workbench API",
    version="0.1.0",
    description="Local-first agentic AI workbench for confidential work.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default settings-provided health/root are replaced by the system router.
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(documents_router)
app.include_router(knowledge_router)
app.include_router(models_router)
app.include_router(agents_router)
app.include_router(artifacts_router)
app.include_router(system_router)
app.include_router(audit_router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"service": "Sovereign AI Workbench API", "docs": "/docs"}


# Public (unauthenticated) health check for orchestration/tooling.
@app.get("/api/system/health/open", include_in_schema=False)
def open_health() -> dict:
    return {
        "status": "ok",
        "service": "sovereign-ai-workbench-api",
        "database_backend": settings.database_backend,
        "rag_backend": settings.rag_backend,
        "ollama_base_url": settings.ollama_base_url,
    }
