"use client";

import { useEffect, useState } from "react";
import { Cpu, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

export default function ModelsPage() {
  const [data, setData] = useState<any[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      const r = await api.listModels();
      setData(r.models);
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
          <h1 className="text-xl font-semibold text-white">Local Models</h1>
          <p className="text-sm text-slate-400">
            Open-weight models routed through the ModelRouter → OllamaProvider.
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

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.length === 0 && (
          <p className="text-sm text-slate-500">No models configured.</p>
        )}
        {data.map((m) => (
          <div key={m.id} className="rounded-xl border border-brand-900 bg-panel p-4">
            <div className="mb-2 flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-brand-500" />
                <div>
                  <div className="font-semibold text-white">{(m.model as string).split(":")[0]}</div>
                  <div className="text-[11px] text-slate-400">
                    role: {m.id} · provider: {m.provider}
                  </div>
                </div>
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                  m.available
                    ? "bg-emerald-900/40 text-emerald-300"
                    : "bg-red-900/40 text-red-300"
                }`}
              >
                {m.available ? "available" : "unavailable"}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {m.capabilities?.map((c: string, i: number) => (
                <span key={i} className="rounded bg-sovereignbg px-2 py-0.5 text-[11px] text-slate-300">
                  {c}
                </span>
              ))}
              {m.vision_support && (
                <span className="rounded bg-sovereignbg px-2 py-0.5 text-[11px] text-slate-300">vision</span>
              )}
              {m.tool_support && (
                <span className="rounded bg-sovereignbg px-2 py-0.5 text-[11px] text-slate-300">tools</span>
              )}
            </div>
            {m.error && !m.available && (
              <div className="mt-2 text-[11px] text-red-300">
                {m.error}
                <span className="ml-1 text-slate-400">
                  (pull with `ollama pull …`)
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
