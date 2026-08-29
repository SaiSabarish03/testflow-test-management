import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import { uniqueProjectKey, uniqueProjectName } from '../../test-data/generators';

test.describe('Project Management', () => {
  test('ADMIN can create and archive a project', async ({ page, projectsPage, projectDetailPage }) => {
    const getErrors = captureConsoleErrors(page);
    const name = uniqueProjectName();
    const key = uniqueProjectKey();

    await projectsPage.goto();
    await projectsPage.createProject(name, key, 'E2E test project');
    await projectsPage.expectProjectInTable(name);

    await projectsPage.openProject(name);
    await expect(page).toHaveURL(/\/projects\/\d+/);

    await projectDetailPage.archiveProject();
    await projectDetailPage.expectStatus('Archived');

    expectNoConsoleErrors(getErrors);
  });

  test('ADMIN can edit a project name and description', async ({ page, projectsPage, projectDetailPage }) => {
    const name = uniqueProjectName();
    const key = uniqueProjectKey();
    const updatedName = uniqueProjectName();

    await projectsPage.goto();
    await projectsPage.createProject(name, key);
    await projectsPage.openProject(name);

    await projectDetailPage.editProject(updatedName, 'Updated description');
    await expect(page.getByRole('heading', { name: updatedName })).toBeVisible();
  });

  test('Project key must be uppercase letters/digits', async ({ page, projectsPage }) => {
    await projectsPage.goto();
    await page.getByRole('button', { name: 'Create project' }).click();
    await page.getByLabel('Project name').fill('Test');
    await page.getByLabel('Project key').fill('invalid key!');
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText(/Key must be/)).toBeVisible();
  });

  test('Project name is required', async ({ page, projectsPage }) => {
    await projectsPage.goto();
    await page.getByRole('button', { name: 'Create project' }).click();
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText('Name is required')).toBeVisible();
  });

  test('Projects list shows ACTIVE and ARCHIVED filter', async ({ page, projectsPage }) => {
    await projectsPage.goto();
    await expect(page.getByLabel('Filter by status').first()).toBeVisible();
    await expect(page.getByRole('table', { name: 'Projects table' })).toBeVisible();
  });
});
