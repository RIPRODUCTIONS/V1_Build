export type FetchOptions = RequestInit & { retries?: number; retryDelayMs?: number };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || '';

export async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { retries = 2, retryDelayMs = 300, headers, ...rest } = opts;
  let lastErr: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...(headers || {}) },
        ...rest,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (err) {
      lastErr = err;
      if (attempt < retries) await new Promise(r => setTimeout(r, retryDelayMs));
    }
  }
  throw lastErr;
}
