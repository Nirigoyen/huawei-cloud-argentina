"use client";

import { useState } from "react";

export function SQLView({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false);
  if (!sql) return null;
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs text-slate-400 hover:text-slate-200 underline"
      >
        {open ? "Hide SQL" : "View SQL"}
      </button>
      {open && (
        <pre className="mt-1 text-xs bg-slate-950 text-slate-300 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap border border-slate-800">
          {sql}
        </pre>
      )}
    </div>
  );
}
