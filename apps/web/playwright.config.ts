import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5000 },
  reporter: 'list',
  retries: process.env.CI ? 1 : 0,
  globalSetup: './tests/global.setup.ts',
  globalTeardown: './tests/global.teardown.ts',
  use: {
    baseURL: process.env.WEB_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
