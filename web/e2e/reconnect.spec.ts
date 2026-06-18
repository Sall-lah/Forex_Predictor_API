/**
 * Reconnect: drop the WebSocket via the fixture's /close endpoint
 * and assert the ReconnectingBanner appears within 5 s.
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { redirectWebSocketsToFixture, WS_FIXTURE_HTTP_URL } from './fixtures/wsHarness';

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

test('reconnect: dropped Kraken socket shows the banner within 5 s', async ({ page }) => {
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
  await expect(page.getByTestId('candles-page')).toBeVisible();

  // Drop the fixture connection with code 1006 (abnormal closure).
  const closeRes = await page.request.post(`${WS_FIXTURE_HTTP_URL}/close`, {
    data: { code: 1006 },
  });
  expect(closeRes.status()).toBe(204);

  // The controller should detect the close and switch to
  // 'reconnecting' state.
  await expect(page.getByTestId('reconnecting-banner')).toBeVisible({
    timeout: 5_000,
  });
});
