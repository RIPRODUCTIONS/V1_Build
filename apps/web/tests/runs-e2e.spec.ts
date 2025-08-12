import { expect, test } from '@playwright/test';

test('Runs page loads', async ({ page }) => {
  await page.goto('/runs');
  await expect(page.getByRole('heading', { name: 'Runs' })).toBeVisible();
});
