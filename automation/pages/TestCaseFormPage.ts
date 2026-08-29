import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { selectAntOption } from '../helpers/antDesign';

export class TestCaseFormPage {
  constructor(private page: Page) {}

  async fillTitle(title: string) {
    await this.page.getByLabel('Test case title').fill(title);
  }

  async fillExpectedResult(result: string) {
    await this.page.getByLabel('Expected result').fill(result);
  }

  async setStatus(status: 'DRAFT' | 'READY') {
    await selectAntOption(this.page, this.page.locator('body'), 'Status', status === 'DRAFT' ? 'Draft' : 'Ready');
  }

  async addStep(action: string) {
    await this.page.getByRole('button', { name: 'Add step' }).click();
    const steps = this.page.getByRole('textbox', { name: /Step \d+ action/ });
    const count = await steps.count();
    await steps.nth(count - 1).fill(action);
  }

  async removeStep(index: number) {
    // index is 1-based to match aria-label "Remove step N"
    await this.page.getByRole('button', { name: `Remove step ${index}` }).click();
  }

  async submit() {
    await this.page.getByRole('button', { name: /Create test case|Save test case/i }).click();
  }

  async expectValidationError(message: string) {
    await expect(this.page.getByText(message)).toBeVisible();
  }
}
