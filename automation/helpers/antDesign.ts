import type { Locator, Page } from '@playwright/test';
import { expect } from '@playwright/test';

export async function selectAntOption(page: Page, root: Locator, label: string, option: string | RegExp) {
  const combo = root.getByRole('combobox', { name: label, exact: true });
  await combo.evaluate((element) => element.scrollIntoView({ block: 'center', inline: 'nearest' }));
  const visibleControl = root.locator(`div[aria-label="${label.replace(/"/g, '\\"')}"]`);
  await visibleControl.click();
  await expect(combo).toHaveAttribute('aria-expanded', 'true');

  const activeDropdown = page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)').last();
  await activeDropdown.waitFor({ state: 'visible' });

  const optionElements = activeDropdown.locator('.ant-select-item-option');
  await optionElements.first().waitFor({ state: 'visible' });

  const options = await optionElements.evaluateAll((elements) =>
    elements.map((element) => ({
      id: element.id,
      name: element.getAttribute('aria-label') ?? element.textContent?.trim() ?? '',
    })),
  );
  const targetIndex = options.findIndex(({ name }) =>
    typeof option === 'string' ? name === option : option.test(name),
  );
  if (targetIndex < 0) {
    throw new Error(`Option "${option}" not found for "${label}"`);
  }

  await optionElements.nth(targetIndex).click();
  await expect(combo).toHaveAttribute('aria-expanded', 'false');
}

export async function dismissNotifications(page: Page) {
  const closeLinks = page.getByRole('link', { name: 'Close' }).or(page.getByLabel('Close'));
  const list = await closeLinks.all();
  for (const link of list) {
    if (await link.isVisible().catch(() => false)) {
      await link.click({ force: true }).catch(() => {});
    }
  }
}

