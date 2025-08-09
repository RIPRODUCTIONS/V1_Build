import { request as makeRequest, FullConfig } from '@playwright/test';

export default async function globalTeardown(config: FullConfig) {
  const apiBase = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
  const token = process.env.CI_CLEANUP_TOKEN || '';
  const ciEnv = process.env.CI_ENV === 'true';
  if (!ciEnv || !token) {
    // Skip cleanup if not in CI mode or token missing
    return;
    }
  const req = await makeRequest.newContext();
  await req.delete(`${apiBase}/admin/cleanup/all`, {
    headers: { 'X-CI-Token': token },
  });
  await req.dispose();
}
