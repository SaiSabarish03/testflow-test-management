import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { dismissNotifications } from '../helpers/antDesign';

export class RunDetailPage {
  constructor(private page: Page) {}

  private async dismissNotifications() {
    await dismissNotifications(this.page);
  }

  async startRun() {
    await this.dismissNotifications();
    await this.page.getByRole('button', { name: 'Start Run' }).click();
    await expect(this.page.getByText('Run started')).toBeVisible();
    await this.dismissNotifications();
  }

  async completeRun() {
    await this.dismissNotifications();
    await this.page.getByRole('button', { name: 'Complete Run' }).click();
    await expect(this.page.getByText('Run completed')).toBeVisible();
    await this.dismissNotifications();
  }

  async abortRun() {
    await this.page.getByRole('button', { name: 'Abort Run' }).click();
    await this.page.getByRole('button', { name: 'Abort' }).last().click();
    await expect(this.page.getByText('Run aborted')).toBeVisible();
  }

  async recordResult(testCaseTitle: string, result: 'Pass' | 'Fail' | 'Blocked', actualResult?: string) {
    const row = this.page.getByRole('row', { name: new RegExp(testCaseTitle, 'i') });
    if (actualResult) {
      await row.getByLabel(new RegExp(`Actual result for ${testCaseTitle}`, 'i')).fill(actualResult);
    }
    await row.getByRole('button', { name: result }).click();
    await expect(this.page.getByText(`Result recorded`)).toBeVisible();
    await this.dismissNotifications();
  }

  async recordFirstResult(result: 'Pass' | 'Fail' | 'Blocked', actualResult?: string) {
    const rows = this.page.locator('.ant-table-row');
    const firstRow = rows.first();
    if (actualResult) {
      await firstRow.getByPlaceholder('Actual result (optional)').fill(actualResult);
    }
    await firstRow.getByRole('button', { name: result }).click();
    await expect(this.page.getByText('Result recorded')).toBeVisible();
    await this.dismissNotifications();
  }

  async expectStatus(status: string) {
    // Status tag appears in the header area
    await expect(this.page.getByText(status).first()).toBeVisible();
  }

  async expectSummaryVisible() {
    await expect(this.page.getByText('Total')).toBeVisible();
    await expect(this.page.getByText('Passed')).toBeVisible();
  }

  async expectNotRunAlert() {
    await expect(this.page.getByText(/result\(s\) still NOT_RUN/)).toBeVisible();
  }

  async expectNoActionButtons() {
    await expect(this.page.getByRole('button', { name: 'Start Run' })).toHaveCount(0);
    await expect(this.page.getByRole('button', { name: 'Complete Run' })).toHaveCount(0);
    await expect(this.page.getByRole('button', { name: 'Abort Run' })).toHaveCount(0);
  }
}
