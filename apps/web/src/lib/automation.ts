/**
 * Automation Client SDK
 * Provides a clean interface for submitting automation requests and polling results
 */

export interface AutomationRequest {
  intent: string;
  payload: Record<string, unknown>;
  idempotency_key?: string;
}

export interface AutomationResponse {
  status: 'succeeded' | 'failed' | 'queued' | 'running';
  run_id: string;
  result?: unknown;
  error?: string;
}

export interface RunDetail {
  run_id: string;
  status: 'succeeded' | 'failed' | 'queued' | 'running';
  detail: {
    intent: string;
    result?: unknown;
    error?: string;
    executed?: string[];
  };
  meta?: Record<string, unknown>;
  ts?: number;
}

export interface RecentRuns {
  items: RunDetail[];
}

export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export interface ListRunsParams {
  intent?: string;
  status?: RunStatus;
  from?: string; // ISO
  to?: string; // ISO
  limit?: number;
  cursor?: string;
}

export interface RunSummary {
  id: string;
  intent: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  detail?: unknown;
}

// Base API prefix for client SDK
export const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '';

/**
 * Submit an automation request
 */
export async function submit(
  intent: string,
  payload: Record<string, unknown>,
  idempotency_key?: string,
): Promise<{ run_id: string; status: string }> {
  const request: AutomationRequest = {
    intent,
    payload,
    idempotency_key: idempotency_key || `ui-${intent}-${Date.now()}`,
  };

  const response = await fetch('/automation/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Automation submission failed: ${errorText}`);
  }

  return response.json();
}

/**
 * Get run details by ID
 */
export async function getRun(id: string): Promise<RunDetail> {
  const response = await fetch(`/automation/runs/${id}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch run ${id}: ${errorText}`);
  }

  return response.json();
}

/**
 * Get recent runs
 */
export async function getRecentRuns(limit: number = 10): Promise<RecentRuns> {
  const response = await fetch(`/automation/recent?limit=${limit}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch recent runs: ${errorText}`);
  }

  return response.json();
}

/**
 * Generate a cURL command for debugging
 */
export function generateCurl(intent: string, payload: Record<string, unknown>): string {
  const body = JSON.stringify({ intent, payload, idempotency_key: `debug-${Date.now()}` });
  return `curl -X POST http://127.0.0.1:8000/automation/submit \\
  -H "Content-Type: application/json" \\
  -d '${body}'`;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textArea);
    return success;
  }
}

/**
 * List runs with filtering and pagination
 */
export async function listRuns(
  params: ListRunsParams = {},
  signal?: AbortSignal,
): Promise<RunSummary[]> {
  const filtered = Object.entries(params).filter(([, v]) => v != null) as Array<
    [string, string | number | boolean]
  >;
  const qs = new URLSearchParams(
    filtered.map(([k, v]) => [k, typeof v === 'string' ? v : String(v)]) as [string, string][],
  );
  const res = await fetch(`${BASE}/automation/runs?${qs.toString()}`, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) throw new Error(`listRuns failed: ${res.status}`);
  return res.json();
}

/**
 * Generate a deep link for a run
 */
export function runLink(runId: string, pathname: string): string {
  const url = new URL(pathname, 'http://x'); // base ignored
  url.searchParams.set('runId', runId);
  return url.pathname + '?' + url.searchParams.toString();
}

/**
 * Enhanced polling with exponential backoff
 */
export async function pollRun<T = unknown>(
  runId: string,
  { timeoutMs = 120000, intervalMs = 1500, maxIntervalMs = 6000 } = {},
): Promise<T> {
  const start = Date.now();
  let delay = intervalMs;
  while (true) {
    const r = await getRun(runId);
    if (r.status === 'succeeded') return r.detail?.result as T;
    if (r.status === 'failed') throw new Error(r.detail?.error ?? 'Run failed');
    if (Date.now() - start > timeoutMs) throw new Error('Timeout waiting for run');
    await new Promise(res => setTimeout(res, delay));
    delay = Math.min(Math.round(delay * 1.4), maxIntervalMs); // backoff
  }
}
