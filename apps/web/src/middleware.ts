import { type NextRequest, NextResponse } from 'next/server';

export function middleware(req: NextRequest) {
  // Simple security headers on every response
  const res = NextResponse.next();
  res.headers.set('X-Frame-Options', 'DENY');
  res.headers.set('X-Content-Type-Options', 'nosniff');
  res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  // Very light RBAC example: restrict DELETE to admins (header based for now)
  if (
    process.env.NODE_ENV === 'production' &&
    req.nextUrl.pathname.startsWith('/api/runs') &&
    req.method === 'DELETE'
  ) {
    const role = req.headers.get('x-role') || 'viewer';
    if (role !== 'admin') return new NextResponse('Forbidden', { status: 403 });
  }

  return res;
}

export const config = { matcher: ['/api/runs/:path*'] };
