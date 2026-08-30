"use client";

import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Loader2,
  Upload,
  FileText,
  Cpu,
  Wrench,
  Download,
  XCircle,
} from "lucide-react";
import { api, downloadArtifact } from "@/lib/api";

type TimelineItem = {
  id: string;
  type: "step" | "tool" | "done" | "error";
  label?: string;
  status?: string;
  detail?: string;
  name?: string;
  risk?: string;
};

function statusIcon(item: TimelineItem) {
  if (item.type === "error") return <XCircle className="h-4 w-4 text-red-400" />;
  if (item.type === "tool") return <Wrench className="h-4 w-4 text-amber-300" />;
  if (item.type === "done")
    return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  if (item.type === "step") {
    if (item.status === "done")
      return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
    if (item.status === "warning")
      return <XCircle className="h-4 w-4 text-amber-400" />;
    return <Loader2 className="h-4 w-4 animate-spin text-brand-500" />;
  }
  return null;
}

export default function Workspace() {
  const [prompt, setPrompt] = useState(
    "Analyze this inspection report, compare against the maintenance SOP, and generate an approval note."
  );
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [taskId, setTaskId] = useState<number | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [detail, setDetail] = useState<any>(null);
  const esRef = useRef<EventSource | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (listRef.current)
      listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [timeline]);

  useEffect(() => {
    return () => esRef.current?.close();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    setTimeline([]);
    setDetail(null);
    esRef.current?.close();
    try {
      const { task_id } = await api.createTask(prompt, file);
      setTaskId(task_id);
      startStream(task_id);
      refreshDetail(task_id);
    } catch (err: any) {
      setError(err.message || "Failed to submit task");
    } finally {
      setBusy(false);
    }
  }

  function startStream(id: number) {
    const es = new EventSource(api.taskEventsUrl(id));
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setTimeline((prev) => [...prev, { id: data.id || Math.random().toString(), ...data }]);
        if (data.type === "done" || data.type === "error") {
          refreshDetail(id);
        }
      } catch {
        /* ignore keep-alive */
      }
    };
    es.onerror = () => {
      // task likely finished and the stream closed
      es.close();
      refreshDetail(id);
    };
  }

  async function refreshDetail(id: number) {
    try {
      setDetail(await api.taskDetail(id));
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="grid h-full grid-cols-1 gap-4 p-4 lg:grid-cols-2">
      {/* Left: input + request */}
      <div className="space-y-4">
        <div className="rounded-xl border border-brand-900 bg-panel p-4">
          <h2 className="mb-3 text-lg font-semibold text-white">New Task</h2>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-slate-400">Request</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-brand-900 bg-sovereignbg px-3 py-2 text-sm text-white outline-none focus:border-brand-600"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-brand-700 px-3 py-2 text-xs text-slate-300 hover:border-brand-500">
                <Upload className="h-4 w-4" />
                {file ? file.name : "Attach file"}
                <input
                  type="file"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>
              <span className="text-xs text-slate-500">
                e.g. inspection PDF, image, docx
              </span>
            </div>
            {error && (
              <div className="rounded-lg bg-red-900/40 px-3 py-2 text-sm text-red-300">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={busy || !prompt.trim()}
              className="w-full rounded-lg bg-brand-600 py-2 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-50"
            >
              {busy ? "Submitting…" : "Run Agentic Task"}
            </button>
          </form>
        </div>

        {/* Model visibility */}
        <div className="rounded-xl border border-brand-900 bg-panel p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
            <Cpu className="h-4 w-4 text-brand-500" /> Model Visibility
          </div>
          <dl className="space-y-1 text-sm">
            <Row k="Routing" v="Rule-based ModelRouter" />
            <Row k="Provider" v="OllamaProvider" />
            <Row k="Location" v="On-Premise" />
            <Row k="Infrastructure" v="Local-only · no cloud calls" />
          </dl>
        </div>
      </div>

      {/* Right: agent timeline */}
      <div className="flex min-h-0 flex-col rounded-xl border border-brand-900 bg-panel">
        <div className="border-b border-brand-900 px-4 py-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Agent Timeline</h2>
            {taskId ? (
              <span className="rounded-full bg-sovereignbg px-3 py-1 text-xs text-slate-300">
                Task #{taskId}
              </span>
            ) : null}
          </div>
        </div>

        <div
          ref={listRef}
          className="flex-1 space-y-1 overflow-y-auto p-4 text-sm"
        >
          {timeline.length === 0 && !detail && (
            <p className="text-slate-500">
              Submit a task to watch the agent work. Progress streams live.
            </p>
          )}
          {timeline.map((item, i) => (
            <div
              key={item.id || i}
              className="flex items-start gap-3 rounded-lg bg-sovereignbg/60 px-3 py-2"
            >
              <span className="mt-0.5">{statusIcon(item)}</span>
              <div className="min-w-0 flex-1">
                <div className="text-slate-200">
                  {item.type === "tool"
                    ? `Tool: ${item.name}`
                    : item.label}
                </div>
                {item.detail && (
                  <div className="truncate text-xs text-slate-400">
                    {item.detail}
                  </div>
                )}
                {item.risk && (
                  <span className="text-[11px] text-amber-300">
                    risk: {item.risk}
                  </span>
                )}
              </div>
            </div>
          ))}
          {timeline.length > 0 && detail?.status === "EXECUTING" && (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-400">
              <Loader2 className="h-3 w-3 animate-spin" /> Agent executing…
            </div>
          )}
        </div>

        {detail && (
          <div className="border-t border-brand-900 p-4 text-sm">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-xs text-slate-400">Status</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  detail.status === "COMPLETED"
                    ? "bg-emerald-900/40 text-emerald-300"
                    : detail.status === "FAILED"
                    ? "bg-red-900/40 text-red-300"
                    : "bg-amber-900/40 text-amber-300"
                }`}
              >
                {detail.status}
              </span>
            </div>
            {detail.run?.selected_models?.length ? (
              <div className="mb-2 flex items-center gap-2 text-xs text-slate-300">
                <Cpu className="h-3 w-3" /> Model:{" "}
                <span className="text-white">
                  {detail.run.selected_models.join(", ")}
                </span>
              </div>
            ) : null}
            <div className="mb-2 flex flex-wrap gap-1.5">
              {detail.tools?.map((t: any, i: number) => (
                <span
                  key={i}
                  className="flex items-center gap-1 rounded bg-sovereignbg px-2 py-0.5 text-[11px] text-slate-300"
                >
                  <Wrench className="h-3 w-3" /> {t.tool_name}
                </span>
              ))}
            </div>
            {detail.artifacts?.length ? (
              <div>
                <div className="mb-1 flex items-center gap-2 text-xs text-slate-300">
                  <FileText className="h-3 w-3" /> Artifacts
                </div>
                {detail.artifacts.map((a: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded bg-sovereignbg px-3 py-2 text-xs"
                  >
                    <span className="text-slate-200">{a.name}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 ${
                          a.verification_status === "passed"
                            ? "bg-emerald-900/40 text-emerald-300"
                            : "bg-amber-900/40 text-amber-300"
                        }`}
                      >
                        {a.verification_status || "pending"}
                      </span>
                      <button
                        onClick={() =>
                          downloadArtifact(a.id, a.name).catch((err) =>
                            console.error(err)
                          )
                        }
                        className="flex items-center gap-1 text-brand-500 hover:text-brand-400"
                      >
                        <Download className="h-3 w-3" /> download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between border-b border-sovereignbg py-1">
      <dt className="text-slate-400">{k}</dt>
      <dd className="text-slate-200">{v}</dd>
    </div>
  );
}
