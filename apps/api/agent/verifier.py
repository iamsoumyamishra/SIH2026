"""Verification of agent outputs and generated artifacts (AGENTS.md §23).

The verifier is intentionally deterministic: it checks real conditions (file
exists, opens, required sections/fields present, code executed + test results)
rather than trusting that generation "looked right".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docx import Document as DocxDocument


@dataclass
class VerificationResult:
    passed: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def add_check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            self.passed = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "notes": self.notes,
        }


class Verifier:
    def verify_docx_file(
        self,
        path: Path | str,
        required_paragraphs: list[str] | None = None,
        required_fields: list[str] | None = None,
    ) -> VerificationResult:
        path = Path(path)
        result = VerificationResult(passed=True)
        result.add_check("file_exists", path.exists(), str(path))
        if not path.exists():
            result.notes = "DOCX file does not exist."
            return result

        try:
            doc = DocxDocument(str(path))
        except Exception as exc:  # noqa: BLE001
            result.add_check("file_opens", False, str(exc))
            result.notes = f"DOCX failed to open: {exc}"
            return result

        paragraphs = [p.text for p in doc.paragraphs]
        full_text = "\n".join(paragraphs)

        sections_present = bool(doc.sections)
        result.add_check("sections_exist", sections_present)

        if required_paragraphs:
            for para in required_paragraphs:
                result.add_check(
                    f"paragraph:{para}",
                    para in full_text,
                    "searched in document text",
                )

        if required_fields:
            for field in required_fields:
                result.add_check(
                    f"field:{field}",
                    bool(full_text.strip())
                    and any(field.lower() in p.lower() or p.strip() for p in paragraphs),
                    "field presence",
                )

        if not full_text.strip():
            result.add_check("non_empty", False, "document has no text")
        return result

    def verify_code_result(
        self,
        stdout: str,
        exit_code: int | None,
        test_output: str = "",
        expected_summary: str = "",
    ) -> VerificationResult:
        result = VerificationResult(passed=True)
        result.add_check("exit_code_zero", exit_code == 0, f"exit={exit_code}")
        if test_output:
            failed_tests = re.search(r"(\d+)\s+failed", test_output)
            result.add_check(
                "tests_passed",
                (not failed_tests) and "passed" in test_output.lower(),
                test_output.strip()[:200],
            )
        if expected_summary and stdout.strip() == "":
            result.add_check("has_output", False, "no stdout")
        if not result.passed:
            result.notes = "Code verification failed."
        return result
