"""Task planning: classify the request and produce structured steps.

For the MVP this uses deterministic rules keyed on the prompt (and any detected
document type). A model-based planner can replace `plan()` later behind the same
signature.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Plan:
    goal: str
    steps: list[dict[str, str]] = field(default_factory=list)
    task_type: str = "general"
    required_capabilities: list[str] = field(default_factory=list)
    requires_vision: bool = False
    requires_tool_calling: bool = True

    def step_ids(self) -> list[str]:
        return [s["id"] for s in self.steps]


_CODE_KW = (
    "write a program",
    "write code",
    "python",
    "script",
    "function",
    "calculate the required values",
    "implement",
    "test the code",
    "coding",
)
_VISION_KW = ("image", "photo", "scanned", "diagram", "p&id", "drawing", "photo", "picture")
_DOC_KW = (
    "document",
    "report",
    "pdf",
    "inspection",
    "ocr",
    "sop",
    "note",
    "analyze this",
    "approval",
)


def classify(prompt: str) -> tuple[str, list[str]]:
    lowered = prompt.lower()
    if any(k in lowered for k in _CODE_KW):
        return "code", ["coding", "tool_calling"]
    if any(k in lowered for k in _VISION_KW):
        return "multimodal", ["vision", "reasoning"]
    if any(k in lowered for k in _DOC_KW):
        return "document", ["reasoning", "tool_calling"]
    return "general", ["reasoning"]


class Planner:
    def classify_prompt(self, prompt: str) -> tuple[str, list[str]]:
        return classify(prompt)

    def plan(self, prompt: str, task_type: str | None = None) -> Plan:
        """Build a concrete step plan for the request."""
        if task_type is None:
            task_type, caps = self.classify_prompt(prompt)
        else:
            _, guessed = self.classify_prompt(prompt)
            caps = guessed

        requires_vision = "vision" in caps
        plan = Plan(
            goal=prompt[:200],
            task_type=task_type,
            required_capabilities=caps,
            requires_vision=requires_vision,
            requires_tool_calling="tool_calling" in caps,
        )

        if task_type == "code":
            plan.steps = [
                {"id": "1", "action": "generate_code", "detail": "Write the program"},
                {"id": "2", "action": "execute_code", "detail": "Run code in sandbox"},
                {"id": "3", "action": "run_tests", "detail": "Run tests"},
                {"id": "4", "action": "verify_result", "detail": "Verify output"},
            ]
        elif task_type == "multimodal":
            plan.steps = [
                {
                    "id": "1",
                    "action": "read_document",
                    "detail": "Load document unless already present",
                },
                {"id": "2", "action": "perform_ocr", "detail": "OCR / vision understanding"},
                {"id": "3", "action": "extract_findings", "detail": "Extract structured findings"},
                {"id": "4", "action": "search_knowledge", "detail": "Search local knowledge base"},
                {"id": "5", "action": "analyze_findings", "detail": "Analyze against SOP"},
                {"id": "6", "action": "generate_docx", "detail": "Generate approval note"},
                {"id": "7", "action": "verify_document", "detail": "Verify the DOCX artifact"},
            ]
        elif task_type == "document":
            wants_approval = any(
                k in prompt.lower()
                for k in ("approval", "approve", "approval note", "generate a note")
            )
            plan.steps = [
                {"id": "1", "action": "read_document", "detail": "Extract document content"},
            ]
            if wants_approval:
                plan.steps.append(
                    {
                        "id": "2",
                        "action": "extract_findings",
                        "detail": "Extract structured findings",
                    }
                )
            plan.steps += [
                {"id": "3", "action": "search_knowledge", "detail": "Search local knowledge base"},
                {"id": "4", "action": "analyze", "detail": "Analyze content"},
            ]
            if wants_approval:
                plan.steps += [
                    {"id": "5", "action": "generate_docx", "detail": "Generate approval note"},
                    {"id": "6", "action": "verify_document", "detail": "Verify the DOCX artifact"},
                ]
            plan.steps.append({"id": "7", "action": "answer", "detail": "Produce final answer"})
        elif task_type == "general":
            plan.steps = [
                {"id": "1", "action": "analyze", "detail": "Understand the request"},
                {"id": "2", "action": "answer", "detail": "Produce the response"},
            ]
        return plan
