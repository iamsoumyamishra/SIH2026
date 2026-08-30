"""PDF text extraction and scanned-page detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber


def extract_pdf_text(path: str | Path) -> dict[str, Any]:
    """Extract text from each page of a PDF.

    Returns dict with:
      - pages: list of per-page text
      - full_text: concatenated text
      - page_count
      - has_text: whether any page contains extractable text (digital detection)
    """
    path = Path(path)
    pages: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    full_text = "\n\n".join(pages).strip()
    return {
        "pages": pages,
        "full_text": full_text,
        "page_count": len(pages),
        "has_text": bool(full_text.strip()),
    }


def is_scanned(pdf_result: dict[str, Any]) -> bool:
    """Heuristic: a PDF is 'scanned' if it carries no extractable text layer."""
    return not pdf_result.get("has_text", False)
