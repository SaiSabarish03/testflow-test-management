import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class TestCaseDetailPage {
  constructor(private page: Page) {}

  async markReady() {
    await this.page.getByRole('button', { name: 'Mark as Ready' }).click();
    await expect(this.page.getByText('Test case marked as Ready')).toBeVisible();
  }

  async clickEdit() {
    await this.page.getByRole('button', { name: 'Edit test case' }).click();
  }

  async deprecate() {
    await this.page.getByRole('button', { name: 'Deprecate test case' }).click();
    await this.page.getByRole('button', { name: 'Deprecate' }).last().click();
    await expect(this.page.getByText('Test case deprecated')).toBeVisible();
  }

  async expectStatus(status: string) {
    await expect(this.page.getByText(status).first()).toBeVisible();
  }

  async expectStepCount(count: number) {
    const steps = this.page.getByLabel('Test steps').locator('li');
    await expect(steps).toHaveCount(count);
  }
}
