import { FullConfig } from '@playwright/test';

export default async function globalSetup(_config: FullConfig) {
  // ensure API env hints exist for local runs if desired
  process.env.API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
}
