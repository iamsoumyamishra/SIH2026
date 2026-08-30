"""Tests for the document pipeline (text and pdf paths avoid OCR)."""
from __future__ import annotations

from multimodal.pdf import extract_pdf_text, is_scanned
from multimodal.pipeline import DocumentPipeline


def test_text_file_pipeline(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("alpha bravo charlie", encoding="utf-8")
    doc = DocumentPipeline().ingest(f)
    assert doc.content_type == "text"
    assert "charlie" in doc.text


def test_digital_pdf_detected_as_text(tmp_path):
    import reportlab.lib.pagesizes
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    pdf_path = tmp_path / "digital.pdf"
    pdf = SimpleDocTemplate(str(pdf_path), pagesize=reportlab.lib.pagesizes.A4)
    pdf.build([Paragraph("This is a digital page", getSampleStyleSheet()["Normal"])])

    result = extract_pdf_text(pdf_path)
    assert result["has_text"] is True
    assert is_scanned(result) is False

    doc = DocumentPipeline().ingest(pdf_path)
    assert doc.content_type == "text"
    assert "digital page" in doc.text


def test_ocr_unavailable_reported_on_image(tmp_path):
    from PIL import Image

    from multimodal.ocr import OcrEngine

    img_path = tmp_path / "blank.png"
    Image.new("RGB", (20, 20), "white").save(img_path)
    doc = DocumentPipeline().ingest(img_path)
    assert doc.content_type == "image"
    # Either OCR ran and produced text, or it reported unavailable — never crashes.
    # With a real engine installed, a blank image may legitimately yield "" with
    # no warning (readable OCR produced no tokens).
    ocr_available = OcrEngine().is_available()
    assert any("OCR" in w for w in doc.warnings) or doc.text or ocr_available
