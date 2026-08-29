import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class SuiteDetailPage {
  constructor(private page: Page) {}

  async createTestCase(title: string, expectedResult: string) {
    await this.page.getByRole('button', { name: 'Create test case' }).click();
    await expect(this.page).toHaveURL(/suites\/\d+\/test-cases\/new/);
    await this.page.getByLabel('Test case title').fill(title);
    await this.page.getByLabel('Expected result').fill(expectedResult);
    await this.page.getByRole('button', { name: 'Create Test Case' }).click();
    await expect(this.page.getByText('Test case created')).toBeVisible();
  }

  async openTestCase(title: string) {
    await this.page.getByRole('button', { name: `Open test case ${title}` }).click();
  }

  async deprecateTestCase(title: string) {
    await this.page.getByRole('button', { name: `Deprecate ${title}` }).click();
    await this.page.getByRole('button', { name: 'Deprecate' }).last().click();
    await expect(this.page.getByText('deprecated')).toBeVisible();
  }

  async expectTestCaseInTable(title: string) {
    await expect(this.page.getByRole('button', { name: `Open test case ${title}` })).toBeVisible();
  }
}
