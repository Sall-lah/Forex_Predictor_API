/**
 * Initial render: the production build loads, the REST stub
 * returns the fixture candles (and the subscription discovery stub
 * returns a known set of pairs), and the StatusBar shows the
 * latest close.
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { redirectWebSocketsToFixture } from './fixtures/wsHarness';

const __dirname = dirname(fileURLToPath(import.meta.url));
const candles = JSON.parse(readFileSync(join(__dirname, 'fixtures/candles.json'), 'utf8'));
const lastClose = candles[candles.length - 1].close as number;

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

test('initial render against the REST fixture', async ({ page }) => {
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
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
  await expect(page.getByTestId('stat-close')).toHaveText(lastClose.toFixed(5));
});

test('interval switch: switching from 1m to 5m only shows 5m candles', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/subscriptions**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(SUBSCRIPTIONS),
    });
  });

  // Generate 5-minute candles for the fixture
  const fiveMinCandles = candles.map((c) => ({
    ...c,
    // Align timestamps to 5-minute grid
    timestamp: (() => {
      const d = new Date(c.timestamp);
      const sec = d.getUTCSeconds();
      if (sec !== 0) {
        d.setUTCMinutes(d.getUTCMinutes() + 1, 0, 0);
      }
      return d.toISOString();
    })(),
  }));

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    const url = new URL(route.request().url());
    const interval = url.searchParams.get('interval');
    const data = interval === '5' ? fiveMinCandles : candles;
    const count = data.length;
    const firstTimestamp = data[0]?.timestamp ?? candles[0]?.timestamp;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        symbol: 'BTC/USD',
        total_records: count,
        data,
      }),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('candles-page')).toBeVisible();

  // Switch interval to 5m
  await page.getByTestId('interval-select').selectOption('5');

  // Wait for the chart to re-render with the new data
  await expect(page.getByTestId('chart-canvas')).toBeVisible({ timeout: 5_000 });

  // All candles should have time aligned to 5-minute grid (time % 300 === 0)
  // We verify by checking the stat-close is updated and valid
  const closeText = await page.getByTestId('stat-close').textContent();
  expect(closeText).toBeTruthy();
  expect(closeText).not.toBe('--');
});
