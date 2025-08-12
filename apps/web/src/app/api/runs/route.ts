import { NextRequest, NextResponse } from 'next/server';

import * as svc from '@/server/services/runs.service';

export async function GET(req: NextRequest) {
  const u = new URL(req.url);
  const page = u.searchParams.get('page');
  const pageSize = u.searchParams.get('pageSize');
  const status = u.searchParams.get('status') as 'queued' | 'running' | 'failed' | 'success' | null;
  const result = await svc.listRunsFlexible({
    page: page ? Number(page) : undefined,
    pageSize: pageSize ? Number(pageSize) : undefined,
    status: status ?? undefined,
  });
  return NextResponse.json(result, { headers: { 'Cache-Control': 'no-store' } });
}

export async function POST(req: Request) {
  const json = await req.json();
  const run = await svc.createRun(json);
  return NextResponse.json(run, { status: 201 });
}
