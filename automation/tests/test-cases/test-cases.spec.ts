import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import {
  uniqueProjectKey, uniqueProjectName, uniqueSuiteName, uniqueTestCaseTitle,
} from '../../test-data/generators';
import type { Page } from '@playwright/test';
import type { ProjectsPage } from '../../pages/ProjectsPage';
import type { ProjectDetailPage } from '../../pages/ProjectDetailPage';

async function setupSuite(page: Page, projectsPage: ProjectsPage, projectDetailPage: ProjectDetailPage) {
  const projName = uniqueProjectName();
  const suiteName = uniqueSuiteName();

  await projectsPage.goto();
  await projectsPage.createProject(projName, uniqueProjectKey());
  await projectsPage.openProject(projName);
  await expect(page).toHaveURL(/\/projects\/\d+/);
  await projectDetailPage.openSuitesTab();
  await projectDetailPage.createSuite(suiteName);
  await projectDetailPage.openSuite(suiteName);
  await expect(page).toHaveURL(/\/suites\/\d+/);
}

test.describe('Test Case Management', () => {
  test('QA can create a test case as DRAFT and promote to READY', async ({
    page, projectsPage, projectDetailPage, testCaseDetailPage, testCaseFormPage,
  }) => {
    const getErrors = captureConsoleErrors(page);
    const title = uniqueTestCaseTitle();

    await setupSuite(page, projectsPage, projectDetailPage);
    await page.getByRole('button', { name: 'Create test case' }).click();
    await expect(page).toHaveURL(/suites\/\d+\/test-cases\/new/);

    await testCaseFormPage.fillTitle(title);
    await testCaseFormPage.fillExpectedResult('Expected outcome');
    await testCaseFormPage.addStep('Perform the test action');
    await testCaseFormPage.submit();

    await expect(page).toHaveURL(/\/test-cases\/\d+/);
    await testCaseDetailPage.expectStatus('Draft');
    await testCaseDetailPage.markReady();
    await testCaseDetailPage.expectStatus('Ready');

    expectNoConsoleErrors(getErrors);
  });

  test('Test case form validates required fields', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
  }) => {
    await setupSuite(page, projectsPage, projectDetailPage);
    await page.getByRole('button', { name: 'Create test case' }).click();
    await testCaseFormPage.submit();
    await expect(page.getByText('Title is required')).toBeVisible();
    await expect(page.getByText('Expected result is required')).toBeVisible();
  });

  test('Step editor adds, numbers, and removes steps correctly', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage, testCaseDetailPage,
  }) => {
    const title = uniqueTestCaseTitle();

    await setupSuite(page, projectsPage, projectDetailPage);
    await page.getByRole('button', { name: 'Create test case' }).click();

    await testCaseFormPage.fillTitle(title);
    await testCaseFormPage.fillExpectedResult('All steps pass');
    await testCaseFormPage.addStep('Open the application');
    await testCaseFormPage.addStep('Click the login button');
    await testCaseFormPage.addStep('Enter credentials');

    await expect(page.getByText('Step 1')).toBeVisible();
    await expect(page.getByText('Step 2')).toBeVisible();
    await expect(page.getByText('Step 3')).toBeVisible();

    await testCaseFormPage.removeStep(2);
    await expect(page.getByText('Step 3')).toHaveCount(0);
    await expect(page.getByText('Step 2')).toBeVisible();

    await testCaseFormPage.submit();
    await expect(page).toHaveURL(/\/test-cases\/\d+/);
    await page.reload();
    await testCaseDetailPage.expectStepCount(2);
  });

  test('Test case can be edited to change status to READY', async ({
    page, projectsPage, projectDetailPage, testCaseFormPage,
  }) => {
    const title = uniqueTestCaseTitle();
    const updatedTitle = uniqueTestCaseTitle();

    await setupSuite(page, projectsPage, projectDetailPage);
    await page.getByRole('button', { name: 'Create test case' }).click();
    await testCaseFormPage.fillTitle(title);
    await testCaseFormPage.fillExpectedResult('Result');
    await testCaseFormPage.addStep('Perform the test action');
    await testCaseFormPage.submit();
    await expect(page).toHaveURL(/\/test-cases\/\d+/);

    await page.getByRole('button', { name: 'Edit test case' }).click();
    await expect(page).toHaveURL(/\/edit/);
    await testCaseFormPage.fillTitle(updatedTitle);
    await testCaseFormPage.setStatus('READY');
    await testCaseFormPage.submit();

    await expect(page.getByText('Test case updated')).toBeVisible();
    await expect(page.getByRole('heading', { name: updatedTitle })).toBeVisible();
  });
});
