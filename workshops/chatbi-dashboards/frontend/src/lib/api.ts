"use client";

export const API = process.env.NEXT_PUBLIC_API_URL || "/api";

// ---- Types ----
export interface Workshop { id: string; name: string; code: string; has_source: boolean; }
export interface Column { name: string; type: string; }
export interface Model { name: string; description?: string; table_reference: any; primary_key?: string; columns: Column[]; }
export interface Relationship { name: string; models: string[]; join_type: string; condition: string; }
export interface Thread { id: string; title: string; }
export interface Message { id: string; role: string; content?: string; sql?: string; chart_spec?: any; }
export interface Item { id: string; title: string; sql?: string; chart_spec?: any; layout: any; }
export interface Dashboard { id: string; name: string; items: Item[]; }

async function j<T>(res: Promise<Response> | Response): Promise<T> {
  const r = await res;
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

// ---- Workshops / setup (organizer) ----
export const createWorkshop = (name: string, code: string) =>
  j<Workshop>(fetch(`${API}/workshops`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ name, code }) }));

export const getWorkshop = (code: string) => j<Workshop>(fetch(`${API}/workshops/${code}`, { credentials: "include" }));

export const setupSource = (workshopId: string, src: any) =>
  j<{ models: Model[]; relationships: Relationship[] }>(fetch(`${API}/workshops/${workshopId}/setup/source`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ ...src, schema: src.schema ?? "public" }) }));

export const listModels = (workshopId: string) => j<Model[]>(fetch(`${API}/workshops/${workshopId}/setup/models`, { credentials: "include" }));
export const listRelationships = (workshopId: string) => j<Relationship[]>(fetch(`${API}/workshops/${workshopId}/setup/relationships`, { credentials: "include" }));

export const getGallery = (code: string) =>
  j<{ workshop: Workshop; participants: { id: string; name: string; dashboards: Dashboard[] }[] }>(fetch(`${API}/workshops/${code}/gallery`, { credentials: "include" }));

// ---- Participants ----
export const join = (code: string, name: string) =>
  j<{ participant_id: string; workshop_id: string; workshop_name: string; workshop_code: string }>(fetch(`${API}/participants/join`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ code, name }) }));

// ---- Chat ----
export const listThreads = () => j<Thread[]>(fetch(`${API}/chat/threads`, { credentials: "include" }));
export const createThread = (title = "New chat") => j<Thread>(fetch(`${API}/chat/threads`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ title }) }));
export const listMessages = (tid: string) => j<Message[]>(fetch(`${API}/chat/threads/${tid}/messages`, { credentials: "include" }));

export async function streamChat(threadId: string, content: string, onEvent: (ev: any) => void) {
  const res = await fetch(`${API}/chat/threads/${threadId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ content }),
  });
  if (!res.ok || !res.body) throw new Error(`chat failed: ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      if (part.startsWith("data: ")) {
        try { onEvent(JSON.parse(part.slice(6))); } catch { /* skip */ }
      }
    }
  }
}

// ---- Dashboards ----
export const listDashboards = () => j<Dashboard[]>(fetch(`${API}/me/dashboards`, { credentials: "include" }));
export const createDashboard = (name = "Untitled dashboard") => j<Dashboard>(fetch(`${API}/me/dashboards`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ name }) }));
export const getDashboard = (id: string) => j<Dashboard>(fetch(`${API}/me/dashboards/${id}`, { credentials: "include" }));
export const deleteDashboard = (id: string) => fetch(`${API}/me/dashboards/${id}`, { method: "DELETE", credentials: "include" });
export const addItem = (did: string, item: any) => j<Item>(fetch(`${API}/me/dashboards/${did}/items`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify(item) }));
export const updateItemLayout = (did: string, itemId: string, layout: any) => j<Item>(fetch(`${API}/me/dashboards/${did}/items/${itemId}`, { method: "PUT", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ layout }) }));
export const deleteItem = (did: string, itemId: string) => fetch(`${API}/me/dashboards/${did}/items/${itemId}`, { method: "DELETE", credentials: "include" });
