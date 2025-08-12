import { CreateRunInput, RunSchema, RunsSchema } from '@/contracts/run';
import * as db from '@/server/db/runs.repo.prisma';
import * as mem from '@/server/db/runs.store';

const repo: typeof mem = process.env.DATABASE_URL ? (db as unknown as typeof mem) : mem;

export async function listRuns() {
  const data = await repo.list();
  return RunsSchema.parse(data);
}

export async function createRun(raw: unknown) {
  const input = CreateRunInput.parse(raw);
  const created = await repo.create({ title: input.title });
  return RunSchema.parse(created);
}

export async function updateRun(id: string, patch: Partial<unknown>) {
  const updated = await repo.update(id, patch as Record<string, unknown>);
  return RunSchema.parse(updated);
}

export async function deleteRun(id: string) {
  await repo.remove(id);
  return { ok: true } as const;
}

export async function listRunsFlexible(params?: {
  page?: number;
  pageSize?: number;
  status?: 'queued' | 'running' | 'failed' | 'success';
}) {
  if (!params?.page && !params?.pageSize) {
    return repo.list();
  }
  const page = Math.max(1, Number(params.page || 1));
  const pageSize = Math.max(1, Number(params.pageSize || 10));
  // mem repo may not implement listPaged; DB repo does. For mem, fallback to slice.
  const withPaged = repo as unknown as { listPaged?: (args: { page: number; pageSize: number; status?: 'queued' | 'running' | 'failed' | 'success' }) => Promise<unknown> };
  if (typeof withPaged.listPaged === 'function') {
    return withPaged.listPaged({ page, pageSize, status: params?.status });
  }
  const all = await repo.list();
  const start = (page - 1) * pageSize;
  const data = all.slice(start, start + pageSize);
  return { data, page, pageSize, total: all.length };
}
