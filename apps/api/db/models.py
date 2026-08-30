"""SQLAlchemy ORM models for the Sovereign AI Workbench.

See AGENTS.md §28 for the required model set and relationships.

NOTE: We never store full confidential document contents here. Files live on
disk; the DB stores metadata, safe text summaries, and paths only.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ── Enums ────────────────────────────────────────────────────
class TaskType(enum.StrEnum):
    UNKNOWN = "unknown"
    GENERAL = "general"
    DOCUMENT = "document"
    CODE = "code"
    MULTIMODAL = "multimodal"
    ANALYSIS = "analysis"


class TaskStatus(enum.StrEnum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolResultStatus(enum.StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class VerificationStatus(enum.StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


# ── Models ───────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    tasks = relationship("Task", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.UNKNOWN)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.RECEIVED)
    workspace: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user = relationship("User", back_populates="tasks")
    runs = relationship("AgentRun", back_populates="task", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.RUNNING)
    model_calls: Mapped[int] = mapped_column(Integer, default=0)
    selected_models: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    task = relationship("Task", back_populates="runs")
    steps = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan")
    tool_executions = relationship(
        "ToolExecution", back_populates="run", cascade="all, delete-orphan"
    )
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run = relationship("AgentRun", back_populates="steps")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    content_type: Mapped[str] = mapped_column(String(40), default="unknown")  # text|scanned|image
    text_preview: Mapped[str | None] = mapped_column(Text, nullable=True)  # safe, truncated summary
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("documents.id"), nullable=True
    )
    document_name: Mapped[str] = mapped_column(String(255), default="")
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(60), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(60), nullable=True)
    chunk_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(60), default="ollama")
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vision_support: Mapped[bool] = mapped_column(Boolean, default=False)
    tool_support: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ToolResultStatus] = mapped_column(
        Enum(ToolResultStatus), default=ToolResultStatus.SUCCESS
    )
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    run = relationship("AgentRun", back_populates="tool_executions")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )  # docx|xlsx|pptx|pdf|txt|code
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    run = relationship("AgentRun", back_populates="artifacts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    model_selected: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tool_result_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    documents_accessed: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_generated: Mapped[str | None] = mapped_column(String(250), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)  # non-sensitive only
