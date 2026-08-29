import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.getByLabel('Email').fill(email);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Sign in' }).click();
  }

  async expectDashboard() {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }

  async expectError(text: string) {
    await expect(this.page.getByTestId('login-error')).toContainText(text);
  }

  async expectOnLoginPage() {
    await expect(this.page).toHaveURL(/\/login/);
  }
}
