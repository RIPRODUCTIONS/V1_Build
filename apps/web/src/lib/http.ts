import { z } from 'zod';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

const defaultHeaders: Record<string, string> = {
  'Content-Type': 'application/json',
};

export class HttpError extends Error {
  status: number;
  body?: unknown;
  name = 'HttpError';
  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export async function request<TSchema extends z.ZodTypeAny>(
  url: string,
  options: RequestInit & { method?: HttpMethod } = {},
  schema: TSchema,
): Promise<z.infer<TSchema>> {
  const res = await fetch(url, {
    headers: { ...defaultHeaders, ...(options.headers || {}) },
    ...options,
  });

  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const body = isJson ? await res.json().catch(() => undefined) : await res.text();

  if (!res.ok) {
    throw new HttpError(`HTTP ${res.status} for ${url}`, res.status, body);
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    const first = parsed.error.issues[0];
    throw new Error(
      `Schema validation failed for ${url}: ${first?.path?.join('.') || ''} ${first?.message}`,
    );
  }
  return parsed.data as z.infer<TSchema>;
}

export async function requestRaw<T = unknown>(
  url: string,
  options: RequestInit & { method?: HttpMethod } = {},
): Promise<T> {
  const res = await fetch(url, {
    headers: { ...defaultHeaders, ...(options.headers || {}) },
    ...options,
  });
  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const body = isJson ? await res.json().catch(() => undefined) : await res.text();
  if (!res.ok) {
    throw new HttpError(`HTTP ${res.status} for ${url}`, res.status, body);
  }
  return body as T;
}
