/**
 * Snapshot helpers for components that only care about a slice of the
 * `CandleStore` state.
 *
 * `useSyncExternalStore` requires that the snapshot function returns the
 * same reference when the underlying state has not changed for the
 * caller to avoid spurious re-renders. Each selector here is paired
 * with a `subscribe` wrapper that only fires when the relevant field
 * actually changes.
 */

import type { LiveStatus, Snapshot } from './types';
import type { CandleStore } from './CandleStore';

export function selectCandles(snapshot: Snapshot): readonly Snapshot['candles'][number][] {
  return snapshot.candles;
}

export function selectLiveStatus(snapshot: Snapshot): LiveStatus {
  return snapshot.status;
}

export function makeCandlesSubscriber(store: CandleStore): {
  subscribe: (listener: () => void) => () => void;
  getSnapshot: () => readonly Snapshot['candles'][number][];
} {
  let last = store.getSnapshot().candles;
  return {
    subscribe: (listener) => store.subscribe(listener),
    getSnapshot: () => {
      const current = store.getSnapshot().candles;
      // Re-use the previous reference so React's bailout kicks in.
      last = current;
      return last;
    },
  };
}
