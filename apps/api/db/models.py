"""SQLAlchemy ORM models for the Sovereign AI Workbench.

See AGENTS.md §28 for the required model set and relationships.

NOTE: We never store full confidential document contents here. Files live on
disk; the DB stores metadata, safe text summaries, and paths only.
"""
from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

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

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    tasks = relationship("Task", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=True)
    prompt = Column(Text, nullable=False)
    task_type = Column(Enum(TaskType), default=TaskType.UNKNOWN)
    status = Column(Enum(TaskStatus), default=TaskStatus.RECEIVED)
    workspace = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="tasks")
    runs = relationship("AgentRun", back_populates="task", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.RUNNING)
    model_calls = Column(Integer, default=0)
    selected_models = Column(JSON, default=list)
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verification_result = Column(JSON, nullable=True)

    task = relationship("Task", back_populates="runs")
    steps = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan")
    tool_executions = relationship(
        "ToolExecution", back_populates="run", cascade="all, delete-orphan"
    )
    artifacts = relationship(
        "Artifact", back_populates="run", cascade="all, delete-orphan"
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    label = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    status = Column(String(40), default="running")
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    run = relationship("AgentRun", back_populates="steps")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    mime_type = Column(String(120), nullable=True)
    content_type = Column(String(40), default="unknown")  # text | scanned | image ...
    text_preview = Column(Text, nullable=True)  # safe, truncated summary
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    document_name = Column(String(255), default="")
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    version = Column(String(60), nullable=True)
    classification = Column(String(60), nullable=True)
    chunk_id = Column(String(120), nullable=True)
    text = Column(Text, nullable=False)


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, index=True, nullable=False)
    provider = Column(String(60), default="ollama")
    capabilities = Column(JSON, default=list)
    context_length = Column(Integer, nullable=True)
    vision_support = Column(Boolean, default=False)
    tool_support = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    tool_name = Column(String(120), nullable=False)
    status = Column(Enum(ToolResultStatus), default=ToolResultStatus.SUCCESS)
    risk_level = Column(String(40), nullable=True)
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    duration_ms = Column(Integer, nullable=True)
    note = Column(String(500), nullable=True)

    run = relationship("AgentRun", back_populates="tool_executions")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    kind = Column(String(40), nullable=True)  # docx | xlsx | pptx | pdf | txt | code
    stored_path = Column(String(500), nullable=False)
    verification_status = Column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    run = relationship("AgentRun", back_populates="artifacts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)
    action = Column(String(120), nullable=False)
    model_selected = Column(String(120), nullable=True)
    tool_name = Column(String(120), nullable=True)
    tool_result_status = Column(String(40), nullable=True)
    documents_accessed = Column(String(500), nullable=True)
    artifact_generated = Column(String(250), nullable=True)
    verification_status = Column(String(40), nullable=True)
    detail = Column(String(500), nullable=True)  # non-sensitive metadata only
