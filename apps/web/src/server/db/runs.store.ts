import type { Run } from '@/contracts/run';

let runs: Run[] = [
  {
    id: 'run_1',
    status: 'success',
    startedAt: new Date().toISOString(),
    finishedAt: new Date().toISOString(),
    title: 'Initial',
  },
];

export async function list() {
  return runs;
}

export async function create(input: { title: string }) {
  const created: Run = {
    id: `run_${Date.now()}`,
    title: input.title,
    status: 'queued',
    startedAt: new Date().toISOString(),
    finishedAt: null,
  };
  runs = [created, ...runs];
  return created;
}

export async function update(id: string, patch: Partial<Run>) {
  const idx = runs.findIndex(r => r.id === id);
  if (idx === -1) throw new Error('Not found');
  runs[idx] = { ...runs[idx], ...patch };
  return runs[idx];
}

export async function remove(id: string) {
  runs = runs.filter(r => r.id !== id);
}
