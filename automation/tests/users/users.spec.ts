import { test, expect } from '../../fixtures/base';
import { captureConsoleErrors, expectNoConsoleErrors } from '../../helpers/consoleErrors';
import { uniqueUserEmail, uniqueUserName } from '../../test-data/generators';

test.describe('User Management', () => {
  test('ADMIN can create, edit, and deactivate a user', async ({ page, usersPage }) => {
    const getErrors = captureConsoleErrors(page);
    const name = uniqueUserName();
    const email = uniqueUserEmail();
    const updatedName = uniqueUserName();

    await usersPage.goto();
    await usersPage.createUser({ name, email, password: 'TestPass123!', role: 'QA_ENGINEER' });
    await usersPage.expectUserInTable(name);

    await usersPage.editUser(name, { name: updatedName, role: 'VIEWER' });
    await usersPage.expectUserInTable(updatedName);

    await usersPage.deactivateUser(updatedName);
    await expect(page.getByRole('button', { name: `Deactivate ${updatedName}` })).toHaveCount(0);

    expectNoConsoleErrors(getErrors);
  });

  test('User creation requires name, email, password, and role', async ({ page, usersPage }) => {
    await usersPage.goto();
    await page.getByRole('button', { name: 'Create user' }).click();
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText(/Please enter|Please select|required/i).first()).toBeVisible();
  });

  test('Users table shows search and role filter controls', async ({ page, usersPage }) => {
    await usersPage.goto();
    await expect(page.getByLabel('Search users')).toBeVisible();
    await expect(page.getByLabel('Filter by role').first()).toBeVisible();
    await expect(page.getByRole('table', { name: 'Users table' })).toBeVisible();
  });
});
