import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('dashboard has no critical/serious a11y issues', async ({ page, request }) => {
  // seed user and set token to avoid redirect
  const uniq = Date.now().toString();
  const email = `a11y+${uniq}@example.com`;
  const password = 'secret123';
  const API = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
  await request.post(`${API}/users/register`, { data: { email, password } });
  const login = await request.post(`${API}/users/login`, { data: { email, password } });
  const token = (await login.json()).access_token as string;
  await page.addInitScript(([t]) => localStorage.setItem('token', t), [token]);
  await page.goto('/dashboard');
  const results = await new AxeBuilder({ page }).analyze();
  const violations = results.violations.filter(v => ['critical', 'serious'].includes(v.impact || ''));
  if (violations.length) {
    console.error(JSON.stringify(violations, null, 2));
  }
  expect(violations.length).toBe(0);
});
