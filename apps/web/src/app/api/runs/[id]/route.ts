import { NextResponse } from 'next/server';

import { RunId, RunSchema, UpdateRunInput } from '@/contracts/run';
import * as svc from '@/server/services/runs.service';

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  const idRes = RunId.safeParse(params.id);
  if (!idRes.success) return NextResponse.json({ message: 'Invalid id' }, { status: 400 });

  const body = await req.json().catch(() => ({}));
  const patch = UpdateRunInput.safeParse(body);
  if (!patch.success) return NextResponse.json({ message: 'Invalid body' }, { status: 400 });

  const updated = await svc.updateRun(idRes.data, patch.data);
  return NextResponse.json(RunSchema.parse(updated));
}

export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  const idRes = RunId.safeParse(params.id);
  if (!idRes.success) return NextResponse.json({ message: 'Invalid id' }, { status: 400 });
  await svc.deleteRun(idRes.data);
  return new Response(null, { status: 204 });
}
