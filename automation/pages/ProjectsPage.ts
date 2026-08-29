import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class ProjectsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/projects');
  }

  async createProject(name: string, key: string, description?: string) {
    await this.page.getByRole('button', { name: 'Create project' }).click();
    await this.page.getByLabel('Project name').fill(name);
    await this.page.getByLabel('Project key').fill(key);
    if (description) await this.page.getByLabel('Project description').fill(description);
    await this.page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(this.page.getByText('Project created')).toBeVisible();
  }

  async openProject(name: string) {
    await this.page.getByLabel('Search projects').fill(name);
    await this.page.getByRole('button', { name: `Open project ${name}` }).click();
  }

  async expectProjectInTable(name: string) {
    await this.page.getByLabel('Search projects').fill(name);
    await expect(this.page.getByRole('button', { name: `Open project ${name}` })).toBeVisible();
  }
}
