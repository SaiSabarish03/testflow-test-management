import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class CreateRunPage {
  constructor(private page: Page) {}

  private async dismissNotifications() {
    const closeLinks = this.page.getByRole('link', { name: 'Close' });
    while (await closeLinks.count() > 0) {
      await closeLinks.first().click();
    }
  }

  async fillRunName(name: string) {
    await this.page.getByLabel('Run name').fill(name);
  }

  async fillEnvironment(env: string) {
    await this.page.getByLabel('Environment').fill(env);
  }

  async selectFirstTestCase() {
    // Wait for the table to have at least one row
    await this.page.locator('.ant-table-row').first().waitFor({ state: 'visible' });
    // Row checkboxes: index 0 is select-all header, index 1 is first data row
    await this.page.locator('.ant-table-cell input[type="checkbox"]').nth(1).click();
  }

  async selectTestCase(title: string) {
    const row = this.page.getByRole('row', { name: new RegExp(title, 'i') });
    await row.getByRole('checkbox').check();
  }

  async selectAllTestCases() {
    await this.page.locator('.ant-table-row').first().waitFor({ state: 'visible' });
    await this.page.locator('.ant-table-cell input[type="checkbox"]').first().click();
  }

  async createRun() {
    await this.page.getByRole('button', { name: 'Create Test Run' }).click();
    await expect(this.page.getByText('Test run created')).toBeVisible();
    await this.dismissNotifications();
  }

  async expectNoReadyCases() {
    await expect(this.page.getByText('No READY test cases found in this project')).toBeVisible();
  }

  async expectOnlyReadyCasesVisible() {
    const draftTags = this.page.getByText('Draft');
    const deprecatedTags = this.page.getByText('Deprecated');
    await expect(draftTags).toHaveCount(0);
    await expect(deprecatedTags).toHaveCount(0);
  }
}
