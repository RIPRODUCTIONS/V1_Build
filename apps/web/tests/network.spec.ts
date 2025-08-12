import { expect, test } from '@playwright/test';

import { apiGet } from './utils/apiClient';
import { awaitNextRequest } from './utils/net';

test.describe('Dashboard network params', () => {
  test('leads filters propagate to API', async ({ page, request }) => {
    const API = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
    // seed user and set token to avoid redirect
    const uniq = Date.now().toString();
    const email = `net+${uniq}@example.com`;
    const password = 'secret123';
    await request.post(`${API}/users/register`, { data: { email, password } });
    const login = await request.post(`${API}/users/login`, { data: { email, password } });
    const token = (await login.json()).access_token as string;
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    await page.goto('/dashboard');

    // Listen for the NEXT leads request after we change controls
    const nextLeadsReq = awaitNextRequest(page, '/leads?');

    const lSearch = page.getByLabel('Leads search');
    await expect(lSearch).toBeVisible();
    await lSearch.fill('');
    await lSearch.fill('Alice');
    await page.getByLabel('Status', { exact: true }).first().selectOption('open');
    await page.getByLabel('Sort', { exact: true }).first().selectOption('name_asc');
    await page.waitForTimeout(50);

    let req = await nextLeadsReq;
    let url = new URL(req.url());
    let p = url.searchParams;

    // If the first request after interactions doesn't include q yet (debounce), wait for the next one
    if (p.get('q') !== 'Alice') {
      req = await awaitNextRequest(page, '/leads?');
      url = new URL(req.url());
      p = url.searchParams;
    }

    expect(p.get('q')).toBe('Alice');
    expect(p.get('status_filter')).toBe('open');
    expect(['name_asc', 'created_desc']).toContain(p.get('sort'));
    expect(p.get('limit')).toBeTruthy();
    expect(p.get('offset')).not.toBeNull();
  });

  test('tasks filters propagate to API', async ({ page, request }) => {
    const API = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
    const uniq = Date.now().toString();
    const email = `net2+${uniq}@example.com`;
    const password = 'secret123';
    await request.post(`${API}/users/register`, { data: { email, password } });
    const login = await request.post(`${API}/users/login`, { data: { email, password } });
    const token = (await login.json()).access_token as string;
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    const requests: string[] = [];
    page.on('request', req => {
      const url = req.url();
      if (url.includes('/tasks')) requests.push(url);
    });

    await page.goto('/dashboard');

    const tSearch = page.getByLabel('Tasks search');
    await expect(tSearch).toBeVisible();
    await tSearch.fill('email');
    await page.getByLabel('Status', { exact: true }).nth(1).selectOption('doing');
    await page.getByLabel('Sort', { exact: true }).nth(1).selectOption('title_desc');

    await page.waitForRequest(r => r.url().includes('/tasks'));

    const last = requests.at(-1)!;
    const u = new URL(last);
    const p = u.searchParams;

    expect(p.get('q')).toBe('email');
    expect(p.get('status_filter')).toBe('doing');
    expect(['title_desc', 'created_desc']).toContain(p.get('sort'));
    expect(p.get('limit')).toBeTruthy();
    expect(p.get('offset')).toBeDefined();
  });

  test('direct-API sorting by name via api client', async ({ request }) => {
    if (process.env.CI !== 'true') {
      test.skip(true, 'Skipping direct-API sorting test outside CI');
    }
    // Seed user and deterministic leads owned by that user
    const uniq = Date.now().toString();
    const email = `api+${uniq}@example.com`;
    const password = 'secret123';
    const API = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
    await request.post(`${API}/users/register`, { data: { email, password } });
    const login = await request.post(`${API}/users/login`, { data: { email, password } });
    const token = (await login.json()).access_token as string;
    const authHeaders = { Authorization: `Bearer ${token}` } as const;

    for (let i = 0; i < 10; i++) {
      const name = `Alpha ${String(i).padStart(3, '0')} ${uniq}`;
      const res = await request.post(`${API}/leads/`, {
        headers: authHeaders,
        data: { name, email: `${i}-${uniq}@acme.dev` },
      });
      expect(res.ok()).toBeTruthy();
    }

    const res = await apiGet('/leads', {
      headers: authHeaders,
      params: { sort: 'name_asc', limit: 15, offset: 0 },
    });
    expect(res.ok).toBeTruthy();
    const body: unknown = await res.json();
    const list = Array.isArray(body)
      ? body
      : typeof body === 'object' && body && (body as Record<string, unknown>).items
        ? ((body as Record<string, unknown>).items as unknown[])
        : [];
    expect(list.length).toBeGreaterThan(2);
    const names = list
      .slice(0, 5)
      .map((l: unknown) => String((l as Record<string, unknown>).name ?? ''));
    for (let i = 1; i < names.length; i++) {
      expect(names[i - 1].localeCompare(names[i])).toBeLessThanOrEqual(0);
    }
  });
});
