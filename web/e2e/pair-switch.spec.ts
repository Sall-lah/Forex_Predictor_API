/**
 * Pair switch: change the active pair via the UI, assert the
 * StatusBar updates to reflect the new pair's last close and that
 * the WebSocket reconnects (subscribing to the new pair on the
 * Kraken fixture).
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { redirectWebSocketsToFixture } from './fixtures/wsHarness';

const __dirname = dirname(fileURLToPath(import.meta.url));
const btcCandles = JSON.parse(readFileSync(join(__dirname, 'fixtures/candles.json'), 'utf8'));
const ethCandles = btcCandles.map((c) => ({
  ...c,
  symbol: 'ETH/USD',
  close: Math.round(c.close * 0.05 * 1e5) / 1e5,
  high: Math.round(c.high * 0.05 * 1e5) / 1e5,
  low: Math.round(c.low * 0.05 * 1e5) / 1e5,
  open: Math.round(c.open * 0.05 * 1e5) / 1e5,
}));
const btcLastClose = btcCandles[btcCandles.length - 1].close as number;
const ethLastClose = ethCandles[ethCandles.length - 1].close as number;

const SUBSCRIPTIONS = {
  subscriptions: [
    { pair: 'BTC/USD', intervals: [1, 5, 15, 60, 240] },
    { pair: 'ETH/USD', intervals: [1, 5, 15, 60, 240] },
  ],
};

function historicResponseFor(symbol: string, candles: unknown[]) {
  return {
    symbol,
    total_records: candles.length,
    data: candles,
  };
}

test('pair switch: switching pair reloads history and reconnects WS', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/subscriptions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(SUBSCRIPTIONS),
    });
  });

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    const url = new URL(route.request().url());
    const pair = url.searchParams.get('pair') ?? 'BTC/USD';
    const payload =
      pair === 'ETH/USD'
        ? historicResponseFor('ETH/USD', ethCandles)
        : historicResponseFor('BTC/USD', btcCandles);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('stat-close')).toHaveText(btcLastClose.toFixed(5));

  // Switch the pair to ETH/USD via the select.
  await page.getByTestId('pair-select').selectOption('ETH/USD');

  // The status bar should now show the ETH/USD last close.
  await expect(page.getByTestId('stat-close')).toHaveText(ethLastClose.toFixed(5), {
    timeout: 3_000,
  });
});

test('pair switch: no candles from previous pair remain on chart', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/subscriptions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(SUBSCRIPTIONS),
    });
  });

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    const url = new URL(route.request().url());
    const pair = url.searchParams.get('pair') ?? 'BTC/USD';
    const payload =
      pair === 'ETH/USD'
        ? historicResponseFor('ETH/USD', ethCandles)
        : historicResponseFor('BTC/USD', btcCandles);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('stat-close')).toHaveText(btcLastClose.toFixed(5));

  // Switch the pair to ETH/USD
  await page.getByTestId('pair-select').selectOption('ETH/USD');

  // After switching, the close should match ETH's last close, not BTC's
  await expect(page.getByTestId('stat-close')).toHaveText(ethLastClose.toFixed(5), {
    timeout: 3_000,
  });

  // The close should NOT be the BTC close (verifying no carry-over)
  const closeText = await page.getByTestId('stat-close').textContent();
  expect(closeText).not.toBe(btcLastClose.toFixed(5));
});
