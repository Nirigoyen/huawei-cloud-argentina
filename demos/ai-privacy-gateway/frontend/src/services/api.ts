import type { ProcessRequest, ProcessResponse } from '../types';

const API_BASE = '/api';

export async function processPrompt(prompt: string): Promise<ProcessResponse> {
  const body: ProcessRequest = { prompt };

  const response = await fetch(`${API_BASE}/process_prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
