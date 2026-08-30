"use client";

import { useEffect, useState } from "react";
import { Package, RefreshCw, Download } from "lucide-react";
import { api, downloadArtifact } from "@/lib/api";

export default function ArtifactsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      const tasks = await api.listTasks();
      const recent = tasks.slice(0, 10);
      const rows = await Promise.all(
        recent.map(async (t) => {
          try {
            return await api.taskDetail(t.id);
          } catch {
            return null;
          }
        })
      );
      setRows(rows.filter(Boolean).filter((r) => r.artifacts?.length));
    } catch (err: any) {
      setMsg(err.message);
    }
  }
  useEffect(() => {
    load();
  }, []);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Artifacts</h1>
          <p className="text-sm text-slate-400">
            Generated deliverables (DOCX, XLSX, PDF, …) with verification status.
          </p>
        </div>
        <button
          onClick={load}
          className="rounded-lg border border-brand-700 p-2 text-slate-300 hover:bg-sovereignbg"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
      {msg && <div className="mb-3 text-sm text-red-300">{msg}</div>}
      {rows.length === 0 && !msg && (
        <p className="text-sm text-slate-500">
          No generated artifacts yet. Run a task to produce one.
        </p>
      )}

      <div className="space-y-3">
        {rows.map((t) => (
          <div key={t.id} className="rounded-xl border border-brand-900 bg-panel">
            <div className="border-b border-sovereignbg px-4 py-2 text-sm text-slate-300">
              Task #{t.id} — <span className="text-slate-400">{t.task_type}</span>{" "}
              <span className="ml-2 text-xs text-slate-500">{t.status}</span>
            </div>
            <div className="p-2">
              {t.artifacts.map((a: any) => (
                <div
                  key={a.name + a.kind}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-sovereignbg/40"
                >
                  <div className="flex items-center gap-2 text-slate-200">
                    <Package className="h-4 w-4 text-brand-500" />
                    {a.name}
                    <span className="text-xs text-slate-500">({a.kind})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-[11px] ${
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
                      <Download className="h-4 w-4" /> download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
