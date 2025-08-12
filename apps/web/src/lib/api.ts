import { z } from 'zod';

import {
  CreateRunInput,
  type CreateRunInputT,
  RunSchema,
  RunsPageSchema,
  RunsSchema,
  type UpdateRunInputT,
} from '@/contracts/run';
import { request, requestRaw } from '@/lib/http';

import { components } from './api-types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://127.0.0.1:8000';

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const headers = new Headers(init.headers || {});
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json');
  if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `Request failed: ${res.status}`);
  }
  const ct = res.headers.get('content-type') || '';
  return (ct.includes('application/json') ? res.json() : (undefined as unknown)) as T;
}

export type LeadOut = components['schemas']['LeadOut'];
export type TaskOut = components['schemas']['TaskOut'];
export type LeadUpdate = components['schemas']['LeadUpdate'];
export type TaskUpdate = components['schemas']['TaskUpdate'];
export type AgentRunRequest = components['schemas']['AgentRunRequest'];
export type ArtifactOut = components['schemas']['ArtifactOut'];

// Example typed API using Zod schema (used by React Query + tests with MSW)
export function fetchRuns(params?: {
  page?: number;
  pageSize?: number;
  status?: 'queued' | 'running' | 'failed' | 'success';
}): Promise<{ kind: 'list'; data: z.infer<typeof RunsSchema> } | { kind: 'page'; data: z.infer<typeof RunsSchema>; page: number; pageSize: number; total: number }> {
  const base = `${process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || ''}/api/runs`;
  const qs = new URLSearchParams();
  if (params?.page) qs.set('page', String(params.page));
  if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
  if (params?.status) qs.set('status', params.status);
  const url = `${base}${qs.toString() ? `?${qs}` : ''}`;
  if (!params?.page && !params?.pageSize) {
    return request(url, { method: 'GET' }, RunsSchema).then(list => ({ kind: 'list', data: list }));
  }
  return request(url, { method: 'GET' }, RunsPageSchema).then(page => ({ kind: 'page', ...page }));
}

export const createRun = (input: CreateRunInputT) =>
  request(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || ''}/api/runs`,
    { method: 'POST', body: JSON.stringify(CreateRunInput.parse(input)) },
    RunSchema,
  );

export const updateRun = (id: string, patch: UpdateRunInputT) =>
  request(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || ''}/api/runs/${id}`,
    { method: 'PATCH', body: JSON.stringify(patch) },
    RunSchema,
  );

export const deleteRun = (id: string) =>
  requestRaw(
    `${process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || ''}/api/runs/${id}`,
    { method: 'DELETE' },
  );
