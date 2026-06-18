/**
 * `useCandles(pair, interval)` is the data hook for the candlestick
 * page. It:
 *
 * 1. Performs an initial REST fetch via `apiClient.get` and pushes the
 *    result to `candleStore.setCandles`.
 * 2. Calls `liveFeed.attach(pair, interval)` so the WebSocket mirrors
 *    the active REST query. The controller itself handles subsequent
 *    pair/interval switches (via its own `attach()`) and reconnect-
 *    time history refetches — see `LiveFeedController.fetchHistory`.
 * 3. Returns the store snapshot via `useSyncExternalStore` so React
 *    re-renders the consumer when the store changes.
 *
 * The hook intentionally does NOT poll: the WebSocket is the live
 * channel and the controller refills gaps on reconnect or pair switch.
 */

import { useEffect, useState, useSyncExternalStore } from 'react';
import { candleStore, liveFeed } from '../store';
import type { Candle, LiveStatus, Snapshot } from '../store';
import { get } from '../services/apiClient';

interface HistoricDataRecord {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface HistoricDataResponse {
  symbol: string;
  total_records: number;
  data: HistoricDataRecord[];
}

function toCandles(resp: HistoricDataResponse): Candle[] {
  return resp.data.map((r) => ({
    time: Math.floor(new Date(r.timestamp).getTime() / 1000),
    open: r.open,
    high: r.high,
    low: r.low,
    close: r.close,
    volume: r.volume,
  }));
}

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
        const resp = await get<HistoricDataResponse>(
          `/historic-data/live?${params.toString()}`
        );
        if (cancelled) return;
        candleStore.setCandles(toCandles(resp));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    }

    void fetchOnce();
    void liveFeed.attach(pair, interval);

    return () => {
      cancelled = true;
    };
  }, [pair, interval]);

  return {
    candles: snapshot.candles,
    status: snapshot.status,
    error,
  };
}
