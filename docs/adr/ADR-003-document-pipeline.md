# ADR-003: Document Pipeline and Local OCR with Graceful Degradation

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

AGENTS.md requires a local multimodal pipeline that distinguishes digital vs
scanned PDFs, runs local OCR (preferred: PaddleOCR), and never uses cloud OCR.
PaddleOCR is a large optional dependency not installed by default, so the
pipeline must not fail hard when it is absent.

## Decision

1. `multimodal/pipeline.py` detects file type and:
   - For PDFs, extracts the text layer; if absent (scanned), renders pages via
     `pypdfium2` and runs OCR.
   - For images, runs OCR.
   - For TXT/DOCX/XLSX/CSV, extracts text directly.
2. `multimodal/ocr.py` loads PaddleOCR lazily. If it is not installed it raises
   `OcrUnavailableError`, which the pipeline converts into an explicit warning
   on the `ExtractedDocument` (`["OCR unavailable — install paddleocr"]`).
   There is **no cloud OCR fallback** and no silent failure.

## Consequences

- Digital documents (including the bundled demo inspection PDF) work fully with
  zero OCR dependency.
- Scanned/image processing requires the operator to install PaddleOCR; until
  then the UI surfaces a clear "OCR unavailable" message.
- The pipeline returns a normalized `ExtractedDocument` (text, pages, tables,
  warnings) consumed by the agent and RAG.
