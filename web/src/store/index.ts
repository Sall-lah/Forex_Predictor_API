/**
 * Singleton store + live-feed wiring.
 *
 * The `candleStore` is a module-level instance, instantiated once at
 * import time. Components should `import { candleStore } from
 * './store'` and use `useSyncExternalStore` to subscribe to its
 * snapshot.
 *
 * The `LiveFeedController` is also instantiated once and bound to the
 * store; the `useCandles` hook calls `liveFeed.attach(pair, interval)`
 * to drive it.
 */

import { CandleStore } from './CandleStore';
import { LiveFeedController } from './LiveFeedController';

export const candleStore = new CandleStore();
export const liveFeed = new LiveFeedController(candleStore);

candleStore.bindController(() => liveFeed.detach());

export type { Candle, LiveStatus, Snapshot } from './types';
export { CandleStore } from './CandleStore';
export { LiveFeedController } from './LiveFeedController';
export { selectCandles, selectLiveStatus } from './selectors';
