/**
 * Smoke test: the production build loads, the document title is set,
 * and the chart canvas is mounted.
 */

import { test, expect } from '@playwright/test';

test('smoke: page loads and chart canvas is present', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle('Forex Candles');
  await expect(page.getByTestId('candles-page')).toBeVisible();
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
});
