import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class ProjectDetailPage {
  constructor(private page: Page) {}

  async editProject(name: string, description?: string) {
    await this.page.getByRole('button', { name: 'Edit project' }).click();
    await this.page.getByLabel('Project name').fill(name);
    if (description !== undefined) await this.page.getByLabel('Project description').fill(description);
    await this.page.getByRole('button', { name: 'Save' }).click();
    await expect(this.page.getByText('Project updated')).toBeVisible();
  }

  async archiveProject() {
    await this.page.getByRole('button', { name: 'Archive project' }).click();
    // Popconfirm — click the danger "Archive" button inside the popover
    await this.page.getByRole('button', { name: 'Archive' }).last().click();
    await expect(this.page.getByText('Project archived')).toBeVisible();
  }

  async openSuitesTab() {
    await this.page.getByRole('tab', { name: 'Test Suites' }).click();
  }

  async openRunsTab() {
    await this.page.getByRole('tab', { name: 'Test Runs' }).click();
  }

  async expectStatus(status: string) {
    await expect(this.page.getByText(status).first()).toBeVisible();
  }

  async createSuite(name: string, description?: string) {
    await this.page.getByRole('button', { name: 'Create suite' }).click();
    await this.page.getByLabel('Suite name').fill(name);
    if (description) await this.page.getByLabel('Suite description').fill(description);
    await this.page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(this.page.getByText('Suite created')).toBeVisible();
  }

  async openSuite(name: string) {
    await this.page.getByRole('button', { name: `Open suite ${name}` }).click();
  }

  async editSuite(currentName: string, newName: string) {
    await this.page.getByRole('button', { name: `Edit suite ${currentName}` }).click();
    await this.page.getByLabel('Suite name').fill(newName);
    await this.page.getByRole('button', { name: 'Save' }).click();
    await expect(this.page.getByText('Suite updated')).toBeVisible();
  }

  async deleteSuite(name: string) {
    await this.page.getByRole('button', { name: `Delete suite ${name}` }).click();
    await this.page.getByRole('button', { name: 'Delete' }).last().click();
    await expect(this.page.getByText('Suite deleted')).toBeVisible();
  }

  async clickNewRun() {
    await this.page.getByRole('button', { name: 'Create Test Run' }).click();
  }
}
