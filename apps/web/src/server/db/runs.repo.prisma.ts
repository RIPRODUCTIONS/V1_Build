import { CreateRunInput } from '@/contracts/run';

import { prisma } from './prisma';

export async function list() {
  const rows = await prisma.run.findMany({ orderBy: { startedAt: 'desc' } });
  return rows.map(r => ({
    id: r.id,
    title: r.title,
    status: r.status as 'queued' | 'running' | 'failed' | 'success',
    startedAt: r.startedAt.toISOString(),
    finishedAt: r.finishedAt ? r.finishedAt.toISOString() : null,
  }));
}

export async function create(raw: unknown) {
  const input = CreateRunInput.parse(raw);
  const row = await prisma.run.create({
    data: { title: input.title, status: 'queued' },
  });
  return {
    id: row.id,
    title: row.title,
    status: row.status as 'queued' | 'running' | 'failed' | 'success',
    startedAt: row.startedAt.toISOString(),
    finishedAt: row.finishedAt ? row.finishedAt.toISOString() : null,
  };
}

export async function update(
  id: string,
  patch: Partial<{ title: string; status: 'queued' | 'running' | 'failed' | 'success' }>,
) {
  const row = await prisma.run.update({ where: { id }, data: patch });
  return {
    id: row.id,
    title: row.title,
    status: row.status as 'queued' | 'running' | 'failed' | 'success',
    startedAt: row.startedAt.toISOString(),
    finishedAt: row.finishedAt ? row.finishedAt.toISOString() : null,
  };
}

export async function remove(id: string) {
  await prisma.run.delete({ where: { id } });
}

export async function listPaged({
  page,
  pageSize,
  status,
}: {
  page: number;
  pageSize: number;
  status?: 'queued' | 'running' | 'failed' | 'success';
}) {
  const where = status ? { status } : {};
  const [total, rows] = await Promise.all([
    prisma.run.count({ where }),
    prisma.run.findMany({
      where,
      skip: (page - 1) * pageSize,
      take: pageSize,
      orderBy: { startedAt: 'desc' },
    }),
  ]);
  return {
    data: rows.map(r => ({
      id: r.id,
      title: r.title,
      status: r.status as 'queued' | 'running' | 'failed' | 'success',
      startedAt: r.startedAt.toISOString(),
      finishedAt: r.finishedAt ? r.finishedAt.toISOString() : null,
    })),
    page,
    pageSize,
    total,
  };
}
