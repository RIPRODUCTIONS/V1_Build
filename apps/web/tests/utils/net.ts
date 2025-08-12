import { APIRequestContext, Page, Request, Response } from '@playwright/test';

/** Resolves with the NEXT request whose URL contains the substring (case-sensitive). */
export function awaitNextRequest(page: Page, contains: string): Promise<Request> {
  return new Promise(resolve => {
    const handler = (req: Request) => {
      if (req.url().includes(contains) && req.method() === 'GET') {
        page.off('request', handler);
        resolve(req);
      }
    };
    page.on('request', handler);
  });
}

/** Resolves with the NEXT response whose URL contains the substring, method is GET, and status is 200. */
export function awaitNextResponse(page: Page, contains: string): Promise<Response> {
  return page.waitForResponse(res => {
    const req = res.request();
    return req.method() === 'GET' && res.status() === 200 && res.url().includes(contains);
  });
}

/** Get a JWT token by registering then logging in against the API. */
export async function getToken(request: APIRequestContext): Promise<string> {
  const API =
    process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
  const email = `e2e+${Date.now()}@test.dev`;
  const password = 'secret123';
  await request.post(`${API}/users/register`, {
    data: { email, password },
    headers: { 'content-type': 'application/json' },
  });
  const res = await request.post(`${API}/users/login`, {
    data: { email, password },
    headers: { 'content-type': 'application/json' },
  });
  const body = await res.json();
  return body.access_token as string;
}
