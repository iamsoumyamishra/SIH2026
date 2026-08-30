"""Local OCR implementation.

Preferred engine: RapidOCR (rapidocr-onnxruntime) — a pure-Python, local and
offline OCR engine. It uses ONNX runtime and runs locally on Windows without
the heavy paddlepaddle dependency. Because RapidOCR is a sizeable optional
dependency, we load it lazily. If it is not installed, we raise a clear
OcrUnavailableError so the caller can surface "OCR unavailable — install
rapidocr-onnxruntime" rather than silently falling back to any cloud service.
"""
from __future__ import annotations

from typing import Any

from PIL import Image


class OcrUnavailableError(Exception):
    pass


def _load_rapidocr():
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
        return RapidOCR()
    except ImportError as exc:
        raise OcrUnavailableError(
            "RapidOCR is not installed. Install it (pip install "
            "rapidocr-onnxruntime) for OCR; no cloud OCR is ever used."
        ) from exc


class OcrEngine:
    def __init__(self) -> None:
        self._engine: Any | None = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            self._engine = _load_rapidocr()
        return self._engine

    def is_available(self) -> bool:
        try:
            self._get_engine()
            return True
        except OcrUnavailableError:
            return False

    def ocr_image(self, image: Image.Image) -> str:
        import numpy as np

        engine = self._get_engine()
        result, _ = engine(np.array(image))
        return _flatten_result(result)

    def ocr_image_bytes(self, image_bytes: bytes) -> str:
        import io

        return self.ocr_image(Image.open(io.BytesIO(image_bytes)))

    def ocr_pdf_pages(self, page_images: list[Image.Image]) -> str:
        parts = []
        for i, img in enumerate(page_images, 1):
            text = self.ocr_image(img)
            parts.append(f"--- page {i} ---\n{text}".strip())
        return "\n\n".join(parts)


def _flatten_result(result) -> str:
    """Flatten RapidOCR output into plain text lines.

    RapidOCR typical result: [ [ [x,y,x,y,x,y,x,y], ('text', score) ], ... ].
    """
    lines: list[str] = []
    if not result:
        return ""
    for item in result:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            text = item[1]
            if isinstance(text, (list, tuple)):
                text = text[0]
            lines.append(str(text))
    return "\n".join(lines)
