import { test, expect } from '@playwright/test';
import { getToken } from './utils/net';

test('Life button triggers and shows toast', async ({ page, request }) => {
  const token = await getToken(request);
  await page.addInitScript((t) => localStorage.setItem('token', t), token);
  await page.goto('/');
  const btn = page.getByRole('button', { name: 'Calendar Organize' });
  await btn.click();
  // expect toast success appears (text includes queued)
  await expect(page.getByText(/queued/i)).toBeVisible({ timeout: 5000 });
});
