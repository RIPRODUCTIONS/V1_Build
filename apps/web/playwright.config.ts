import { defineConfig, devices } from '@playwright/test';
import fs from 'fs';

const resultsDir = process.env.PW_RESULTS_DIR || './test-results';
try {
  fs.mkdirSync(resultsDir, { recursive: true });
} catch {}

const runningInCompose = process.env.IN_DOCKER_COMPOSE === 'true';

export default defineConfig({
  testDir: './tests',
  timeout: 90_000,
  expect: { timeout: 5000 },
  reporter: [['list'], ['junit', { outputFile: `${resultsDir}/results.xml` }]],
  retries: process.env.CI ? 1 : 0,
  globalSetup: './tests/global.setup.ts',
  globalTeardown: './tests/global.teardown.ts',
  use: {
    baseURL: process.env.WEB_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  outputDir: resultsDir,
  webServer: runningInCompose
    ? undefined
    : {
        command: 'npm run dev',
        port: 3000,
        reuseExistingServer: true,
        timeout: 120_000,
      },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
