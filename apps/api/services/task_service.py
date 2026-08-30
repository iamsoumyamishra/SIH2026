"""Task service: wires the full agent stack for a user task.

Creates the task + secure workspace, binds tools and handlers, runs the
orchestrator with streaming progress + audit logging, and persists the run,
steps, tool executions, and artifacts.

This is the layer the API calls; the agent itself stays decoupled from the
concrete tools/services via ActionHandler + ToolRegistry + ModelRouter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.context import AgentContext
from agent.executor import ActionHandler
from agent.orchestrator import Orchestrator
from artifacts.docx import make_approval_note
from db.models import (
    AgentRun,
    AgentStep,
    Artifact,
    RunStatus,
    Task,
    TaskStatus,
    TaskType,
    ToolExecution,
    ToolResultStatus,
    VerificationStatus,
)
from db.session import SessionLocal
from models.registry import ModelRegistry
from models.schemas import GenerationRequest
from multimodal.pipeline import DocumentPipeline
from rag.retrieval import RetrievalService
from security.audit import AuditLogger
from services.event_bus import EventBus, get_event_bus
from tools.filesystem.workspace import Workspace, create_workspace
from tools.registry import ToolRegistry
from tools.setup import CODE_PERMISSIONS, build_registry


@dataclass
class RunOutput:
    task_id: int
    run_id: int
    status: str
    summary: dict[str, Any]


class TaskService:
    def __init__(
        self,
        db=None,
        bus: EventBus | None = None,
        pipeline: DocumentPipeline | None = None,
        retrieval: RetrievalService | None = None,
        registry: ModelRegistry | None = None,
    ) -> None:
        self._db = db
        self.bus = bus or get_event_bus()
        self.pipeline = pipeline or DocumentPipeline()
        self.retrieval = retrieval or RetrievalService()
        self.registry = registry or ModelRegistry()

    def _db_session(self):
        return self._db if self._db is not None else SessionLocal()

    # ── public entry ─────────────────────────────────────────
    def submit_task(
        self,
        prompt: str,
        user_id: int | None = None,
        code_request: bool = False,
        input_source: Path | None = None,
    ) -> Task:
        """Create the task + secure workspace + stage input.

        Returns the Task immediately so callers can hand back a task id and
        execute `run_task(task.id)` in the background.
        """
        db = self._db_session()
        try:
            task = Task(user_id=user_id, prompt=prompt, task_type=TaskType.UNKNOWN)
            db.add(task)
            db.commit()
            db.refresh(task)

            ws = create_workspace(task.id)
            task.workspace = str(ws.root)
            if input_source is not None and input_source.is_file():
                import shutil

                shutil.copy(input_source, ws.dir("input") / input_source.name)
            task.status = TaskStatus.RECEIVED
            db.commit()
            db.refresh(task)
            return task
        finally:
            if self._db is None:
                db.close()

    async def run_task(self, task_id: int, code_request: bool = False) -> RunOutput:
        """Execute the orchestrator for an already-submitted task."""
        db = self._db_session()
        try:
            task = db.query(Task).filter(Task.id == task_id).one()
            prompt = task.prompt
            user_id = task.user_id
            ws = Workspace(Path(task.workspace))

            ctx = AgentContext(
                task_id=task.id,
                user_id=user_id,
                prompt=prompt,
                workspace=str(ws.root),
                workspace_obj=ws,
            )

            audit = AuditLogger(db)
            audit.log_task_started(task.id, user_id, "unknown")

            registry = build_registry(include_code=code_request)
            if code_request:
                registry.grant_permissions(*CODE_PERMISSIONS)

            run = AgentRun(task_id=task.id, status=RunStatus.RUNNING)
            db.add(run)
            db.commit()
            db.refresh(run)

            self._wire_execution_hooks(registry, db, task.id, run.id, audit)

            handlers = self._build_handlers(ctx, registry)
            orch = Orchestrator(handlers=handlers)

            orchestrator_progress = self._make_progress(db, task, run, audit)
            orch.on_progress = orchestrator_progress

            await orch.run(ctx, prompt)

            await self._finalize(db, task, run, ctx, audit)

            return RunOutput(
                task_id=task.id,
                run_id=run.id,
                status=task.status.value,
                summary=self._summarize(ctx, task),
            )
        finally:
            if self._db is None:
                db.close()

    async def create_and_run(
        self,
        prompt: str,
        user_id: int | None = None,
        code_request: bool = False,
        input_source: Path | None = None,
    ) -> RunOutput:
        task = self.submit_task(
            prompt, user_id=user_id, code_request=code_request, input_source=input_source
        )
        return await self.run_task(task.id, code_request=code_request)

    # ── progress / persistence wiring ────────────────────────
    def _update_task_status(self, db, task: Task, status: TaskStatus) -> None:
        task.status = status
        db.add(task)
        db.commit()

    def _make_progress(self, db, task, run, audit):
        async def progress(label: str, status: str, detail: str | None = None):
            await self.bus.publish(
                task.id,
                {"type": "step", "label": label, "status": status, "detail": detail},
            )
            step = AgentStep(run_id=run.id, label=label, detail=detail, status=status)
            db.add(step)
            db.commit()
            if status in ("done", "warning"):
                # flip node-end states to done for the UI
                pass

        return progress

    def _wire_execution_hooks(self, registry: ToolRegistry, db, task_id, run_id, audit):
        def on_tool(name: str, risk: str, duration_ms: float):
            te = ToolExecution(
                run_id=run_id,
                tool_name=name,
                status=ToolResultStatus.SUCCESS,
                risk_level=risk,
                duration_ms=int(duration_ms),
            )
            db.add(te)
            db.commit()
            audit.log_tool(task_id, name, "success", risk)
            self._emit_now(task_id, {"type": "tool", "name": name, "risk": risk})

        registry.on_execution(on_tool)

    def _emit_now(self, task_id, event: dict):
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.bus.publish(task_id, event))
        except RuntimeError:
            pass

    async def _finalize(self, db, task, run, ctx, audit):
        # Persist artifacts
        for art in ctx.artifacts:
            ar = Artifact(
                run_id=run.id,
                name=art.get("name", ""),
                kind=art.get("kind", ""),
                stored_path=art.get("path", ""),
                verification_status=VerificationStatus(
                    "passed" if ctx.verification.get("passed", False) else "pending"
                ),
            )
            db.add(ar)
            status = "passed" if ctx.verification.get("passed", False) else "pending"
            audit.log_artifact(task.id, art.get("name", ""), status)
        db.commit()

        run.status = RunStatus.COMPLETED
        run.model_calls = ctx.model_calls
        run.selected_models = [ctx.selected_model_name] if ctx.selected_model_name else []
        run.verification_result = ctx.verification
        db.add(run)
        db.commit()

        if ctx.task_type:
            task.task_type = TaskType(ctx.task_type)
        is_done = ctx.verification.get("passed", True) or not ctx.artifacts
        self._update_task_status(db, task, TaskStatus.COMPLETED if is_done else TaskStatus.FAILED)
        await self.bus.publish(task.id, {"type": "done", "status": task.status.value})

    # ── summarize ────────────────────────────────────────────
    def _summarize(self, ctx: AgentContext, task: Task) -> dict[str, Any]:
        return {
            "task_id": task.id,
            "prompt": task.prompt,
            "task_type": ctx.task_type,
            "status": task.status.value,
            "model": {
                "id": ctx.selected_model_id,
                "name": ctx.selected_model_name,
                "provider": ctx.selected_provider,
            },
            "steps": [
                {"label": s.label, "status": s.status, "detail": s.detail} for s in ctx.steps
            ],
            "artifacts": ctx.artifacts,
            "retrieved_sources": ctx.retrieved_sources,
            "verification": ctx.verification,
            "model_calls": ctx.model_calls,
            "tool_executions": ctx.tool_executions,
            "model_warning": ctx.model_reason if ctx.selected_model_name is None else None,
        }

    # ── handlers ─────────────────────────────────────────────
    def _build_handlers(self, ctx: AgentContext, registry: ToolRegistry) -> ActionHandler:
        ah = ActionHandler()

        async def read_document(context, detail):
            ws = context.workspace_obj
            files = ws.list("input")
            if not files:
                return {"ok": False, "error": "No input document found in workspace."}
            fname = files[0]
            target = ws.dir("input") / fname
            util = self.pipeline.ingest(target)
            context.tool_results["extracted_document"] = {
                "filename": util.filename,
                "content_type": util.content_type,
                "text": util.text,
                "warnings": util.warnings,
            }
            context.documents_accessed.append(fname)
            return {
                "ok": True,
                "filename": util.filename,
                "content_type": util.content_type,
                "text": util.text[:2000],
                "warnings": util.warnings,
            }

        ah.register("read_document", read_document)
        ah.register("perform_ocr", read_document)

        async def extract_findings(context, detail):
            doc = context.tool_results.get("extracted_document", {})
            findings = self._parse_findings(doc.get("text", ""))
            if doc.get("content_type") in ("scanned", "image"):
                vision = await self._extract_findings_vision(context, doc)
                if vision:
                    findings = vision
            context.tool_results["findings"] = findings
            return {"ok": True, "findings": findings}

        ah.register("extract_findings", extract_findings)

        async def search_knowledge(context, detail):
            findings = context.tool_results.get("findings", [])
            query = " ".join(f.get("item", "") for f in findings) or context.prompt
            try:
                res = self.retrieval.search(query, limit=5)
                context.tool_results["sop_results"] = res
                context.retrieved_sources = res["results"]
                return {"ok": True, "results": res["results"]}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": f"RAG search failed: {exc}"}

        ah.register("search_knowledge", search_knowledge)

        async def analyze_findings(context, detail):
            analysis = await self._model_analysis(context)
            context.tool_results["analysis"] = analysis
            return {"ok": True, "analysis": analysis}

        ah.register("analyze_findings", analyze_findings)
        ah.register("analyze", analyze_findings)
        ah.register("answer", analyze_findings)

        async def generate_docx(context, detail):
            ws = context.workspace_obj
            findings = context.tool_results.get("findings", [])
            sop = context.tool_results.get("sop_results", {}).get("results", [])
            sop_refs = [f"{r.get('document_name')} §{r.get('section') or '?'}" for r in sop] or [
                "Maintenance SOP"
            ]
            machine_id = self._machine_id(context)
            date = "2026-08-20"
            recommendation = self._recommendation(findings)
            analysis = context.tool_results.get("analysis", "")
            if analysis and ("approve" in analysis.lower() or "corrective" in analysis.lower()):
                recommendation = analysis.strip().splitlines()[0]
            out = ws.dir("output") / "approval_note.docx"
            make_approval_note(
                out,
                machine_id=machine_id,
                date=date,
                findings=findings,
                sop_references=sop_refs,
                recommendation=recommendation,
            )
            context.artifacts.append(
                {"name": "approval_note.docx", "kind": "docx", "path": str(out)}
            )
            return {"ok": True, "artifact": str(out), "kind": "docx", "name": "approval_note.docx"}

        ah.register("generate_docx", generate_docx)

        async def verify_document(context, detail):
            from agent.verifier import Verifier

            verifier = Verifier()
            checks: list[dict] = []
            passed = True
            for art in context.artifacts:
                if art.get("kind") == "docx":
                    res = verifier.verify_docx_file(
                        Path(art["path"]),
                        required_paragraphs=["Findings", "Approval"],
                    )
                    checks.append(res.to_dict())
                    if not res.passed:
                        passed = False
            context.verification = {"passed": passed, "items": checks}
            return {"ok": True, "verification": context.verification}

        ah.register("verify_document", verify_document)
        ah.register("verify_result", verify_document)

        # ── code handlers ────────────────────────────────────
        async def generate_code(context, detail):
            code = await self._model_code(context)
            context.tool_results["code"] = code
            return {"ok": True, "code": code}

        ah.register("generate_code", generate_code)

        async def execute_code(context, detail):
            code = context.tool_results.get("code", "")
            result = await registry.execute("execute_code", context, code=code)
            context.tool_results["exec_result"] = result["result"]
            return result["result"]

        ah.register("execute_code", execute_code)

        async def run_tests(context, detail):
            code = context.tool_results.get("code", "")
            tests = context.tool_results.get("tests", "")
            result = await registry.execute("run_tests", context, code=code, tests=tests)
            context.tool_results["test_result"] = result["result"]
            return result["result"]

        ah.register("run_tests", run_tests)

        return ah

    # ── deterministic helpers ────────────────────────────────
    async def _generate(
        self,
        context: AgentContext,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        images: list[str] | None = None,
    ) -> str:
        """Invoke the selected model through the provider abstraction.

        Records every real inference call on context.model_calls. Returns ''
        (caller falls back to a deterministic path) when no model is selected
        or the provider is unreachable — inference is never fatal.
        """
        model = context.selected_model_name
        if not model:
            return ""
        try:
            response = await self.registry.provider.generate(
                GenerationRequest(
                    model=model,
                    prompt=prompt,
                    system=system,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    images=images,
                )
            )
            context.model_calls += 1
            return response.text.strip()
        except Exception as exc:  # noqa: BLE001
            context.model_reason = f"LLM call failed, used fallback: {exc}"
            return ""

    async def _model_analysis(self, context) -> str:
        findings = context.tool_results.get("findings", [])
        sop = context.tool_results.get("sop_results", {}).get("results", [])
        lines = [
            f"- {f.get('item')} ({f.get('status')}): {f.get('remark') or 'no remark'}"
            for f in findings
        ] or ["(no findings parsed)"]
        sop_refs = [f"{r.get('document_name')} §{r.get('section') or '?'}" for r in sop]
        prompt = (
            "You are a maintenance inspection analyst. Below are extracted findings "
            "and relevant maintenance SOP references.\n\n"
            f"Inspection findings:\n{chr(10).join(lines)}\n\n"
            f"SOP references:\n{chr(10).join(sop_refs) if sop_refs else '(none retrieved)'}\n\n"
            "Write a concise approval-note analysis (1-3 sentences): how many items "
            "passed/failed, whether corrective maintenance is required, and the "
            "recommendation (approve, or corrective maintenance required)."
        )
        text = await self._generate(
            context, prompt, system="You are a concise engineering analyst.", max_tokens=300
        )
        return text or self._analyze(context)

    async def _model_code(self, context) -> str:
        prompt = (
            "Write a complete, standalone Python program that satisfies this request. "
            "Return only the code, no markdown fences, no explanations.\n\n"
            f"Request: {context.prompt}"
        )
        text = await self._generate(
            context, prompt, system="You are a senior Python engineer.", max_tokens=1000
        )
        return text or self._default_code(context.prompt)

    async def _extract_findings_vision(self, context, doc: dict) -> list[dict]:
        """Structure findings from a scanned/image document with the vision model.

        OCR text of tables loses row/column layout, so for scanned inputs the
        vision model reads the rendered page and returns structured findings.
        Tolerates either a JSON array or a markdown table in the reply. Returns
        [] (caller uses the deterministic parser) on any failure.
        """
        import base64
        import io

        if not context.selected_model_name:
            return []
        try:
            ws = context.workspace_obj
            fname = context.documents_accessed[-1] if context.documents_accessed else None
            source = (ws.dir("input") / fname) if fname else None
            if source is None or not source.is_file():
                return []
            from multimodal.images import load_image, render_pdf_pages

            if source.suffix.lower() == ".pdf":
                images = render_pdf_pages(source, max_pages=1)
                page = images[0] if images else None
            else:
                page = load_image(source)
            if page is None:
                return []
            buf = io.BytesIO()
            page.convert("RGB").save(buf, format="JPEG", quality=90)
            b64 = base64.b64encode(buf.getvalue()).decode()

            ocr_hint = doc.get("text", "")[:1500]
            prompt = (
                "You are reading a page from an inspection report (noisy local OCR "
                "text of the same page is included below).\n"
                f"OCR TEXT:\n{ocr_hint or '(empty)'}\n\n"
                "Return the checklist table rows ONLY, with columns item, status "
                '(PASS or FAIL), remark. Either a JSON array of {"item":..., '
                '"status":..., "remark":...} objects, or a markdown table. '
                "No prose, no markdown fences."
            )
            text = await self._generate(
                context,
                prompt,
                system="You are a precise table-extraction model.",
                max_tokens=600,
                images=[b64],
            )
            if not text:
                return []
            rows = self._json_rows(text) or self._table_rows(text)
            return rows
        except Exception as exc:  # noqa: BLE001
            context.model_reason = f"Vision extraction skipped, used OCR parse: {exc}"
            return []

    @staticmethod
    def _json_rows(text: str) -> list[dict]:
        """Parse a JSON array of {item, status, remark} objects."""
        import json

        start, end = text.find("["), text.rfind("]")
        if start < 0 or end <= start:
            return []
        try:
            payload = json.loads(text[start : end + 1])
        except (json.JSONDecodeError, ValueError):
            return []
        rows: list[dict] = []
        if not isinstance(payload, list):
            return rows
        for row in payload:
            if not isinstance(row, dict):
                continue
            item = str(row.get("item", "")).strip()
            if not item:
                continue
            status_raw = str(row.get("status", "")).upper()
            rows.append(
                {
                    "item": item,
                    "status": "Fail" if status_raw.startswith("FAIL") else "Pass",
                    "remark": str(row.get("remark", "")).strip(),
                }
            )
        return rows

    @staticmethod
    def _table_rows(text: str) -> list[dict]:
        """Parse a markdown/pipe table with an item|status|remark layout."""
        rows: list[dict] = []
        skip = {"checklist item", "item", "status", "remark"}
        for line in text.splitlines():
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            status_idx = next(
                (
                    i
                    for i, c in enumerate(cells)
                    if c.upper() in ("PASS", "FAIL", "PASSED", "FAILED")
                ),
                -1,
            )
            if status_idx < 0:
                continue
            item = cells[status_idx - 1].strip("*- ") if status_idx > 0 else ""
            remark = cells[status_idx + 1].strip() if status_idx + 1 < len(cells) else ""
            if not item or item.lower() in skip:
                continue
            rows.append(
                {
                    "item": item,
                    "status": "Fail" if cells[status_idx].upper().startswith("FAIL") else "Pass",
                    "remark": remark,
                }
            )
        return rows

    @staticmethod
    def _parse_findings(text: str) -> list[dict]:
        """Extract inspection findings from digital text layers and OCR output.

        Digital PDFs keep each line as "item STATUS remark"; OCR of scanned
        tables often drops the status onto its own line ("item" / "FAIL" /
        "remark") because coordinates are lost. Handle both layouts.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        findings: list[dict] = []
        consumed: set[int] = set()
        status_tokens = ("FAILED", "PASSED", "FAIL", "PASS")

        # Layout A — status on its own line (OCR tables): prev line = item,
        # next line = remark.
        n = len(lines)
        for i, line in enumerate(lines):
            if line.upper() in status_tokens:
                item = ""
                if i > 0 and (i - 1) not in consumed:
                    item = lines[i - 1]
                    consumed.add(i - 1)
                remark = ""
                if i + 1 < n:
                    remark = lines[i + 1]
                    consumed.add(i + 1)
                if not item:
                    item = f"Item {len(findings) + 1}"
                findings.append(
                    {
                        "item": item,
                        "status": "Fail" if line.upper().startswith("FAIL") else "Pass",
                        "remark": remark,
                    }
                )
                consumed.add(i)

        # Layout B — inline "item STATUS remark" (digital text layers).
        for idx, line in enumerate(lines):
            if idx in consumed:
                continue
            upper = line.upper()
            for token in status_tokens:
                pos = upper.find(token)
                if pos < 0:
                    continue
                item = line[:pos].strip(" -:").strip()
                if not item:
                    continue
                remark = line[pos + len(token) :].strip(" -:").strip()
                findings.append(
                    {
                        "item": item,
                        "status": "Fail" if token.startswith("FAIL") else "Pass",
                        "remark": remark,
                    }
                )
                consumed.add(idx)
                break

        # Drop duplicates (same item/status seen twice), keep first.
        seen: set[tuple] = set()
        unique: list[dict] = []
        for f in findings:
            key = (f["item"].lower(), f["status"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        return unique

    @staticmethod
    def _machine_id(context) -> str:
        doc = context.tool_results.get("extracted_document", {}).get("text", "")
        for line in doc.splitlines():
            if "machine" in line.lower() and ":" in line:
                return line.split(":", 1)[1].strip()
        return "MC-UNKNOWN"

    @staticmethod
    def _recommendation(findings: list[dict]) -> str:
        failed = [f for f in findings if f.get("status", "").upper() == "FAIL"]
        if failed:
            return (
                "Perform corrective maintenance on the failed items ("
                + ", ".join(f["item"] for f in failed)
                + ") and re-inspect before approving return to service."
            )
        return "No corrective action required; continue normal operation."

    def _analyze(self, context) -> str:
        findings = context.tool_results.get("findings", [])
        sop = context.tool_results.get("sop_results", {}).get("results", [])
        failed = [f for f in findings if f.get("status", "").upper() == "FAIL"]
        base = f"Inspection analysis: {len(findings)} items checked, {len(failed)} failed."
        if sop:
            base += f" Relevant SOP references retrieved: {len(sop)}."
        if context.selected_model_name:
            base += f" (model {context.selected_model_name})"
        else:
            base += " (no local model configured; deterministic analysis used)"
        return base

    @staticmethod
    def _default_code(prompt: str) -> str:
        return (
            "# Generated solution stub.\n"
            "def solve():\n"
            "    return 'implement me'\n\n"
            "if __name__ == '__main__':\n"
            "    print(solve())\n"
        )
