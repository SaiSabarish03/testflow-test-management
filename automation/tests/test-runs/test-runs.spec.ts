import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import {
  uniqueProjectKey, uniqueProjectName, uniqueSuiteName,
  uniqueTestCaseTitle, uniqueRunName,
} from '../../test-data/generators';
import type { Page } from '@playwright/test';
import type { ProjectsPage } from '../../pages/ProjectsPage';
import type { ProjectDetailPage } from '../../pages/ProjectDetailPage';
import type { TestCaseFormPage } from '../../pages/TestCaseFormPage';

async function buildProjectWithReadyCase(
  page: Page,
  projectsPage: ProjectsPage,
  projectDetailPage: ProjectDetailPage,
  testCaseFormPage: TestCaseFormPage,
): Promise<string> {
  const projName = uniqueProjectName();
  const suiteName = uniqueSuiteName();
  const caseTitle = uniqueTestCaseTitle();

  await projectsPage.goto();
  await projectsPage.createProject(projName, uniqueProjectKey());
  await projectsPage.openProject(projName);
  await expect(page).toHaveURL(/\/projects\/\d+/);
  await projectDetailPage.openSuitesTab();
  await projectDetailPage.createSuite(suiteName);
  await projectDetailPage.openSuite(suiteName);

  await page.getByRole('button', { name: 'Create test case' }).click();
  await testCaseFormPage.fillTitle(caseTitle);
  await testCaseFormPage.fillExpectedResult('Expected outcome');
  await testCaseFormPage.addStep('Perform the test action');
  await testCaseFormPage.setStatus('READY');
  await testCaseFormPage.submit();
  await expect(page).toHaveURL(/\/test-cases\/\d+/);

  return `${projName}|${caseTitle}`;
}

test.describe('Test Run Workflow', () => {
  test('User can execute a test run and complete it with PASS result', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const getErrors = captureConsoleErrors(page);
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await expect(page).toHaveURL(/\/runs\/new/);
    await createRunPage.expectOnlyReadyCasesVisible();
    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('QA');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await expect(page).toHaveURL(/\/runs\/\d+/);
    await runDetailPage.expectStatus('Not Started');
    await runDetailPage.startRun();
    await runDetailPage.expectStatus('In Progress');
    await runDetailPage.expectSummaryVisible();
    await runDetailPage.expectNotRunAlert();
    await runDetailPage.recordFirstResult('Pass', 'Login succeeded as expected');
    await runDetailPage.completeRun();
    await runDetailPage.expectStatus('Completed');
    await runDetailPage.expectNoActionButtons();

    expectNoConsoleErrors(getErrors);
  });

  test('User can execute a test run and complete it with FAIL result', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('Staging');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await runDetailPage.startRun();
    await runDetailPage.recordFirstResult('Fail', 'Login failed unexpectedly');
    await runDetailPage.completeRun();
    await runDetailPage.expectStatus('Completed');
  });

  test('User can execute a test run and complete it with BLOCKED result', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('Dev');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await runDetailPage.startRun();
    await runDetailPage.recordFirstResult('Blocked', 'Blocked by environment issue');
    await runDetailPage.completeRun();
    await runDetailPage.expectStatus('Completed');
  });

  test('Completing a run with NOT_RUN results shows backend validation message', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('QA');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await runDetailPage.startRun();
    await page.getByRole('button', { name: 'Complete Run' }).click();
    await expect(page.getByText(/NOT_RUN|not.*run|incomplete/i).first()).toBeVisible();
  });

  test('Run status becomes IN_PROGRESS after start and COMPLETED after complete', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('QA');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await runDetailPage.expectStatus('Not Started');
    await runDetailPage.startRun();
    await runDetailPage.expectStatus('In Progress');
    await runDetailPage.recordFirstResult('Pass');
    await runDetailPage.completeRun();
    await runDetailPage.expectStatus('Completed');
  });

  test('Executor information is displayed after recording a result', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
    createRunPage, runDetailPage,
  }) => {
    const [projName, caseTitle] = (await buildProjectWithReadyCase(page, projectsPage, projectDetailPage, testCaseFormPage)).split('|');

    await page.goto('/projects');
    await projectsPage.openProject(projName);
    await projectDetailPage.openRunsTab();
    await projectDetailPage.clickNewRun();

    await createRunPage.fillRunName(uniqueRunName());
    await createRunPage.fillEnvironment('QA');
    await createRunPage.selectTestCase(caseTitle);
    await createRunPage.createRun();

    await runDetailPage.startRun();
    await runDetailPage.recordFirstResult('Pass');

    const executedByCell = page.locator('.ant-table-row').first().locator('td').nth(3);
    await expect(executedByCell).not.toHaveText('—');
  });
});
