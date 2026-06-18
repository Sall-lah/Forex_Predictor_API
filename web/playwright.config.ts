/**
 * Playwright configuration for the candlestick e2e suite.
 *
 * Two background services are launched for the test run:
 *   1. `vite preview` serves the production build on port 4173 (the
 *      test runner's baseURL).
 *   2. `node e2e/fixtures/wsServer.mjs` runs the local Kraken v2
 *      WebSocket fixture on port 5180. The browser-side tests
 *      redirect `wss://ws.kraken.com/v2` to `ws://localhost:5180`
 *      via the init-script helper in `e2e/fixtures/wsHarness.ts`.
 *
 * The backend REST API is mocked in-test via `page.route()` for
 * `/api/v1/historic-data/live` and `/api/v1/subscriptions`.
 */

import { defineConfig, devices } from '@playwright/test';

const PORT = 4173;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  testMatch: /.*\.spec\.ts$/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: BASE_URL,
    headless: true,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'npm run build && npx vite preview --port 4173 --strictPort',
      url: BASE_URL,
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'node e2e/fixtures/wsServer.mjs',
      url: 'http://localhost:5180/healthz',
      timeout: 30_000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
