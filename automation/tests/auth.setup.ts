import { test as setup } from '@playwright/test';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { STORAGE_STATE } from '../config/storage-state';

export { STORAGE_STATE };

dotenv.config({ path: path.resolve(__dirname, '../.env') });

const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || 'admin@testflow.local';
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || 'Admin123!';
const QA_EMAIL = process.env.TEST_QA_EMAIL || 'qa@testflow.local';
const QA_PASSWORD = process.env.TEST_QA_PASSWORD || 'QaPass123!';
const VIEWER_EMAIL = process.env.TEST_VIEWER_EMAIL || 'viewer@testflow.local';
const VIEWER_PASSWORD = process.env.TEST_VIEWER_PASSWORD || 'View123!';

async function loginAndSave(page: import('@playwright/test').Page, email: string, password: string, file: string) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/\/dashboard/);
  await page.context().storageState({ path: file });
}

setup('authenticate as admin', async ({ page }) => {
  await loginAndSave(page, ADMIN_EMAIL, ADMIN_PASSWORD, STORAGE_STATE.admin);
});

setup('authenticate as qa', async ({ page }) => {
  await loginAndSave(page, QA_EMAIL, QA_PASSWORD, STORAGE_STATE.qa);
});

setup('authenticate as viewer', async ({ page }) => {
  await loginAndSave(page, VIEWER_EMAIL, VIEWER_PASSWORD, STORAGE_STATE.viewer);
});
