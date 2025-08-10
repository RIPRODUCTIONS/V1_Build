import { Page, expect } from "@playwright/test";

export async function waitForListCount(page: Page, selector: string, minimum = 1) {
  await expect(async () => {
    const count = await page.locator(selector).count();
    expect(count).toBeGreaterThanOrEqual(minimum);
  }).toPass({ intervals: [200, 300, 500], timeout: 5000 });
}
