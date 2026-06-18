/**
 * Initial render: the production build loads, the REST stub
 * returns the fixture candles, and the StatusBar shows the
 * latest close.
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { redirectWebSocketsToFixture } from './fixtures/wsHarness';

const __dirname = dirname(fileURLToPath(import.meta.url));
const candles = JSON.parse(
  readFileSync(join(__dirname, 'fixtures/candles.json'), 'utf8')
);
const lastClose = candles[candles.length - 1].close as number;

test('initial render against the REST fixture', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(candles),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('candles-page')).toBeVisible();
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
  await expect(page.getByTestId('stat-close')).toHaveText(
    lastClose.toFixed(5)
  );
});
