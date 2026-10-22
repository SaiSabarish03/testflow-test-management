import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env') });

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

const AUTH_DIR = path.resolve(__dirname, '.auth');

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: FRONTEND_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    // ── Auth setup ──────────────────────────────────────────────────────────
    {
      name: 'setup',
      testMatch: '**/auth.setup.ts',
      use: { ...devices['Desktop Chrome'] },
    },

    // ── Unauthenticated tests (auth spec itself) ─────────────────────────────
    {
      name: 'chromium-noauth',
      testMatch: '**/auth/auth.spec.ts',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },

    // Cross-browser smoke tests: authentication and route protection
    {
      name: 'firefox-noauth',
      testMatch: '**/auth/auth.spec.ts',
      grep: /invalid password|unknown email|unauthenticated user/i,
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit-noauth',
      testMatch: '**/auth/auth.spec.ts',
      grep: /invalid password|unknown email|unauthenticated user/i,
      use: { ...devices['Desktop Safari'] },
    },


    // ── Admin-authenticated tests ────────────────────────────────────────────
    {
      name: 'chromium-admin',
      testMatch: [
        '**/projects/projects.spec.ts',
        '**/test-suites/test-suites.spec.ts',
        '**/test-cases/test-cases.spec.ts',
        '**/test-cases/deprecation.spec.ts',
        '**/test-runs/test-runs.spec.ts',
        '**/defects/defects.spec.ts',
        '**/users/users.spec.ts',
      ],
      use: {
        ...devices['Desktop Chrome'],
        storageState: path.join(AUTH_DIR, 'admin.json'),
      },
      dependencies: ['setup'],
    },

    // ── RBAC tests (each describe block uses test.use internally) ────────────
    {
      name: 'chromium-rbac',
      testMatch: '**/rbac/rbac.spec.ts',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      name: 'api',
      testMatch: '**/api/api.spec.ts',
      use: {
        baseURL: API_URL,
      },
    },
  ],
  outputDir: 'test-results',
  globalSetup: path.resolve(__dirname, 'config/global-setup.ts'),
});

export { FRONTEND_URL, API_URL };
