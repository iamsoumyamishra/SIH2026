"use client";

import { useEffect, useState } from "react";
import { ScrollText, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

export default function AuditPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      setRows(await api.listAudit(150));
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
          <h1 className="text-xl font-semibold text-white">Audit Trail</h1>
          <p className="text-sm text-slate-400">
            Non-sensitive trail of agent runs, tools, models, and artifacts.
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

      <div className="overflow-x-auto rounded-xl border border-brand-900 bg-panel">
        <table className="w-full text-sm">
          <thead className="border-b border-brand-900 text-left text-xs text-slate-400">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Task</th>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Tool</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Artifact</th>
              <th className="px-4 py-3">Verify</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-slate-500">
                  No audit entries yet.
                </td>
              </tr>
            )}
            {rows.map((e) => (
              <tr key={e.id} className="border-b border-sovereignbg align-top">
                <td className="px-4 py-3 text-slate-400">{e.id}</td>
                <td className="px-4 py-3 text-slate-300">{e.task_id ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400">
                  {e.timestamp ? new Date(e.timestamp).toLocaleString() : "—"}
                </td>
                <td className="px-4 py-3 text-slate-200">{e.action}</td>
                <td className="px-4 py-3 text-slate-300">{e.model_selected || "—"}</td>
                <td className="px-4 py-3 text-slate-300">{e.tool_name || "—"}</td>
                <td className="px-4 py-3 text-slate-300">
                  {e.tool_result_status || "—"}
                </td>
                <td className="px-4 py-3 text-slate-300">{e.artifact_generated || "—"}</td>
                <td className="px-4 py-3">
                  {e.verification_status ? (
                    <span
                      className={`rounded px-2 py-0.5 text-[11px] ${
                        e.verification_status === "passed"
                          ? "bg-emerald-900/40 text-emerald-300"
                          : "bg-amber-900/40 text-amber-300"
                      }`}
                    >
                      {e.verification_status}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
