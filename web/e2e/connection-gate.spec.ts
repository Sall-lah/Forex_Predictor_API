/**
 * Connection gate: pair and interval selects are disabled while the
 * WebSocket is connecting or reconnecting, with a dimmed visual
 * treatment and a status label. The label is suppressed during the
 * initial 'idle' state.
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  redirectWebSocketsToFixture,
  WS_FIXTURE_HTTP_URL,
} from './fixtures/wsHarness';

const __dirname = dirname(fileURLToPath(import.meta.url));
const candles = JSON.parse(
  readFileSync(join(__dirname, 'fixtures/candles.json'), 'utf8')
);

const SUBSCRIPTIONS = {
  subscriptions: [
    { pair: 'BTC/USD', intervals: [1, 5, 15, 60, 240] },
    { pair: 'ETH/USD', intervals: [1, 5, 15, 60, 240] },
  ],
};

const HISTORIC_RESPONSE = {
  symbol: 'BTC/USD',
  total_records: candles.length,
  data: candles,
};

test('controls are disabled before WebSocket opens and enabled after', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/subscriptions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(SUBSCRIPTIONS),
    });
  });

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(HISTORIC_RESPONSE),
    });
  });

  await page.goto('/');

  // Controls should be disabled initially (status starts at 'idle')
  await expect(page.getByTestId('pair-select')).toBeDisabled();
  await expect(page.getByTestId('interval-select')).toBeDisabled();

  // Controls should become enabled once the WebSocket opens
  await expect(page.getByTestId('pair-select')).toBeEnabled({ timeout: 5_000 });
  await expect(page.getByTestId('interval-select')).toBeEnabled({ timeout: 5_000 });

  // No controls-status label should be in the DOM when live
  await expect(page.getByTestId('controls-status')).toHaveCount(0);

  // Controls should be at full opacity when live
  const pairSelect = page.getByTestId('pair-select');
  const opacity = await pairSelect.evaluate((el) => getComputedStyle(el).opacity);
  expect(opacity).toBe('1');
});

test('controls are re-disabled on reconnect with "Reconnecting…" label', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/subscriptions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(SUBSCRIPTIONS),
    });
  });

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(HISTORIC_RESPONSE),
    });
  });

  await page.goto('/');

  // Wait for controls to become enabled
  await expect(page.getByTestId('pair-select')).toBeEnabled({ timeout: 5_000 });

  // Drop the socket to trigger a reconnect
  const closeRes = await page.request.post(`${WS_FIXTURE_HTTP_URL}/close`, {
    data: { code: 1006 },
  });
  expect(closeRes.status()).toBe(204);

  // Controls should be re-disabled
  await expect(page.getByTestId('pair-select')).toBeDisabled({ timeout: 5_000 });
  await expect(page.getByTestId('interval-select')).toBeDisabled({ timeout: 5_000 });

  // The controls-status label should appear with "Reconnecting…"
  await expect(page.getByTestId('controls-status')).toBeVisible({ timeout: 5_000 });
  await expect(page.getByTestId('controls-status')).toHaveText('Reconnecting…');

  // Wait for the reconnect to succeed
  await expect(page.getByTestId('pair-select')).toBeEnabled({ timeout: 5_000 });
  await expect(page.getByTestId('interval-select')).toBeEnabled({ timeout: 5_000 });

  // Label should be removed
  await expect(page.getByTestId('controls-status')).toHaveCount(0);
});
