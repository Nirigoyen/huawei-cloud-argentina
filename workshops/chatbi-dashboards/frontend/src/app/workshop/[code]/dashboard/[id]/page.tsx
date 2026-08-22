"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import Link from "next/link";
import type { Layout } from "react-grid-layout";
import { getDashboard, deleteDashboard, updateItemLayout, deleteItem, type Dashboard } from "@/lib/api";
import { DashboardGrid } from "@/components/dashboard/DashboardGrid";

export default function DashboardBuilder({ params }: { params: Promise<{ code: string; id: string }> }) {
  const { code, id } = use(params);
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [saving, setSaving] = useState(false);

  function refresh() {
    getDashboard(id).then(setDash).catch(() => {});
  }

  useEffect(() => {
    refresh();
  }, [id]);

  async function saveLayout(layout: Layout) {
    if (!dash) return;
    setSaving(true);
    await Promise.all(
      layout.map((l) =>
        updateItemLayout(dash.id, l.i, { x: l.x, y: l.y, w: l.w, h: l.h }).catch(() => {})
      )
    );
    setSaving(false);
  }

  async function removeItem(itemId: string) {
    if (!dash) return;
    await deleteItem(dash.id, itemId);
    refresh();
  }

  async function removeDashboard() {
    if (!dash || !confirm("Delete this dashboard?")) return;
    await deleteDashboard(dash.id);
    window.location.href = `/workshop/${code}`;
  }

  if (!dash) return <main className="p-6 text-slate-300">Loading…</main>;

  return (
    <main className="min-h-screen p-6">
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Link href={`/workshop/${code}`} className="text-sm text-slate-400 hover:text-white hover:underline">← Back</Link>
          <h1 className="text-xl font-bold text-white">{dash.name}</h1>
          {saving && <span className="text-xs text-slate-500">saving…</span>}
        </div>
        <button onClick={removeDashboard} className="text-sm text-red-400 hover:text-red-300 hover:underline">Delete dashboard</button>
      </header>

      {dash.items.length === 0 ? (
        <p className="text-slate-500 text-sm">Empty dashboard. Add charts from the chat, then arrange them here.</p>
      ) : (
        <div className="bg-slate-900 rounded-2xl p-4 border border-slate-800">
          <DashboardGrid items={dash.items} onSaveLayout={saveLayout} onDeleteItem={removeItem} />
        </div>
      )}
    </main>
  );
}
