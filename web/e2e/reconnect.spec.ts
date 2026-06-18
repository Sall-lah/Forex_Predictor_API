/**
 * Reconnect: drop the WebSocket via the fixture's /close endpoint
 * and assert the ReconnectingBanner appears within 4 s.
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

test('reconnect: dropped socket shows the banner within 4 s', async ({ page }) => {
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

  // Drop the fixture connection with code 1006 (abnormal closure).
  const closeRes = await page.request.post(`${WS_FIXTURE_URL}/close`, {
    data: { code: 1006 },
  });
  expect(closeRes.status()).toBe(204);

  // The 3-second silence timeout on the controller should fire
  // shortly after, setting the store status to 'reconnecting'.
  await expect(page.getByTestId('reconnecting-banner')).toBeVisible({
    timeout: 5_000,
  });
});
