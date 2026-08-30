"""PDF artifact generation using reportlab."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def generate_pdf(
    path: str | Path,
    title: str,
    sections: list[dict],
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for section in sections:
        if section.get("heading"):
            story.append(Paragraph(section["heading"], styles["Heading2"]))
            story.append(Spacer(1, 6))
        body = section.get("body", "")
        if isinstance(body, str):
            body = [body]
        for para in body:
            story.append(Paragraph(para, styles["Normal"]))
            story.append(Spacer(1, 4))
    doc.build(story)
    return path
