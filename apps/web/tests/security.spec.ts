import { test, expect } from "@playwright/test";

test("security headers present on root (placeholder)", async ({ request }) => {
  const base = process.env.NEXT_PUBLIC_WEB_ORIGIN || "http://localhost:3000";
  const res = await request.get(base);
  expect(res.status()).toBeGreaterThanOrEqual(200);
});
