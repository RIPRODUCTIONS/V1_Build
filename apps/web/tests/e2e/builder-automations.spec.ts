import { test, expect } from '@playwright/test';

test.describe('Builder Automations', () => {
  test('Personal Research quick run', async ({ page }) => {
    await page.goto('http://localhost:3000/personal');
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/personal|assistant/i);

    // Click run using default topic
    await page.getByTestId('research-assistant-run').click();
    await expect(page.getByTestId('research-results')).toBeVisible({ timeout: 45000 });
  });
});


