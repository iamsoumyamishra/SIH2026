"""Pytest fixtures shared across all test suites."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the API package importable regardless of where pytest is launched from.
API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(API_DIR))

# Isolate storage and DB for tests before any app module initializes.
TEST_DATA_DIR = Path(__file__).resolve().parent / "_tmp"
os.environ.setdefault("STORAGE_ROOT", str(TEST_DATA_DIR / "workspaces"))
os.environ.setdefault("DATABASE_BACKEND", "sqlite")


@pytest.fixture(scope="session")
def api_dir() -> Path:
    return API_DIR


@pytest.fixture(autouse=True)
def _clean_test_storage(tmp_path):
    """Ensure a clean workspace root for each test."""
    os.environ["STORAGE_ROOT"] = str(tmp_path / "workspaces")
    yield
