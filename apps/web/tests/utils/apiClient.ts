// Lightweight API client for Playwright tests
// Uses node-fetch and supports query params + headers

import fetch from 'node-fetch';

type RequestOptions = {
  headers?: Record<string, string>;
  params?: Record<string, string | number | undefined | null>;
};

const API_BASE =
  process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(
    path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`,
  );
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }
  return url.toString();
}

export async function apiGet(path: string, options: RequestOptions = {}) {
  const url = buildUrl(path, options.params);
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  });
  return res;
}
