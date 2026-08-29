import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { selectAntOption, dismissNotifications } from '../helpers/antDesign';

export class DefectsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/defects');
  }

  async createDefect(opts: {
    projectName: string;
    title: string;
    severity: string;
    priority: string;
    description?: string;
  }) {
    await this.page.getByRole('button', { name: 'Create defect' }).click();

    const dialog = this.page.getByRole('dialog', { name: 'New Defect' });

    await selectAntOption(this.page, dialog, 'Project', new RegExp(`^${opts.projectName}$`, 'i'));

    await dialog.getByLabel('Defect title').fill(opts.title);
    if (opts.description) await dialog.getByLabel('Description').fill(opts.description);

    await selectAntOption(this.page, dialog, 'Severity', new RegExp(`^${opts.severity}$`, 'i'));
    await selectAntOption(this.page, dialog, 'Priority', new RegExp(`^${opts.priority}$`, 'i'));

    await dialog.getByRole('button', { name: 'Create', exact: true }).click();
    // After creation, navigates to defect detail
    await expect(this.page).toHaveURL(/\/defects\/\d+/);
    await dismissNotifications(this.page);
  }

  async openDefect(title: string) {
    await this.page.getByRole('button', { name: `Open defect ${title}` }).click();
  }

  async expectDefectInTable(title: string) {
    await expect(this.page.getByRole('button', { name: `Open defect ${title}` })).toBeVisible();
  }
}
