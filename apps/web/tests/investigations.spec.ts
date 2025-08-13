import { test, expect } from '@playwright/test';

test('Investigations page loads and queues OSINT', async ({ page }) => {
  await page.goto('/investigations');
  await page.fill('input[aria-label="Subject name"]', 'Jane Doe');
  await page.click('button:has-text("Run OSINT")');
  await expect(page.locator('text=Queued')).toBeVisible({ timeout: 5000 });
});


