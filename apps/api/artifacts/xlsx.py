"""XLSX artifact generation using openpyxl."""

from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Font


def generate_xlsx(
    path: str | Path,
    sheet_name: str,
    headers: list[str],
    rows: list[list],
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    wb.save(str(path))
    return path
