import { beforeAll, describe, expect, it } from 'vitest';

import { DELETE as deleteRun, PATCH as patchRun } from '@/app/api/runs/[id]/route';
import { GET as getRuns, POST as postRun } from '@/app/api/runs/route';
import * as runsService from '@/server/services/runs.service';
import { makeNextRequest } from '@/test-utils/nextReq';

describe('Next API routes: /api/runs', () => {
  beforeAll(async () => {
    // DB is reset/seeded by script before running this suite
  });

  it('GET /api/runs returns seeded runs', async () => {
    const req = makeNextRequest('/api/runs');
    const res = await getRuns(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThanOrEqual(1);
    const list = await runsService.listRuns();
    expect(list.length).toBeGreaterThanOrEqual(1);
  });

  it('POST /api/runs creates a run', async () => {
    const body = { title: 'integration-created' };
    const req = makeNextRequest('/api/runs', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'content-type': 'application/json' },
    });
    const res = await postRun(req);
    expect(res.status).toBe(201);
    const created = await res.json();
    expect(created?.title).toBe('integration-created');
    expect(created?.id).toBeTruthy();
  });

  it('PATCH /api/runs/[id] updates a run', async () => {
    const createReq = makeNextRequest('/api/runs', {
      method: 'POST',
      body: JSON.stringify({ title: 'to-update' }),
      headers: { 'content-type': 'application/json' },
    });
    const createdRes = await postRun(createReq);
    const created = await createdRes.json();
    const id = created.id as string;

    const req = makeNextRequest(`/api/runs/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'success' }),
      headers: { 'content-type': 'application/json' },
    });
    const res = await patchRun(req, { params: { id } } as { params: { id: string } });
    expect(res.status).toBe(200);
    const updated = await res.json();
    expect(updated.status).toBe('success');
  });

  it('DELETE /api/runs/[id] removes a run', async () => {
    const createReq = makeNextRequest('/api/runs', {
      method: 'POST',
      body: JSON.stringify({ title: 'to-delete' }),
      headers: { 'content-type': 'application/json' },
    });
    const createdRes = await postRun(createReq);
    const created = await createdRes.json();
    const id = created.id as string;

    const req = makeNextRequest(`/api/runs/${id}`, { method: 'DELETE' });
    const res = await deleteRun(req, { params: { id } } as { params: { id: string } });
    expect(res.status).toBe(204);
  });
});
