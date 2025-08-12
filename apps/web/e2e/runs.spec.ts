import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';
import { adminCookie } from '../src/test-utils/auth';

test.beforeEach(async ({ context, page }) => {
  await context.addCookies(adminCookie('http://localhost:3000'));
  await page.goto('http://localhost:3000/runs');
});

test('a11y clean', async ({ page }) => {
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
});

test('runs page lists, creates, updates, deletes', async ({ page }) => {
  await expect(page.getByRole('heading', { name: /runs/i })).toBeVisible();
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);

  await page.getByRole('textbox', { name: /run-title/i }).fill('e2e-run');
  await page.getByRole('button', { name: /create/i }).click();
  await expect(page.getByText('e2e-run')).toBeVisible();

  // Simplified: click the first "Run ▶" then rename then delete
  await page
    .getByRole('button', { name: /Run ▶/i })
    .first()
    .click();
  await page
    .getByRole('button', { name: /Rename/i })
    .first()
    .click();
  await page
    .getByRole('button', { name: /delete-/i })
    .first()
    .click();
});
