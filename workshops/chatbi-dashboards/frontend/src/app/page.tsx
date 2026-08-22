"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { join } from "@/lib/api";

export default function Landing() {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const res = await join(code.trim(), name.trim());
      router.push(`/workshop/${res.workshop_code}`);
    } catch (e: any) {
      setErr(e.message.includes("404") ? "Workshop code not found" : e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-8">
        <h1 className="text-2xl font-bold mb-1 text-white">ChatBI Workshop</h1>
        <p className="text-slate-400 mb-6 text-sm">Enter your workshop code and name to join.</p>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-300">Workshop code</label>
            <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="ECOM2026"
              className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-100 placeholder-slate-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-500" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-300">Your name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ada"
              className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-100 placeholder-slate-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-500" required />
          </div>
          {err && <p className="text-sm text-red-400">{err}</p>}
          <button disabled={busy} className="w-full rounded-lg bg-white text-slate-900 py-2 font-medium hover:bg-slate-200 disabled:opacity-50">
            {busy ? "Joining..." : "Join workshop"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slate-500">
          Organizer? <a href="/admin" className="underline text-slate-300 hover:text-white">Open admin</a>
        </p>
      </div>
    </main>
  );
}
