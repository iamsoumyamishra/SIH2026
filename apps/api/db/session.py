"""SQLAlchemy engine, session factory, and base declarative class."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _connect_args() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (dev-friendly; use Alembic for migrations in prod)."""
    import db.models  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)
