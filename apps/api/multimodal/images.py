"""Image helpers: format detection, base64 encoding, and PDF page rendering.

Used by OCR and the vision pipeline. No cloud services are used.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image


def is_image_file(path: str | Path) -> bool:
    ext = Path(path).suffix.lower()
    return ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


def load_image(path: str | Path) -> Image.Image:
    return Image.open(str(path)).convert("RGB")


def to_base64(path: str | Path) -> str:
    """Encode an image file to base64 (for the local vision model)."""
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def render_pdf_pages(
    pdf_path: str | Path, dpi: int = 150, max_pages: int | None = None
) -> list[Image.Image]:
    """Render PDF pages to PIL images using pypdfium2 (local)."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdfium2 is required to render PDF pages.") from exc

    pdf = pdfium.PdfDocument(str(pdf_path))
    scale = dpi / 72.0
    images: list[Image.Image] = []
    page_count = len(pdf)
    if max_pages is not None:
        page_count = min(page_count, max_pages)
    for i in range(page_count):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        images.append(pil)
    pdf.close()
    return images


def image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()
