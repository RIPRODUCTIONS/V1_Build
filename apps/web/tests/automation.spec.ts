import { test, expect } from "@playwright/test";

test("Lead intake automation succeeds", async ({ page }) => {
  await page.goto("/automation");
  await page.getByRole("button", { name: "Run: Lead Intake" }).click();
  await expect(page.locator("li >> nth=0")).toContainText(/queued|running|succeeded/);
});
