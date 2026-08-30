"""Document chunking for RAG ingestion.

Splits text into bounded chunks, optionally by section (AGENTS.md §20, §21).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Chunk:
    text: str
    chunk_id: str
    meta: dict[str, Any]


def chunk_text(
    text: str,
    document_id: str,
    document_name: str = "",
    page_number: int | None = None,
    section: str | None = None,
    chunk_size: int = 900,
    overlap: int = 120,
    prefix: str = "chunk",
) -> list[Chunk]:
    """Split text into overlapping chunks."""
    if not text or not text.strip():
        return []

    # Split into paragraphs first to respect structure.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[Chunk] = []
    current = ""
    index = 0

    for para in paragraphs:
        if len(para) > chunk_size:
            # split a very long paragraph into pieces
            for i in range(0, len(para), chunk_size - overlap):
                piece = para[i : i + chunk_size]
                if piece:
                    chunks.append(
                        _make_chunk(
                            piece,
                            index,
                            prefix,
                            document_id,
                            document_name,
                            page_number,
                            section,
                        )
                    )
                    index += 1
            continue

        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(
                    _make_chunk(
                        current,
                        index,
                        prefix,
                        document_id,
                        document_name,
                        page_number,
                        section,
                    )
                )
                index += 1
            current = para

    if current:
        chunks.append(
            _make_chunk(current, index, prefix, document_id, document_name, page_number, section)
        )
    return chunks


def _make_chunk(
    text: str,
    index: int,
    prefix: str,
    document_id: str,
    document_name: str,
    page_number: int | None,
    section: str | None,
) -> Chunk:
    return Chunk(
        text=text.strip(),
        chunk_id=f"{document_id}::{prefix}-{index}",
        meta={
            "document_id": document_id,
            "document_name": document_name,
            "page_number": page_number,
            "section": section,
        },
    )
