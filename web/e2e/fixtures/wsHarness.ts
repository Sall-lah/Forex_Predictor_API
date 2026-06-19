/**
 * Test helpers: redirect browser WebSockets to a local Kraken v2
 * fixture server. Used by every spec that needs a deterministic
 * WebSocket source.
 *
 * The frontend connects to `wss://ws.kraken.com/v2` (the real
 * Kraken public WS endpoint). The harness transparently rewrites
 * that URL to point at a local Node fixture so e2e tests can run
 * offline. All other WebSocket targets pass through untouched.
 */

import type { Page } from '@playwright/test';

/** WebSocket endpoint the harness redirects to. */
export const WS_FIXTURE_URL = 'ws://localhost:5180';
/** HTTP control surface (push-tick / close / healthz) on the same fixture. */
export const WS_FIXTURE_HTTP_URL = 'http://localhost:5180';
/** The real Kraken endpoint the frontend would connect to. */
export const KRAKEN_WS_URL = 'wss://ws.kraken.com/v2';

/**
 * Install a `WebSocket` constructor override on the page that
 * transparently rewrites `wss://ws.kraken.com/v2` URLs to point at
 * the local Kraken fixture server. Other WebSocket targets pass
 * through untouched.
 */
export async function redirectWebSocketsToFixture(page: Page): Promise<void> {
  await page.addInitScript(
    ({ target, krakenUrl }) => {
      const original = window.WebSocket;
      function PatchedWS(this: WebSocket, url: string | URL, protocols?: string | string[]) {
        const asString = typeof url === 'string' ? url : url.toString();
        if (asString === krakenUrl || asString.startsWith(`${krakenUrl}/`)) {
          return new original(target, protocols);
        }
        return new original(url as string, protocols);
      }
      PatchedWS.prototype = original.prototype;
      // Preserve constants used by callers.
      Object.assign(PatchedWS, {
        CONNECTING: original.CONNECTING,
        OPEN: original.OPEN,
        CLOSING: original.CLOSING,
        CLOSED: original.CLOSED,
      });
      (window as unknown as { WebSocket: unknown }).WebSocket = PatchedWS;
    },
    { target: WS_FIXTURE_URL, krakenUrl: KRAKEN_WS_URL },
  );
}
