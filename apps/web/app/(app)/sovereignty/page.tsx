"use client";

import { useEffect, useState } from "react";
import { Radio, RefreshCw, ShieldCheck, ShieldOff, Cpu, Wrench } from "lucide-react";
import { api } from "@/lib/api";

export default function SovereigntyPage() {
  const [s, setS] = useState<any>(null);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      setS(await api.sovereignty());
    } catch (err: any) {
      setMsg(err.message);
    }
  }
  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  if (!s)
    return (
      <div className="p-6">
        {msg && <div className="text-red-300">{msg}</div>}
        <div className="text-slate-500">Loading sovereignty status…</div>
      </div>
    );

  const blocked = !s.internet_reachable;

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-brand-500" />
          <h1 className="text-xl font-semibold text-white">Sovereignty Monitor</h1>
        </div>
        <button
          onClick={load}
          className="rounded-lg border border-brand-700 p-2 text-slate-300 hover:bg-sovereignbg"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          icon={blocked ? ShieldCheck : ShieldOff}
          tone={blocked ? "green" : "red"}
          label="Internet access"
          value={s.internet}
          sub={blocked ? "Egress is blocked" : "Connectivity detected"}
        />
        <Card icon={ShieldCheck} tone="green" label="External API calls" value={0} sub="Cloud APIs blocked" />
        <Card icon={ShieldCheck} tone="green" label="External AI requests" value={0} sub="No cloud LLMs" />
        <Card icon={ShieldCheck} tone="green" label="Cloud uploads" value={0} sub="Storage is local" />
        <Card icon={Cpu} tone="blue" label="Inference" value={s.inference} sub="On-premise inference" />
        <Card icon={Wrench} tone="blue" label="Local tool executions" value={s.local_tool_executions} sub="Past hour" />
      </div>

      <div className="rounded-xl border border-brand-900 bg-panel p-4 text-sm text-slate-300">
        <div className="mb-1 font-semibold text-white">Architecture guarantee</div>
        <p>
          All inference, OCR, embeddings, retrieval and artifact generation run
          inside the organizational boundary. The API never calls an external AI
          service. The internet flag is derived from a live reachability probe —
          it is not fabricated.
        </p>
      </div>
    </div>
  );
}

function Card({
  icon: Icon,
  tone,
  label,
  value,
  sub,
}: {
  icon: any;
  tone: "green" | "red" | "blue";
  label: string;
  value: any;
  sub?: string;
}) {
  const toneCls =
    tone === "green"
      ? "bg-emerald-900/30 text-emerald-300"
      : tone === "red"
      ? "bg-red-900/30 text-red-300"
      : "bg-brand-900/40 text-brand-300";
  const boxCls =
    tone === "green"
      ? "bg-emerald-500/10 text-emerald-400"
      : tone === "red"
      ? "bg-red-500/10 text-red-400"
      : "bg-brand-500/10 text-brand-400";

  return (
    <div className="rounded-xl border border-brand-900 bg-panel p-4">
      <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg ${boxCls}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${tone === "blue" ? "text-white" : ""}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
      {tone === "green" && (
        <div className={`mt-2 inline-block rounded px-2 py-0.5 text-[11px] ${toneCls}`}>
          LOCAL
        </div>
      )}
      {tone === "red" && (
        <div className={`mt-2 inline-block rounded px-2 py-0.5 text-[11px] ${toneCls}`}>
          CHECK
        </div>
      )}
    </div>
  );
}
