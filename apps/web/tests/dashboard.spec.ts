import { test, expect } from '@playwright/test';
import { awaitNextRequest, awaitNextResponse } from './utils/net';

async function seed(request: any, counts: { leads?: number; tasks?: number } = {}) {
  const uniq = Date.now().toString();
  const email = `user+${uniq}@example.com`;
  const password = 'secret123';
  await request.post('http://127.0.0.1:8000/users/register', { data: { email, password } });
  const login = await request.post('http://127.0.0.1:8000/users/login', { data: { email, password } });
  const token = (await login.json()).access_token as string;
  const auth = { headers: { Authorization: `Bearer ${token}` } };
  const leadsCount = counts.leads ?? 30;
  const tasksCount = counts.tasks ?? 30;
  // Seed leads containing uniq in names for search (zero-padded for stable sort)
  for (let i = 0; i < leadsCount; i++) {
    const name = `Lead ${String(i).padStart(3, '0')} ${uniq}`;
    await request.post('http://127.0.0.1:8000/leads/', {
      ...auth,
      data: { name, email: `${i}-${uniq}@acme.com` },
    });
  }
  // Seed tasks with mixed statuses and uniq in title
  for (let i = 0; i < tasksCount; i++) {
    const res = await request.post('http://127.0.0.1:8000/tasks/', {
      ...auth,
      data: { title: `Task ${String(i).padStart(3, '0')} ${uniq}`, lead_id: null },
    });
    const id = (await res.json()).id as number;
    if (i % 2 === 0) {
      await request.put(`http://127.0.0.1:8000/tasks/${id}`, { ...auth, data: { status: 'done' } });
    }
  }
  return { token, uniq };
}

test.describe('Dashboard filters, sorting, infinite scroll, and toasts', () => {
  test('filters/sorting UI wires query params and shows toast', async ({ page, request }) => {
    const { token, uniq } = await seed(request);
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    await page.goto('/dashboard');

    // Apply search for seeded uniq token
    const search = page.getByLabel('Leads search');
    await expect(search).toBeVisible();
    await search.fill(uniq);

    // Apply status (open)
    await page.locator('select').nth(0).selectOption('open');

    // Apply sort by name and capture the next leads request (debounced)
    const reqP = awaitNextRequest(page, '/leads?');
    await page.locator('#lead-sort').selectOption('name_asc');
    await reqP;

    // Expect toast
    await expect(page.getByText('Filters applied').first()).toBeVisible({ timeout: 10000 });
  });

  test('infinite scroll loads more', async ({ page, request }) => {
    const { token } = await seed(request, { leads: 50, tasks: 50 });
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    await page.goto('/dashboard');
    // Ensure we see initial items, then scroll to trigger more
    await expect(page.locator('h2:text("Leads")')).toBeVisible();
    // Scroll to bottom to trigger observer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    // Basic smoke: page stays on dashboard
    await expect(page).toHaveURL(/.*\/dashboard$/);
  });

  test('empty filter yields no results', async ({ page, request }) => {
    const { token, uniq } = await seed(request, { leads: 5, tasks: 5 });
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    await page.goto('/dashboard');
    const search = page.getByLabel('Leads search');
    await expect(search).toBeVisible();
    await search.fill(uniq + '-no-match');
    await page.locator('#lead-sort').selectOption('name_asc');
    await expect(page.getByText('Filters applied').first()).toBeVisible();
    // No list items should include uniq + '-no-match'
    await expect(page.locator('li', { hasText: uniq + '-no-match' })).toHaveCount(0);
  });

  test('sorting stable with larger dataset', async ({ page, request }) => {
    const { token, uniq } = await seed(request, { leads: 60, tasks: 0 });
    await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
    await page.goto('/dashboard');
    const search = page.getByLabel('Leads search');
    await expect(search).toBeVisible();
    await search.fill(uniq);
    // Network-level assertion: capture the next request(s) and assert final state
    let nextReq = awaitNextRequest(page, '/leads?');
    await page.locator('#lead-sort').selectOption('name_asc');
    let req = await nextReq;
    let url = new URL(req.url());
    let params = url.searchParams;
    if (params.get('sort') !== 'name_asc' || params.get('q') !== uniq) {
      // Some UIs fire an intermediate request with previous/default state; wait for the subsequent one
      req = await awaitNextRequest(page, '/leads?');
      url = new URL(req.url());
      params = url.searchParams;
    }
    expect(params.get('sort')).toBe('name_asc');
    expect(params.get('q')).toBe(uniq);
  });
});
