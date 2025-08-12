import { NextRequest } from 'next/server';

export function makeNextRequest(url: string, init?: RequestInit) {
  const absolute = url.startsWith('http') ? url : `http://localhost${url}`;
  return new NextRequest(new Request(absolute, init));
}
