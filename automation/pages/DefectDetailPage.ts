import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { selectAntOption, dismissNotifications } from '../helpers/antDesign';

export class DefectDetailPage {
  constructor(private page: Page) {}

  async transition(label: string) {
    await this.page.getByRole('button', { name: label }).click();
    await expect(this.page.getByText(/Status updated/).first()).toBeVisible();
    await dismissNotifications(this.page);
  }

  async editDefect(opts: { severity?: string; priority?: string; assigneeName?: string }) {
    await this.page.getByRole('button', { name: 'Edit defect' }).click();

    const dialog = this.page.getByRole('dialog', { name: 'Edit Defect' });

    if (opts.severity) {
      await selectAntOption(this.page, dialog, 'Severity', new RegExp(`^${opts.severity}$`, 'i'));
    }
    if (opts.priority) {
      await selectAntOption(this.page, dialog, 'Priority', new RegExp(`^${opts.priority}$`, 'i'));
    }
    if (opts.assigneeName) {
      await selectAntOption(this.page, dialog, 'Assign to', new RegExp(opts.assigneeName));
    }

    await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(this.page.getByText('Defect updated')).toBeVisible();
    await dismissNotifications(this.page);
  }

  async expectStatus(status: string) {
    await expect(this.page.getByRole('main').getByText(new RegExp(`^${status}$`, 'i')).first()).toBeVisible({ timeout: 10000 });
  }

  async expectTransitionButton(label: string) {
    await expect(this.page.getByRole('button', { name: label })).toBeVisible();
  }

  async expectNoTransitionButton(label: string) {
    await expect(this.page.getByRole('button', { name: label })).toHaveCount(0);
  }
}
