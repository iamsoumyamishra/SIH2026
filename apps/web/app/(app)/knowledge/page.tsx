"use client";

import { useState } from "react";
import { BookOpen, Search } from "lucide-react";
import { api } from "@/lib/api";

export default function KnowledgePage() {
  const [docId, setDocId] = useState("sop-001");
  const [docName, setDocName] = useState("");
  const [text, setText] = useState("");
  const [section, setSection] = useState("");
  const [ingestMsg, setIngestMsg] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searchMsg, setSearchMsg] = useState("");

  async function ingest(e: React.FormEvent) {
    e.preventDefault();
    setIngestMsg("");
    try {
      const r = await api.ingestKnowledge({
        document_id: docId,
        document_name: docName || docId,
        text,
        section: section || undefined,
      });
      setIngestMsg(`Ingested ${r.chunks} chunks (${r.document_name})`);
      setText("");
    } catch (err: any) {
      setIngestMsg("Failed: " + err.message);
    }
  }

  async function search(e: React.FormEvent) {
    e.preventDefault();
    setSearchMsg("");
    try {
      const r = await api.searchKnowledge(query);
      setResults(r.results || []);
    } catch (err: any) {
      setSearchMsg("Search failed: " + err.message);
    }
  }

  return (
    <div className="grid h-full grid-cols-1 gap-4 p-6 lg:grid-cols-2">
      <div className="rounded-xl border border-brand-900 bg-panel p-4">
        <div className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
          <BookOpen className="h-5 w-5 text-brand-500" /> Local RAG Ingestion
        </div>
        <form onSubmit={ingest} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Document ID" value={docId} set={setDocId} />
            <Field label="Document Name" value={docName} set={setDocName} />
          </div>
          <Field label="Section" value={section} set={setSection} />
          <div>
            <label className="mb-1 block text-xs text-slate-400">Content</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              required
              className="w-full rounded-lg border border-brand-900 bg-sovereignbg px-3 py-2 text-sm text-white outline-none focus:border-brand-600"
            />
          </div>
          <button
            type="submit"
            disabled={!text.trim()}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-50"
          >
            Ingest (embed → local store)
          </button>
          {ingestMsg && <div className="text-sm text-slate-300">{ingestMsg}</div>}
        </form>
      </div>

      <div className="rounded-xl border border-brand-900 bg-panel p-4">
        <div className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
          <Search className="h-5 w-5 text-brand-500" /> Semantic Search
        </div>
        <form onSubmit={search} className="space-y-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. How often is structural inspection required?"
            className="w-full rounded-lg border border-brand-900 bg-sovereignbg px-3 py-2 text-sm text-white outline-none focus:border-brand-600"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-50"
          >
            Search
          </button>
        </form>
        {searchMsg && <div className="mt-2 text-sm text-red-300">{searchMsg}</div>}
        <div className="mt-4 space-y-2">
          {results.map((r: any, i: number) => (
            <div key={i} className="rounded-lg bg-sovereignbg/60 p-3 text-sm">
              <div className="mb-1 flex flex-wrap gap-2 text-[11px] text-slate-400">
                <span className="rounded bg-brand-900 px-2 py-0.5">
                  {r.document_name}
                </span>
                {r.page_number ? (
                  <span>Page {r.page_number}</span>
                ) : null}
                {r.section ? <span>{r.section}</span> : null}
                {typeof r.score === "number" && (
                  <span>score {(r.score as number).toFixed(3)}</span>
                )}
              </div>
              <div className="text-slate-200">{r.text || (r.chunk ?? "")}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  set,
}: {
  label: string;
  value: string;
  set: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-slate-400">{label}</label>
      <input
        value={value}
        onChange={(e) => set(e.target.value)}
        className="w-full rounded-lg border border-brand-900 bg-sovereignbg px-3 py-2 text-sm text-white outline-none focus:border-brand-600"
      />
    </div>
  );
}
