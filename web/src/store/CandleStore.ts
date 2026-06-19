/**
 * `CandleStore` is the single source of truth for candle data and
 * WebSocket connection state on the candlestick page.
 *
 * It implements the shape required by `useSyncExternalStore`:
 *   - `subscribe(listener)` registers a callback and returns an unsubscribe
 *     function
 *   - `getSnapshot()` returns a referentially stable object that only
 *     changes when one of the three tracked fields (`candles`, `status`,
 *     `lastUpdatedAt`) changes
 *
 * The store is also responsible for keeping the candle series normalised
 * (sorted ascending by `time` with duplicate times collapsed to the
 * latest write) so the chart can trust that `setData` receives a
 * monotonic series.
 */

import type { Candle, LiveStatus, Snapshot } from './types';

const EMPTY_SNAPSHOT: Snapshot = Object.freeze({
  candles: Object.freeze([]) as readonly Candle[],
  status: 'idle',
  lastUpdatedAt: null,
});

function normalise(candles: readonly Candle[]): readonly Candle[] {
  if (candles.length === 0) return candles;
  const byTime = new Map<number, Candle>();
  for (const c of candles) {
    byTime.set(c.time, c);
  }
  return Array.from(byTime.values()).sort((a, b) => a.time - b.time);
}

function candlesEqual(
  a: readonly Candle[],
  b: readonly Candle[]
): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    const x = a[i];
    const y = b[i];
    if (
      x.time !== y.time ||
      x.open !== y.open ||
      x.high !== y.high ||
      x.low !== y.low ||
      x.close !== y.close ||
      x.volume !== y.volume
    ) {
      return false;
    }
  }
  return true;
}

type Listener = () => void;

export class CandleStore {
  private candles: readonly Candle[] = EMPTY_SNAPSHOT.candles;
  private status: LiveStatus = 'idle';
  private lastUpdatedAt: number | null = null;
  private snapshot: Snapshot = EMPTY_SNAPSHOT;
  private listeners: Set<Listener> = new Set();
  private destroyed = false;

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  getSnapshot = (): Snapshot => this.snapshot;

  getCandles = (): readonly Candle[] => this.candles;
  getStatus = (): LiveStatus => this.status;

  setCandles(candles: readonly Candle[]): void {
    // Merge REST data into existing candles: only add candles that
    // don't already exist. WebSocket ticks are the source of truth
    // for candles already in the store (more up-to-date OHLCV values).
    const existingByTime = new Map<number, Candle>();
    for (const c of this.candles) {
      existingByTime.set(c.time, c);
    }
    for (const c of candles) {
      if (!existingByTime.has(c.time)) {
        existingByTime.set(c.time, c);
      }
    }
    const next = Array.from(existingByTime.values()).sort(
      (a, b) => a.time - b.time
    );
    if (candlesEqual(this.candles, next)) return;
    this.candles = next;
    this.lastUpdatedAt = Date.now();
    this.publish();
  }

  /**
   * Replace the current candle series. Used when the active
   * pair/interval changes and the existing series is no longer
   * relevant. Unlike `setCandles`, this does NOT merge.
   */
  replaceCandles(candles: readonly Candle[]): void {
    const next = candles.slice().sort((a, b) => a.time - b.time);
    if (candlesEqual(this.candles, next)) return;
    this.candles = next;
    this.lastUpdatedAt = Date.now();
    this.publish();
  }

  applyTick(candle: Candle): void {
    const next = normalise([...this.candles, candle]);
    if (candlesEqual(this.candles, next)) return;
    this.candles = next;
    this.lastUpdatedAt = Date.now();
    this.publish();
  }

  setStatus(status: LiveStatus): void {
    if (this.status === status) return;
    this.status = status;
    this.publish();
  }

  /**
   * Synchronously wipe the candle series without touching `status` or
   * the live WebSocket lifecycle. Publishes a new snapshot only on a
   * transition from populated to empty; calls on an already-cleared
   * store are no-ops, matching the `setCandles` / `replaceCandles` /
   * `applyTick` publish pattern.
   */
  clear(): void {
    if (this.candles.length === 0 && this.lastUpdatedAt === null) return;
    this.candles = EMPTY_SNAPSHOT.candles;
    this.lastUpdatedAt = null;
    this.publish();
  }

  /**
   * Tear-down hook used by the page-level `useEffect` cleanup. Closes
   * any registered WebSocket through the bound controller and clears
   * timers.
   */
  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    if (this.detachController) {
      try {
        this.detachController();
      } catch {
        // best-effort cleanup
      }
      this.detachController = null;
    }
    this.candles = EMPTY_SNAPSHOT.candles;
    this.status = 'closed';
    this.lastUpdatedAt = null;
    this.publish();
    this.listeners.clear();
    this.destroyed = false;
  }

  /**
   * Wire the store to its live feed controller so that `destroy()`
   * can reach it. Internal API used by `web/src/store/index.ts`.
   */
  bindController(detach: () => void): void {
    this.detachController = detach;
    this.destroyed = false;
  }

  private detachController: (() => void) | null = null;

  private publish(): void {
    this.snapshot = Object.freeze({
      candles: this.candles,
      status: this.status,
      lastUpdatedAt: this.lastUpdatedAt,
    });
    for (const listener of Array.from(this.listeners)) {
      try {
        listener();
      } catch {
        // listener errors should not break the store
      }
    }
  }
}
