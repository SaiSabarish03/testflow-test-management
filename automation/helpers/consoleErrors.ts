import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

const IGNORED_PATTERNS = [
  /Download the React DevTools/,
  /Warning: /,
  /\[HMR\]/,
  /\[vite\]/,
];

export function captureConsoleErrors(page: Page): () => string[] {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!IGNORED_PATTERNS.some((p) => p.test(text))) {
        errors.push(text);
      }
    }
  });

  page.on('pageerror', (err) => {
    errors.push(`[pageerror] ${err.message}`);
  });

  return () => errors;
}

export function expectNoConsoleErrors(getErrors: () => string[]) {
  const errors = getErrors();
  expect(errors, `Unexpected browser console errors:\n${errors.join('\n')}`).toHaveLength(0);
}
