import { request } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

async function globalSetup() {
  const ctx = await request.newContext({ baseURL: API_URL });

  const health = await ctx.get('/health');
  if (!health.ok()) throw new Error(`Backend /health returned ${health.status()}`);

  const dbHealth = await ctx.get('/health/db');
  if (!dbHealth.ok()) throw new Error(`Backend /health/db returned ${dbHealth.status()}`);

  await ctx.dispose();
  console.log('[global-setup] Backend health checks passed.');
}

export default globalSetup;
