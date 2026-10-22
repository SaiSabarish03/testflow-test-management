import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || 'admin@testflow.local';
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || 'Admin123!';

test.describe('Authentication', () => {
  test('ADMIN can log in with valid credentials and reach dashboard', async ({ page }) => {
    const getErrors = captureConsoleErrors(page);
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_EMAIL, ADMIN_PASSWORD);
    await loginPage.expectDashboard();

    // Authenticated navigation works
    await expect(page.getByRole('menuitem', { name: 'Projects' })).toBeVisible();
    await expect(page.getByRole('menuitem', { name: 'Defects' })).toBeVisible();

    // User info is displayed in the header (use exact match to avoid strict-mode violation)
    await expect(page.getByText('Admin User', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('ADMIN', { exact: true }).first()).toBeVisible();

    expectNoConsoleErrors(getErrors);
  });

  test('Login with invalid password shows error and stays on login page', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_EMAIL, 'wrongpassword');

    await loginPage.expectOnLoginPage();
    await loginPage.expectError('');
    // Error alert is visible (any message)
    await expect(page.getByTestId('login-error')).toBeVisible();
  });

  test('Login with unknown email shows error', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login('nobody@testflow.local', 'anything');

    await loginPage.expectOnLoginPage();
    await expect(page.getByTestId('login-error')).toBeVisible();
  });

  test('Protected route redirects unauthenticated user to login', async ({ page }) => {
    await page.goto('/projects');
    await expect(page).toHaveURL(/\/login/);
  });

  test('Protected route redirects unauthenticated user from dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('QA Engineer can log in and sees correct role', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const qaEmail = process.env.TEST_QA_EMAIL || 'qa@testflow.local';
    const qaPassword = process.env.TEST_QA_PASSWORD || 'QaPass123!';

    await loginPage.goto();
    await loginPage.login(qaEmail, qaPassword);
    await loginPage.expectDashboard();

    await expect(page.getByText('QA_ENGINEER')).toBeVisible();
    // Users menu item should NOT be visible for QA
    await expect(page.getByRole('menuitem', { name: 'Users' })).toHaveCount(0);
  });

  test('Viewer can log in and sees correct role', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const viewerEmail = process.env.TEST_VIEWER_EMAIL || 'viewer@testflow.local';
    const viewerPassword = process.env.TEST_VIEWER_PASSWORD || 'View123!';

    await loginPage.goto();
    await loginPage.login(viewerEmail, viewerPassword);
    await loginPage.expectDashboard();

    await expect(page.getByText('VIEWER', { exact: true }).first()).toBeVisible();
  });

  test('Authenticated user can log out and is redirected from protected routes', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(ADMIN_EMAIL, ADMIN_PASSWORD);
    await loginPage.expectDashboard();

    await page.getByLabel('User menu').click();
    await page.getByRole('menuitem', { name: 'Logout' }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/projects');
    await expect(page).toHaveURL(/\/login/);
    await expect.poll(() => page.evaluate(() => localStorage.getItem('access_token'))).toBeNull();
  });
});
