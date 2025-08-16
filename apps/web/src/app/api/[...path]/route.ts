import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://api:8000';
const INTERNAL_KEY = process.env.NEXT_PUBLIC_INTERNAL_API_KEY || process.env.INTERNAL_API_KEY || 'dev-internal-key';

async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const url = new URL(req.url);
  const target = new URL(`${API_BASE}/${path.join('/')}`);
  target.search = url.search;
  if (INTERNAL_KEY) {
    target.searchParams.set('token', INTERNAL_KEY);
  }

  const init: RequestInit = {
    method: req.method,
    headers: new Headers(req.headers),
    body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
    redirect: 'manual',
  };

  // Ensure API key header is present
  if (INTERNAL_KEY) {
    (init.headers as Headers).set('X-API-Key', INTERNAL_KEY);
  }

  const resp = await fetch(target.toString(), init as any);
  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers,
  });
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }): Promise<Response> {
  return proxy(req, params.path || []);
}

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }): Promise<Response> {
  return proxy(req, params.path || []);
}

export async function PUT(req: NextRequest, { params }: { params: { path: string[] } }): Promise<Response> {
  return proxy(req, params.path || []);
}

export async function PATCH(req: NextRequest, { params }: { params: { path: string[] } }): Promise<Response> {
  return proxy(req, params.path || []);
}

export async function DELETE(req: NextRequest, { params }: { params: { path: string[] } }): Promise<Response> {
  return proxy(req, params.path || []);
}


