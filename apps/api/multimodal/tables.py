"""Table extraction from PDFs using pdfplumber (local)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber


def extract_tables(path: str | Path) -> list[dict[str, Any]]:
    """Extract tables from each page of a PDF.

    Returns a list of {"page": int, "table": [[...]]} entries, or an empty list
    if none are found.
    """
    path = Path(path)
    tables: list[dict[str, Any]] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables() or []:
                rows = []
                for row in table:
                    cleaned = ["" if c is None else str(c) for c in row]
                    rows.append(cleaned)
                tables.append({"page": page_idx, "table": rows})
    return tables
