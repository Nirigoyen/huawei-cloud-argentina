"use client";

import { useState } from "react";
import {
  createWorkshop,
  setupSource,
  getGallery,
  type Workshop,
  type Model,
  type Relationship,
  type Dashboard,
} from "@/lib/api";
import { ChartAnswer } from "@/components/chat/ChartAnswer";

export default function Admin() {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [workshop, setWorkshop] = useState<Workshop | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [rels, setRels] = useState<Relationship[]>([]);
  const [gallery, setGallery] = useState<{ id: string; name: string; dashboards: Dashboard[] }[]>(
    [],
  );
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const [src, setSrc] = useState({
    host: "localhost",
    port: 5432,
    database: "scenario",
    user: "workshop",
    password: "workshop",
    schema: "public",
  });

  async function create() {
    setMsg("");
    try {
      const w = await createWorkshop(name.trim(), code.trim());
      setWorkshop(w);
      setMsg(`Workshop created. Share code ${w.code} with participants.`);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : String(e));
    }
  }

  async function connect() {
    if (!workshop) return;
    setBusy(true);
    setMsg("Introspecting schema + building semantic layer…");
    try {
      const res = await setupSource(workshop.id, src);
      setModels(res.models);
      setRels(res.relationships);
      setMsg(`Connected. ${res.models.length} models, ${res.relationships.length} relationships.`);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadGallery() {
    if (!workshop) return;
    try {
      const g = await getGallery(workshop.code);
      setGallery(g.participants);
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : String(e));
    }
  }

  const inputCls =
    "rounded-lg border border-slate-700 bg-slate-800 text-slate-100 placeholder-slate-500 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500";

  return (
    <main className="min-h-screen p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">Organizer console</h1>

      {/* Step 1: create workshop */}
      <section className="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-4">
        <h2 className="font-semibold mb-3 text-slate-100">1. Create workshop</h2>
        <div className="flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Workshop name"
            className={`flex-1 ${inputCls}`}
          />
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Code (e.g. ECOM2026)"
            className={`w-40 ${inputCls}`}
          />
          <button
            onClick={create}
            disabled={!name || !code}
            className="rounded-lg bg-white text-slate-900 px-4 py-2 text-sm font-medium disabled:opacity-50 hover:bg-slate-200"
          >
            Create
          </button>
        </div>
      </section>

      {/* Step 2: connect + introspect */}
      {workshop && (
        <section className="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-4">
          <h2 className="font-semibold mb-3 text-slate-100">
            2. Connect PostgreSQL &amp; introspect
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
            <input
              value={src.host}
              onChange={(e) => setSrc({ ...src, host: e.target.value })}
              placeholder="host"
              className={inputCls}
            />
            <input
              type="number"
              value={src.port}
              onChange={(e) => setSrc({ ...src, port: +e.target.value })}
              placeholder="port"
              className={inputCls}
            />
            <input
              value={src.database}
              onChange={(e) => setSrc({ ...src, database: e.target.value })}
              placeholder="database"
              className={inputCls}
            />
            <input
              value={src.user}
              onChange={(e) => setSrc({ ...src, user: e.target.value })}
              placeholder="user"
              className={inputCls}
            />
            <input
              value={src.password}
              onChange={(e) => setSrc({ ...src, password: e.target.value })}
              placeholder="password"
              type="password"
              className={inputCls}
            />
            <input
              value={src.schema}
              onChange={(e) => setSrc({ ...src, schema: e.target.value })}
              placeholder="schema"
              className={inputCls}
            />
          </div>
          <button
            onClick={connect}
            disabled={busy}
            className="rounded-lg bg-white text-slate-900 px-4 py-2 text-sm font-medium disabled:opacity-50 hover:bg-slate-200"
          >
            {busy ? "Working…" : "Connect &amp; introspect"}
          </button>
        </section>
      )}

      {/* Step 3: models + relationships */}
      {models.length > 0 && (
        <section className="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-4">
          <h2 className="font-semibold mb-3 text-slate-100">
            3. Semantic layer ({models.length} models, {rels.length} relationships)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1">MODELS</p>
              <ul className="space-y-1">
                {models.map((m) => (
                  <li
                    key={m.name}
                    className="text-sm border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <span className="font-medium">{m.name}</span>{" "}
                    <span className="text-slate-500">
                      ({m.columns.length} cols, pk: {m.primary_key || "—"})
                    </span>
                    {m.description && (
                      <p className="text-xs text-slate-400 mt-0.5">{m.description}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1">RELATIONSHIPS</p>
              <ul className="space-y-1">
                {rels.map((r) => (
                  <li
                    key={r.name}
                    className="text-sm border border-slate-800 rounded-lg px-3 py-2 text-slate-200"
                  >
                    <span className="font-medium">{r.models.join(" → ")}</span>{" "}
                    <span className="text-slate-500">({r.join_type})</span>
                    <p className="text-xs text-slate-400 mt-0.5">{r.condition}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Step 4: gallery */}
      {workshop && (
        <section className="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-100">4. Gallery (judging)</h2>
            <button
              onClick={loadGallery}
              className="text-sm px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
            >
              Refresh
            </button>
          </div>
          {gallery.length === 0 ? (
            <p className="text-sm text-slate-500">
              No participants yet. Share the code{" "}
              <span className="font-mono font-medium text-slate-300">{workshop.code}</span> and the
              join link.
            </p>
          ) : (
            <div className="space-y-4">
              {gallery.map((p) => (
                <div key={p.id} className="border border-slate-800 rounded-xl p-3">
                  <p className="font-medium text-sm mb-2 text-slate-100">{p.name}</p>
                  {p.dashboards.map((d) => (
                    <div key={d.id} className="mb-3">
                      <p className="text-xs text-slate-400 mb-1">
                        {d.name} ({d.items.length} charts)
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {d.items.map((it) => (
                          <div key={it.id} className="border border-slate-800 rounded-lg p-2">
                            <p className="text-xs font-medium mb-1 truncate text-slate-200">
                              {it.title}
                            </p>
                            {it.chart_spec && <ChartAnswer spec={it.chart_spec} />}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {msg && (
        <p className="text-sm text-slate-300 fixed bottom-4 right-4 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 shadow-lg">
          {msg}
        </p>
      )}
    </main>
  );
}
