/**
 * Public types for the candle store and live feed.
 *
 * Kept free of runtime code so they can be imported by both the store
 * implementation and the React hooks without circular concerns.
 */

export interface Candle {
  /** Unix-seconds UTC timestamp marking the start of the candle. */
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type LiveStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'reconnecting';

export interface Snapshot {
  readonly candles: readonly Candle[];
  readonly status: LiveStatus;
  readonly lastUpdatedAt: number | null;
}

export type TickMessage = {
  type: 'tick';
  candle: Candle;
};

export type StatusMessage = {
  type: 'status';
  status: LiveStatus;
};

export type LiveFeedMessage = TickMessage | StatusMessage | { type: string };
