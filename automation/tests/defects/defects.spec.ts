import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import { uniqueDefectTitle } from '../../test-data/generators';

const SEED_PROJECT = 'TestFlow Web';

test.describe('Defect Management', () => {
  test('ADMIN can create a defect and verify detail', async ({
    page, defectsPage, defectDetailPage,
  }) => {
    const getErrors = captureConsoleErrors(page);
    const title = uniqueDefectTitle();

    await defectsPage.goto();
    await defectsPage.createDefect({
      projectName: SEED_PROJECT,
      title,
      severity: 'MAJOR',
      priority: 'HIGH',
      description: 'E2E created defect',
    });

    await expect(page).toHaveURL(/\/defects\/\d+/);
    await expect(page.getByRole('heading', { name: title })).toBeVisible();
    await defectDetailPage.expectStatus('Open');

    expectNoConsoleErrors(getErrors);
  });

  test('Defect lifecycle: OPEN → IN_PROGRESS → RESOLVED → CLOSED', async ({
    page, defectsPage, defectDetailPage,
  }) => {
    const title = uniqueDefectTitle();

    await defectsPage.goto();
    await defectsPage.createDefect({ projectName: SEED_PROJECT, title, severity: 'MINOR', priority: 'LOW' });

    await defectDetailPage.expectStatus('Open');
    await defectDetailPage.expectTransitionButton('Start Work');
    await defectDetailPage.expectTransitionButton('Reject');

    await defectDetailPage.transition('Start Work');
    await defectDetailPage.expectStatus('In Progress');
    await defectDetailPage.expectTransitionButton('Resolve');

    await defectDetailPage.transition('Resolve');
    await defectDetailPage.expectStatus('Resolved');
    await defectDetailPage.expectTransitionButton('Close');

    await defectDetailPage.transition('Close');
    await defectDetailPage.expectStatus('Closed');
    await defectDetailPage.expectNoTransitionButton('Start Work');
    await defectDetailPage.expectNoTransitionButton('Resolve');
  });

  test('Defect can be rejected and reopened', async ({
    page, defectsPage, defectDetailPage,
  }) => {
    const title = uniqueDefectTitle();

    await defectsPage.goto();
    await defectsPage.createDefect({ projectName: SEED_PROJECT, title, severity: 'TRIVIAL', priority: 'LOW' });

    await defectDetailPage.transition('Reject');
    await defectDetailPage.expectStatus('Rejected');
    await defectDetailPage.expectTransitionButton('Reopen');

    await defectDetailPage.transition('Reopen');
    await defectDetailPage.expectStatus('Open');
  });

  test('ADMIN can edit defect severity and priority', async ({
    page, defectsPage, defectDetailPage,
  }) => {
    const title = uniqueDefectTitle();

    await defectsPage.goto();
    await defectsPage.createDefect({ projectName: SEED_PROJECT, title, severity: 'MINOR', priority: 'LOW' });

    await defectDetailPage.editDefect({ severity: 'BLOCKER', priority: 'CRITICAL' });
    await expect(page.getByText('Blocker')).toBeVisible();
    await expect(page.getByText('Critical')).toBeVisible();
  });

  test('Defect creation requires project and title', async ({ page, defectsPage }) => {
    await defectsPage.goto();
    await page.getByRole('button', { name: 'Create defect' }).click();
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText('Project is required')).toBeVisible();
  });
});
