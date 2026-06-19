/**
 * `useCandles(pair, interval)` is the data hook for the candlestick
 * page. It:
 *
 * 1. Calls `liveFeed.attach(pair, interval)` so the controller handles
 *    history fetching and the WebSocket lifecycle — see
 *    `LiveFeedController.fetchHistoryAndOpen`.
 * 2. Returns the store snapshot via `useSyncExternalStore` so React
 *    re-renders the consumer when the store changes.
 *
 * The hook intentionally does NOT poll or fetch REST data independently:
 * the controller is the single source of truth for history, and the
 * WebSocket is the live channel.
 */

import { useEffect, useSyncExternalStore } from 'react';
import { candleStore, liveFeed } from '../store';
import type { Candle, LiveStatus, Snapshot } from '../store';

export interface UseCandlesResult {
  candles: readonly Candle[];
  status: LiveStatus;
}

export function useCandles(pair: string, interval: number): UseCandlesResult {
  const snapshot: Snapshot = useSyncExternalStore(
    candleStore.subscribe,
    candleStore.getSnapshot
  );

  useEffect(() => {
    candleStore.clear();
    void liveFeed.attach(pair, interval);
  }, [pair, interval]);

  return {
    candles: snapshot.candles,
    status: snapshot.status,
  };
}
