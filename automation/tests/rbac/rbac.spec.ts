import { test, expect } from '@playwright/test';
import { STORAGE_STATE } from '../../config/storage-state';

test.describe('RBAC — ADMIN', () => {
  test.use({ storageState: STORAGE_STATE.admin });

  test('ADMIN sees Users menu item', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('menuitem', { name: 'Users' })).toBeVisible();
  });

  test('ADMIN sees New Project button on projects page', async ({ page }) => {
    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create project' })).toBeVisible();
  });

  test('ADMIN can access /users route', async ({ page }) => {
    await page.goto('/users');
    await expect(page).toHaveURL(/\/users/);
    await expect(page.getByRole('table', { name: 'Users table' })).toBeVisible();
  });
});

test.describe('RBAC — QA_ENGINEER', () => {
  test.use({ storageState: STORAGE_STATE.qa });

  test('QA_ENGINEER does NOT see Users menu item', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('menuitem', { name: 'Users' })).toHaveCount(0);
  });

  test('QA_ENGINEER sees New Project button', async ({ page }) => {
    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create project' })).toBeVisible();
  });

  test('QA_ENGINEER is redirected away from /users', async ({ page }) => {
    await page.goto('/users');
    await expect(page).not.toHaveURL(/^http:\/\/localhost:\d+\/users$/);
  });

  test('QA_ENGINEER sees New Defect button', async ({ page }) => {
    await page.goto('/defects');
    await expect(page.getByRole('heading', { name: 'Defects' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create defect' })).toBeVisible();
  });
});

test.describe('RBAC — VIEWER', () => {
  test.use({ storageState: STORAGE_STATE.viewer });

  test('VIEWER does NOT see Users menu item', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('menuitem', { name: 'Users' })).toHaveCount(0);
  });

  test('VIEWER does NOT see New Project button', async ({ page }) => {
    await page.goto('/projects');
    await expect(page.getByRole('button', { name: 'Create project' })).toHaveCount(0);
  });

  test('VIEWER does NOT see New Defect button', async ({ page }) => {
    await page.goto('/defects');
    await expect(page.getByRole('button', { name: 'Create defect' })).toHaveCount(0);
  });

  test('VIEWER is redirected away from /users', async ({ page }) => {
    await page.goto('/users');
    await expect(page).not.toHaveURL(/^http:\/\/localhost:\d+\/users$/);
  });

  test('VIEWER cannot see Start Run or Complete Run buttons', async ({ page }) => {
    await page.goto('/projects/1?tab=runs');
    const firstRunLink = page.getByRole('button', { name: /Open run/ }).first();
    if (await firstRunLink.count() > 0) {
      await firstRunLink.click();
      await expect(page.getByRole('button', { name: 'Start Run' })).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Complete Run' })).toHaveCount(0);
    }
  });

  test('VIEWER cannot see New Suite button on project detail', async ({ page }) => {
    await page.goto('/projects/1');
    await expect(page.getByRole('button', { name: 'New Suite' })).toHaveCount(0);
  });
});
