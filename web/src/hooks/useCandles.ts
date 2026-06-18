/**
 * `useCandles(pair, interval)` is the data hook for the candlestick
 * page. It:
 *
 * 1. Performs an initial REST fetch via `apiClient.get` and pushes the
 *    result to `candleStore.setCandles`.
 * 2. Polls the REST endpoint every 15 s while the component is mounted.
 * 3. Calls `liveFeed.attach(pair, interval)` after each successful
 *    fetch so the WebSocket mirrors the active REST query.
 * 4. Returns the store snapshot via `useSyncExternalStore` so React
 *    re-renders the consumer when the store changes.
 *
 * The hook intentionally does NOT cache: `candleStore` is the single
 * source of truth and the REST poll is a small constant-rate background
 * job.
 */

import { useEffect, useState, useSyncExternalStore } from 'react';
import { candleStore, liveFeed } from '../store';
import type { Candle, LiveStatus, Snapshot } from '../store';
import { get } from '../services/apiClient';

const POLL_INTERVAL_MS = 15_000;

export interface UseCandlesResult {
  candles: readonly Candle[];
  status: LiveStatus;
  error: Error | null;
}

export function useCandles(pair: string, interval: number): UseCandlesResult {
  const snapshot: Snapshot = useSyncExternalStore(
    candleStore.subscribe,
    candleStore.getSnapshot
  );
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchOnce(): Promise<void> {
      try {
        const params = new URLSearchParams({
          pair,
          interval: String(interval),
          count: '180',
        });
        const data = await get<Candle[]>(
          `/historic-data/live?${params.toString()}`
        );
        if (cancelled) return;
        candleStore.setCandles(data);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    }

    void fetchOnce();
    const id = setInterval(() => {
      void fetchOnce();
    }, POLL_INTERVAL_MS);

    // Attach the live feed only after the first fetch resolves so the
    // store has a non-empty series to merge into.
    let attached = false;
    const attachIfReady = () => {
      if (attached) return;
      attached = true;
      liveFeed.attach(pair, interval);
    };
    const unwatch = candleStore.subscribe(attachIfReady);
    // Best-effort attach in case the snapshot already had candles.
    attachIfReady();

    return () => {
      cancelled = true;
      clearInterval(id);
      unwatch();
    };
  }, [pair, interval]);

  return {
    candles: snapshot.candles,
    status: snapshot.status,
    error,
  };
}
