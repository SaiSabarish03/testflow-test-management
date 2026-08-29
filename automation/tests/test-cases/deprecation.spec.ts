import { test, expect } from '../../fixtures/base';
import {
  uniqueProjectKey, uniqueProjectName, uniqueSuiteName, uniqueTestCaseTitle,
} from '../../test-data/generators';
import { dismissNotifications } from '../../helpers/antDesign';

test.describe('Test Case Deprecation', () => {
  test('READY test case can be deprecated from detail page', async ({
    page, projectsPage, projectDetailPage, testCaseDetailPage, testCaseFormPage,
  }) => {
    const projName = uniqueProjectName();
    const suiteName = uniqueSuiteName();
    const title = uniqueTestCaseTitle();

    await projectsPage.goto();
    await projectsPage.createProject(projName, uniqueProjectKey());
    await projectsPage.openProject(projName);
    await projectDetailPage.openSuitesTab();
    await projectDetailPage.createSuite(suiteName);
    await projectDetailPage.openSuite(suiteName);

    await page.getByRole('button', { name: 'Create test case' }).click();
    await testCaseFormPage.fillTitle(title);
    await testCaseFormPage.fillExpectedResult('Expected');
    await testCaseFormPage.addStep('Perform test action');
    await testCaseFormPage.setStatus('READY');
    await testCaseFormPage.submit();

    await expect(page).toHaveURL(/\/test-cases\/\d+/);
    await dismissNotifications(page);
    await testCaseDetailPage.expectStatus('Ready');
    await testCaseDetailPage.deprecate();
    await testCaseDetailPage.expectStatus('Deprecated');
    await expect(page.getByRole('button', { name: 'Deprecate test case' })).toHaveCount(0);
  });

  test('Deprecated test case does not appear in Create Run selection', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage, testCaseDetailPage, createRunPage,
  }) => {
    const projName = uniqueProjectName();
    const suiteName = uniqueSuiteName();
    const title = uniqueTestCaseTitle();

    await projectsPage.goto();
    await projectsPage.createProject(projName, uniqueProjectKey());
    await projectsPage.openProject(projName);
    await projectDetailPage.openSuitesTab();
    await projectDetailPage.createSuite(suiteName);
    await projectDetailPage.openSuite(suiteName);

    await page.getByRole('button', { name: 'Create test case' }).click();
    await testCaseFormPage.fillTitle(title);
    await testCaseFormPage.fillExpectedResult('Expected');
    await testCaseFormPage.addStep('Perform test action');
    await testCaseFormPage.setStatus('READY');
    await testCaseFormPage.submit();
    await expect(page).toHaveURL(/\/test-cases\/\d+/);

    await dismissNotifications(page);
    await testCaseDetailPage.deprecate();

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await expect(page).toHaveURL(/\/runs\/new/);
    await createRunPage.expectNoReadyCases();
  });
});
