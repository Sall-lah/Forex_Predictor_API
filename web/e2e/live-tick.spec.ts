/**
 * Live tick: push a Kraken v2 OHLC update via the fixture's HTTP
 * control surface and assert the StatusBar updates within 1 s.
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
const lastClose = candles[candles.length - 1].close as number;
const bumpedClose = lastClose + 0.001;

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

test('live tick: status bar updates within 1 s', async ({ page }) => {
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
  await expect(page.getByTestId('stat-close')).toHaveText(lastClose.toFixed(5));

  // Push a Kraken v2 OHLC update through the fixture's HTTP control surface.
  const pushRes = await page.request.post(`${WS_FIXTURE_HTTP_URL}/push-tick`, {
    data: { close: bumpedClose, symbol: 'BTC/USD', interval: 60 },
  });
  expect(pushRes.status()).toBe(204);

  // Status bar should reflect the bumped close within 1 s.
  await expect(page.getByTestId('stat-close')).toHaveText(
    bumpedClose.toFixed(5),
    { timeout: 1_000 }
  );
});
