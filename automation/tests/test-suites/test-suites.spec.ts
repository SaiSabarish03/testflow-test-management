import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import { uniqueProjectKey, uniqueProjectName, uniqueSuiteName } from '../../test-data/generators';

/** Create a project and navigate to its detail page, returning the project name. */
async function createAndOpenProject(
  page: import('@playwright/test').Page,
  projectsPage: import('../../pages/ProjectsPage').ProjectsPage,
) {
  const projName = uniqueProjectName();
  await projectsPage.goto();
  await projectsPage.createProject(projName, uniqueProjectKey());
  // After creation the modal closes and the project appears in the table — open it
  await projectsPage.openProject(projName);
  await expect(page).toHaveURL(/\/projects\/\d+/);
  return projName;
}

test.describe('Test Suite Management', () => {
  test('ADMIN can create, edit, and delete a test suite', async ({
    page, projectsPage, projectDetailPage,
  }) => {
    const getErrors = captureConsoleErrors(page);
    const suiteName = uniqueSuiteName();
    const updatedName = uniqueSuiteName();

    await createAndOpenProject(page, projectsPage);
    await projectDetailPage.openSuitesTab();

    await projectDetailPage.createSuite(suiteName, 'Suite for E2E testing');
    await expect(page.getByRole('button', { name: `Open suite ${suiteName}` })).toBeVisible();

    await projectDetailPage.editSuite(suiteName, updatedName);
    await expect(page.getByRole('button', { name: `Open suite ${updatedName}` })).toBeVisible();

    await projectDetailPage.deleteSuite(updatedName);
    await expect(page.getByRole('button', { name: `Open suite ${updatedName}` })).toHaveCount(0);

    expectNoConsoleErrors(getErrors);
  });

  test('Suite name is required', async ({ page, projectsPage, projectDetailPage }) => {
    await createAndOpenProject(page, projectsPage);
    await projectDetailPage.openSuitesTab();

    await page.getByRole('button', { name: 'Create suite' }).click();
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText('Name is required')).toBeVisible();
  });

  test('Suite shows empty state when no test cases exist', async ({
    page, projectsPage, projectDetailPage,
  }) => {
    const suiteName = uniqueSuiteName();

    await createAndOpenProject(page, projectsPage);
    await projectDetailPage.openSuitesTab();
    await projectDetailPage.createSuite(suiteName);
    await projectDetailPage.openSuite(suiteName);

    await expect(page.getByText('No test cases found')).toBeVisible();
  });
});
