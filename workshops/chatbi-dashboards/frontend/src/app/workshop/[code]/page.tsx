"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import {
  getWorkshop,
  listDashboards,
  createDashboard,
  type Workshop,
  type Dashboard,
} from "@/lib/api";
import { ChatPanel } from "@/components/chat/ChatPanel";

export default function WorkshopHome({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const [workshop, setWorkshop] = useState<Workshop | null>(null);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);

  function refresh() {
    listDashboards()
      .then(setDashboards)
      .catch(() => {});
  }

  useEffect(() => {
    getWorkshop(code)
      .then(setWorkshop)
      .catch(() => {});
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [code]);

  async function newDashboard() {
    const d = await createDashboard("Untitled dashboard");
    setDashboards((x) => [...x, d]);
  }

  return (
    <main className="min-h-screen p-6">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-white">{workshop?.name || "Workshop"}</h1>
          <p className="text-sm text-slate-400">Code: {code}</p>
        </div>
        <Link href="/" className="text-sm text-slate-400 hover:text-white hover:underline">
          Leave
        </Link>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
        <ChatPanel />

        <aside className="space-y-3">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-semibold text-slate-100">My dashboards</h2>
              <button
                onClick={newDashboard}
                className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
              >
                + New
              </button>
            </div>
            <ul className="space-y-1">
              {dashboards.map((d) => (
                <li key={d.id}>
                  <Link
                    href={`/workshop/${code}/dashboard/${d.id}`}
                    className="block text-sm px-2 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200"
                  >
                    {d.name} <span className="text-slate-500">({d.items.length})</span>
                  </Link>
                </li>
              ))}
              {!dashboards.length && (
                <li className="text-sm text-slate-500 px-2 py-1">
                  No dashboards yet. Add charts from chat.
                </li>
              )}
            </ul>
          </div>
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-4 text-sm text-slate-400">
            <p className="font-semibold text-slate-200 mb-1">How to compete</p>
            <p>
              Ask questions in chat, add the resulting charts to a dashboard, arrange them, and
              build the most insightful view. Judges will review dashboards from the admin gallery.
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
