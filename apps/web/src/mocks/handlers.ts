import { http, HttpResponse } from 'msw';

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

export const handlers = [
  http.get('/api/runs', () => HttpResponse.json(runs)),

  http.post('/api/runs', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as { title?: string };
    if (!body?.title) {
      return HttpResponse.json({ message: 'Title required' }, { status: 400 });
    }
    const newRun: Run = {
      id: `run_${Date.now()}`,
      status: 'queued',
      startedAt: new Date().toISOString(),
      finishedAt: null,
      title: body.title,
    };
    runs = [newRun, ...runs];
    return HttpResponse.json(newRun, { status: 201 });
  }),
  http.patch('/api/runs/:id', async ({ params, request }) => {
    const { id } = params as { id: string };
    const body = (await request.json().catch(() => ({}))) as Partial<Run>;
    const idx = runs.findIndex(r => r.id === id);
    if (idx === -1) return HttpResponse.json({ message: 'Not found' }, { status: 404 });
    runs[idx] = { ...runs[idx], ...body } as Run;
    return HttpResponse.json(runs[idx]);
  }),
  http.delete('/api/runs/:id', ({ params }) => {
    const { id } = params as { id: string };
    const before = runs.length;
    runs = runs.filter(r => r.id !== id);
    if (runs.length === before) return HttpResponse.json({ message: 'Not found' }, { status: 404 });
    return HttpResponse.json({ ok: true });
  }),
];
