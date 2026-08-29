import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { selectAntOption, dismissNotifications } from '../helpers/antDesign';

export class UsersPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/users');
  }

  async createUser(opts: { name: string; email: string; password: string; role: string }) {
    await this.page.getByRole('button', { name: 'Create user' }).click();
    const dialog = this.page.getByRole('dialog', { name: 'New User' });
    await dialog.getByLabel('Name').fill(opts.name);
    await dialog.getByLabel('Email').fill(opts.email);
    await dialog.getByLabel('Password').fill(opts.password);
    const roleLabel = opts.role === 'QA_ENGINEER' ? 'QA Engineer' : opts.role === 'ADMIN' ? 'Admin' : opts.role === 'VIEWER' ? 'Viewer' : opts.role;
    await selectAntOption(this.page, dialog, 'Role', roleLabel);
    await dialog.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(this.page.getByText('User created')).toBeVisible();
    await dismissNotifications(this.page);
  }

  async editUser(currentName: string, updates: { name?: string; role?: string }) {
    await this.page.getByRole('button', { name: `Edit ${currentName}` }).click();
    const dialog = this.page.getByRole('dialog', { name: 'Edit User' });
    if (updates.name) await dialog.getByLabel('Name').fill(updates.name);
    if (updates.role) {
      const roleLabel = updates.role === 'QA_ENGINEER' ? 'QA Engineer' : updates.role === 'ADMIN' ? 'Admin' : updates.role === 'VIEWER' ? 'Viewer' : updates.role;
      await selectAntOption(this.page, dialog, 'Role', roleLabel);
    }
    await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(this.page.getByText('User updated')).toBeVisible();
    await dismissNotifications(this.page);
  }

  async deactivateUser(name: string) {
    await this.page.getByRole('button', { name: `Deactivate ${name}` }).click();
    await this.page.getByRole('button', { name: 'Deactivate' }).last().click();
    await expect(this.page.getByText(`${name} deactivated`)).toBeVisible();
    await dismissNotifications(this.page);
  }

  async expectUserInTable(name: string) {
    await expect(this.page.getByRole('cell', { name, exact: true })).toBeVisible();
  }
}
