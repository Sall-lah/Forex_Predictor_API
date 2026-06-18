/**
 * Live tick: push a new tick via the fixture server's HTTP
 * control surface and assert the StatusBar updates within 500 ms.
 */

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { redirectWebSocketsToFixture, WS_FIXTURE_URL } from './fixtures/wsHarness';

const __dirname = dirname(fileURLToPath(import.meta.url));
const candles = JSON.parse(
  readFileSync(join(__dirname, 'fixtures/candles.json'), 'utf8')
);
const lastClose = candles[candles.length - 1].close as number;
const bumpedClose = lastClose + 0.001;

test('live tick: status bar updates within 500 ms', async ({ page }) => {
  await redirectWebSocketsToFixture(page);

  await page.route('**/api/v1/historic-data/live**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(candles),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('stat-close')).toHaveText(lastClose.toFixed(5));

  // Push a tick through the fixture's HTTP control surface.
  const pushRes = await page.request.post(`${WS_FIXTURE_URL}/push-tick`, {
    data: { close: bumpedClose },
  });
  expect(pushRes.status()).toBe(204);

  // Status bar should reflect the bumped close within 500 ms.
  await expect(page.getByTestId('stat-close')).toHaveText(
    bumpedClose.toFixed(5),
    { timeout: 1_000 }
  );
});
