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
    ) -> None:
        self._db = db
        self.bus = bus or get_event_bus()
        self.pipeline = pipeline or DocumentPipeline()
        self.retrieval = retrieval or RetrievalService()

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
                {"label": s.label, "status": s.status, "detail": s.detail}
                for s in ctx.steps
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
            context.tool_results["analysis"] = self._analyze(context)
            return {"ok": True, "analysis": context.tool_results["analysis"]}
        ah.register("analyze_findings", analyze_findings)
        ah.register("analyze", analyze_findings)
        ah.register("answer", analyze_findings)

        async def generate_docx(context, detail):
            ws = context.workspace_obj
            findings = context.tool_results.get("findings", [])
            sop = context.tool_results.get("sop_results", {}).get("results", [])
            sop_refs = [
                f"{r.get('document_name')} §{r.get('section') or '?'}" for r in sop
            ] or ["Maintenance SOP"]
            machine_id = self._machine_id(context)
            date = "2026-08-20"
            recommendation = self._recommendation(findings)
            out = ws.dir("output") / "approval_note.docx"
            make_approval_note(
                out, machine_id=machine_id, date=date,
                findings=findings, sop_references=sop_refs,
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
            context.tool_results["code"] = self._default_code(context.prompt)
            return {"ok": True, "code": context.tool_results["code"]}
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
    @staticmethod
    def _parse_findings(text: str) -> list[dict]:
        findings: list[dict] = []
        for line in text.splitlines():
            upper = line.upper()
            status = None
            for token in ("FAIL", "PASS"):
                if token in upper:
                    status = token
                    break
            if not status:
                continue
            # heuristic: item = leading tokens before status, remark = after
            parts = line.split(status, 1)
            item = parts[0].strip(" -:").strip()
            remark = parts[1].strip() if len(parts) > 1 else ""
            if item:
                findings.append({"item": item, "status": status.title(), "remark": remark})
        return findings

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
