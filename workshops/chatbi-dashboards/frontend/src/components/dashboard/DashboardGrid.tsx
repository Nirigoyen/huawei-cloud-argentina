"use client";

import { useEffect, useRef } from "react";
import GridLayout, { WidthProvider } from "react-grid-layout/legacy";
import type { Layout } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { ChartAnswer } from "@/components/chat/ChartAnswer";
import type { Item } from "@/lib/api";

const Grid = WidthProvider(GridLayout);

export function DashboardGrid({
  items,
  onSaveLayout,
  onDeleteItem,
}: {
  items: Item[];
  onSaveLayout: (layout: Layout) => void;
  onDeleteItem: (id: string) => void;
}) {
  const layout: Layout = items.map((it) => ({
    i: it.id,
    x: it.layout.x ?? 0,
    y: it.layout.y ?? 0,
    w: it.layout.w ?? 6,
    h: it.layout.h ?? 4,
    minW: 2,
    minH: 2,
  }));
  const mounted = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latest = useRef<Layout>(layout);

  useEffect(() => {
    mounted.current = true;
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  function onLayoutChange(next: Layout) {
    latest.current = next;
    if (!mounted.current) return;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => onSaveLayout(latest.current), 600);
  }

  return (
    <Grid
      layout={layout}
      cols={12}
      rowHeight={40}
      margin={[12, 12]}
      containerPadding={[0, 0]}
      onLayoutChange={onLayoutChange}
      draggableHandle=".drag-handle"
      compactType="vertical"
    >
      {items.map((it) => (
        <div
          key={it.id}
          className="border border-slate-800 rounded-xl bg-slate-900 p-3 overflow-hidden flex flex-col"
        >
          <div className="drag-handle flex items-center justify-between mb-2 cursor-move">
            <span className="text-sm font-medium truncate text-slate-100">
              {it.title}
            </span>
            <button
              onClick={() => onDeleteItem(it.id)}
              className="text-slate-500 hover:text-red-400 text-sm ml-2"
            >
              ×
            </button>
          </div>
          <div className="flex-1 overflow-hidden min-h-0 relative">
            {it.chart_spec ? (
              <ChartAnswer spec={it.chart_spec} fill />
            ) : (
              <p className="text-xs text-slate-500">No chart</p>
            )}
          </div>
        </div>
      ))}
    </Grid>
  );
}
