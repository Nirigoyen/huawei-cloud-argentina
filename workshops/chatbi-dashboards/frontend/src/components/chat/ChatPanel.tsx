"use client";

import { useEffect, useRef, useState } from "react";
import {
  listThreads,
  createThread,
  listMessages,
  streamChat,
  listDashboards,
  createDashboard,
  addItem,
  type Thread,
  type Message,
  type Dashboard,
  type ChartSpec,
} from "@/lib/api";
import { ChartAnswer } from "./ChartAnswer";
import { SQLView } from "./SQLView";
import { Markdown } from "./Markdown";

interface StreamMsg {
  role: string;
  content: string;
  thinking?: string;
  sql?: string;
  chart_spec?: ChartSpec;
  data?: unknown;
}

/** Extract a human title from a Vega-Lite spec (DeepSeek sets one). */
function chartTitle(spec: ChartSpec): string {
  if (!spec) return "";
  const t = spec.title;
  if (typeof t === "string") return t;
  if (t && typeof t.text === "string") return t.text;
  return "";
}

export function ChatPanel() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [active, setActive] = useState<Thread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState<StreamMsg | null>(null);
  const [busy, setBusy] = useState(false);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [addError, setAddError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listThreads()
      .then(setThreads)
      .catch(() => {});
    listDashboards()
      .then(setDashboards)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (active)
      listMessages(active.id)
        .then(setMessages)
        .catch(() => {});
  }, [active]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streaming]);

  async function newThread() {
    const t = await createThread();
    setThreads((x) => [t, ...x]);
    setActive(t);
  }

  async function send() {
    if (!input.trim() || busy) return;
    let thread = active;
    if (!thread) {
      thread = await createThread(input.trim().slice(0, 40));
      setThreads((x) => [thread!, ...x]);
      setActive(thread);
    }
    const content = input.trim();
    setInput("");
    setBusy(true);
    setStreaming({ role: "assistant", content: "" });

    await streamChat(thread.id, content, (ev) => {
      setStreaming((s) => {
        if (!s) return s;
        if (ev.type === "thinking")
          return { ...s, thinking: (s.thinking || "") + ev.content };
        if (ev.type === "token")
          return { ...s, content: s.content + ev.content };
        if (ev.type === "sql") return { ...s, sql: ev.content };
        if (ev.type === "data") return { ...s, data: ev.content };
        if (ev.type === "chart") return { ...s, chart_spec: ev.content };
        if (ev.type === "error")
          return { ...s, content: s.content + `\n\n[error: ${ev.content}]` };
        return s;
      });
    });

    setStreaming(null);
    setBusy(false);
    if (thread)
      listMessages(thread.id)
        .then(setMessages)
        .catch(() => {});
  }

  async function addToDashboard(msg: StreamMsg | Message) {
    if (!msg.chart_spec) return;
    setAddError("");
    try {
      const defaultName = chartTitle(msg.chart_spec);
      const title = defaultName || prompt("Name this chart:", "Chart");
      if (!title) return;
      let dash = dashboards[0];
      if (!dash) {
        dash = await createDashboard("From chat");
        setDashboards((x) => [...x, dash!]);
      }
      await addItem(dash.id, {
        title,
        sql: msg.sql,
        chart_spec: msg.chart_spec,
        layout: { x: 0, y: 0, w: 6, h: 4 },
      });
      alert("Added to dashboard");
    } catch (e: unknown) {
      setAddError(e instanceof Error ? e.message : String(e));
    }
  }

  function renderMsg(m: StreamMsg | Message, streamingFlag = false) {
    const isUser = m.role === "user";
    const thinking = (m as StreamMsg).thinking;
    return (
      <div
        key={"id" in m ? m.id : "stream"}
        className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      >
        <div
          className={`max-w-[85%] rounded-2xl px-4 py-3 ${isUser ? "bg-indigo-600 text-white" : "bg-slate-800 border border-slate-700 text-slate-200"}`}
        >
          {/* Collapsible reasoning (only for assistant, only while/after streaming) */}
          {!isUser && thinking && (
            <details className="mb-2 text-xs text-slate-400">
              <summary className="cursor-pointer select-none hover:text-slate-200">
                Thinking…
              </summary>
              <div className="mt-1 opacity-70">
                <Markdown>{thinking}</Markdown>
              </div>
            </details>
          )}
          {m.content && !isUser && (
            <>
              <Markdown>{m.content}</Markdown>
              {streamingFlag && <span className="animate-pulse">▋</span>}
            </>
          )}
          {m.content && isUser && (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {m.content}
            </p>
          )}
          {m.sql && <SQLView sql={m.sql} />}
          {m.chart_spec && (
            <div className="mt-2 overflow-hidden">
              <ChartAnswer spec={m.chart_spec} />
            </div>
          )}
          {!isUser && !streamingFlag && m.chart_spec && (
            <button
              onClick={() => addToDashboard(m)}
              className="mt-2 text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-200"
            >
              + Add to dashboard
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] border border-slate-800 rounded-2xl bg-slate-900 overflow-hidden">
      {/* Threads sidebar */}
      <div className="w-48 border-r border-slate-800 flex flex-col">
        <button
          onClick={newThread}
          className="m-2 text-sm rounded-lg bg-white text-slate-900 py-2 hover:bg-slate-200 font-medium"
        >
          + New chat
        </button>
        <div className="flex-1 overflow-y-auto px-2">
          {threads.map((t) => (
            <button
              key={t.id}
              onClick={() => setActive(t)}
              className={`w-full text-left text-sm px-2 py-1.5 rounded-lg mb-1 text-slate-300 ${active?.id === t.id ? "bg-slate-800 font-medium text-white" : "hover:bg-slate-800/60"}`}
            >
              {t.title}
            </button>
          ))}
        </div>
      </div>
      {/* Messages */}
      <div className="flex-1 flex flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m) => renderMsg(m))}
          {streaming && renderMsg(streaming, true)}
          {!messages.length && !streaming && (
            <p className="text-slate-500 text-sm text-center mt-8">
              Ask a question about the data to get started.
            </p>
          )}
        </div>
        <div className="border-t border-slate-800 p-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask about the data…"
            className="flex-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-100 placeholder-slate-500 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
            disabled={busy}
          />
          <button
            onClick={send}
            disabled={busy || !input.trim()}
            className="rounded-lg bg-white text-slate-900 px-4 py-2 text-sm font-medium hover:bg-slate-200 disabled:opacity-50"
          >
            {busy ? "…" : "Send"}
          </button>
        </div>
        {addError && (
          <p className="text-xs text-red-400 px-3 pb-2">{addError}</p>
        )}
      </div>
    </div>
  );
}
