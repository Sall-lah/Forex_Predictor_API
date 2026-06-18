/**
 * Test helpers: redirect browser WebSockets to a local fixture
 * server. Used by every spec that needs a deterministic
 * WebSocket source.
 */

import type { Page } from '@playwright/test';

export const WS_FIXTURE_URL = 'ws://localhost:5180';

/**
 * Install a `WebSocket` constructor override on the page that
 * transparently rewrites `/ws/candles` URLs to point at the
 * local fixture server. Other WebSocket targets pass through
 * untouched.
 */
export async function redirectWebSocketsToFixture(page: Page): Promise<void> {
  await page.addInitScript(
    ({ target }) => {
      const original = window.WebSocket;
      function PatchedWS(
        this: WebSocket,
        url: string | URL,
        protocols?: string | string[]
      ) {
        const asString = typeof url === 'string' ? url : url.toString();
        if (asString.includes('/ws/candles')) {
          const rewritten = `${target}/ws/candles`;
          return new original(rewritten, protocols);
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
    { target: WS_FIXTURE_URL }
  );
}
