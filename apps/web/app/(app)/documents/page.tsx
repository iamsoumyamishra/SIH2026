"use client";

import { useEffect, useState } from "react";
import { FileText, RefreshCw, Upload } from "lucide-react";
import { api } from "@/lib/api";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function load() {
    try {
      setDocs(await api.listDocuments());
    } catch (err: any) {
      setMsg(err.message);
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    setMsg("");
    try {
      await api.uploadDocument(f);
      await load();
    } catch (err: any) {
      setMsg(err.message);
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Documents</h1>
          <p className="text-sm text-slate-400">
            Files uploaded to the local workbench. Contents never leave.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm text-white hover:bg-brand-500">
            <Upload className="h-4 w-4" />
            {busy ? "Uploading…" : "Upload"}
            <input type="file" className="hidden" onChange={upload} />
          </label>
          <button
            onClick={load}
            className="rounded-lg border border-brand-700 p-2 text-slate-300 hover:bg-sovereignbg"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
      {msg && <div className="mb-3 text-sm text-red-300">{msg}</div>}

      <div className="overflow-x-auto rounded-xl border border-brand-900 bg-panel">
        <table className="w-full text-sm">
          <thead className="border-b border-brand-900 text-left text-xs text-slate-400">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Pages</th>
              <th className="px-4 py-3">Preview</th>
            </tr>
          </thead>
          <tbody>
            {docs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                  No documents yet.
                </td>
              </tr>
            )}
            {docs.map((d) => (
              <tr key={d.id} className="border-b border-sovereignbg">
                <td className="flex items-center gap-2 px-4 py-3 text-slate-200">
                  <FileText className="h-4 w-4 text-brand-500" /> {d.filename}
                </td>
                <td className="px-4 py-3 text-slate-300">{d.content_type}</td>
                <td className="px-4 py-3 text-slate-300">{d.page_count}</td>
                <td className="max-w-xs truncate px-4 py-3 text-xs text-slate-500">
                  {d.text_preview || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
