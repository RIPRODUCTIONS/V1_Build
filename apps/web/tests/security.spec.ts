import { test, expect } from '@playwright/test';

async function getHeaders(request: any, url: string) {
  const res = await request.get(url);
  const entries = res.headersArray();
  const map: Record<string, string> = {};
  for (const { name, value } of entries) map[name.toLowerCase()] = value;
  return { status: res.status(), headers: map };
}

test.describe('Security headers', () => {
  test('CSP present on /health/live', async ({ request }) => {
    const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    const { status, headers } = await getHeaders(request, base + '/health/live');
    expect(status).toBeGreaterThanOrEqual(200);
    expect(status).toBeLessThan(500);
    const csp = headers['content-security-policy'] || headers['content-security-policy-report-only'];
    expect(csp).toBeTruthy();
  });

  test('CSP present on /api/runs', async ({ request }) => {
    const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    const { status, headers } = await getHeaders(request, base + '/api/runs');
    expect(status).toBeGreaterThanOrEqual(200);
    const csp = headers['content-security-policy'] || headers['content-security-policy-report-only'];
    expect(csp).toBeTruthy();
  });
});
