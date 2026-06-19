/**
 * `LiveFeedController` owns the WebSocket connection to Kraken's
 * public WebSocket v2 API (`wss://ws.kraken.com/v2`) and translates
 * incoming messages into `candleStore` updates.
 *
 * Responsibilities
 * ----------------
 * - Discover configured trading pair subscriptions from the backend
 *   REST endpoint (`GET /api/v1/subscriptions`) and cache the result.
 * - Open exactly one WebSocket per `(pair, interval)` change; the
 *   previous socket is closed with code `1000` before a new one opens.
 * - On `open`, fetch the latest historical candles from the backend
 *   REST endpoint and merge them into the store before sending the
 *   Kraken v2 subscribe message. The same refetch happens on every
 *   successful reconnect so a dropped socket never leaves stale data
 *   on the chart.
 * - Dispatch OHLC update messages via `candleStore.applyTick()`.
 *   Kraken v2 sends numbers as strings and uses `interval_begin` (ISO
 *   timestamp) as the candle start; the controller parses both.
 * - Silently ignore non-OHLC messages (heartbeat, status, subscription
 *   confirmations, etc.).
 * - Treat 35 seconds of silence on an open socket as a dropped
 *   connection: close the socket and switch the store to
 *   `'reconnecting'`. Kraken v2 sends periodic heartbeats that reset
 *   the timer.
 * - Reconnect with exponential back-off
 *   `1s -> 2s -> 4s -> 8s -> 16s -> 30s` (capped at 30 s) and reset
 *   the counter on a successful `'open'`.
 */

import type { CandleStore } from './CandleStore';
import type { Candle } from './types';

const KRAKEN_WS_URL = 'wss://ws.kraken.com/v2';
const BACKOFF_SCHEDULE_MS = [1000, 2000, 4000, 8000, 16000, 30000];
const SILENCE_THRESHOLD_MS = 35_000;
const HISTORY_FETCH_COUNT = 180;

interface SubscriptionPair {
  pair: string;
  intervals: number[];
}

interface SubscriptionResponse {
  subscriptions: SubscriptionPair[];
}

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

export class LiveFeedController {
  private readonly store: CandleStore;
  private currentSocket: WebSocket | null = null;
  private activePair: string | null = null;
  private activeInterval: number | null = null;
  private attempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private subscriptionsPromise: Promise<SubscriptionResponse> | null = null;
  private destroyed = false;
  private fetchOverride:
    | (<T>(endpoint: string) => Promise<T>)
    | null = null;

  constructor(
    store: CandleStore,
    options: { fetchOverride?: <T>(endpoint: string) => Promise<T> } = {}
  ) {
    this.store = store;
    this.fetchOverride = options.fetchOverride ?? null;
  }

  attach(pair: string, interval: number): Promise<void> {
    this.destroyed = false;
    const sameTarget =
      this.activePair === pair &&
      this.activeInterval === interval &&
      this.currentSocket !== null;
    if (sameTarget) return Promise.resolve();

    this.store.setStatus('connecting');
    this.store.clear();
    this.detachSocket(1000);
    this.activePair = pair;
    this.activeInterval = interval;
    this.attempt = 0;
    return this.bootstrap(pair, interval);
  }

  detach(): void {
    this.destroyed = true;
    this.clearReconnectTimer();
    this.clearSilenceTimer();
    this.detachSocket(1000);
    this.activePair = null;
    this.activeInterval = null;
    this.store.clear();
    this.store.setStatus('closed');
  }

  private async bootstrap(pair: string, interval: number): Promise<void> {
    try {
      const subs = await this.fetchSubscriptions();
      const valid = subs.subscriptions.some(
        (s) => s.pair === pair && s.intervals.includes(interval)
      );
      if (!valid) {
        if (this.destroyed || this.activePair !== pair || this.activeInterval !== interval) {
          return;
        }
        console.warn(
          `live-feed: pair/interval not configured on backend: ${pair}@${interval}m`
        );
      }
    } catch (error) {
      // Treat subscription discovery failure as non-fatal: still
      // open the WS so the user sees live data; the backend may
      // simply be slow to respond.
      if (typeof console !== 'undefined') {
        console.warn('live-feed: subscription discovery failed', error);
      }
    }

    if (this.destroyed || this.activePair !== pair || this.activeInterval !== interval) {
      return;
    }

    await this.fetchHistoryAndOpen(pair, interval);
  }

  private openSocket(): void {
    if (this.destroyed || this.activePair === null || this.activeInterval === null) {
      return;
    }
    this.store.setStatus('connecting');
    let ws: WebSocket;
    try {
      ws = new WebSocket(KRAKEN_WS_URL);
    } catch (error) {
      if (typeof console !== 'undefined') {
        console.warn('live-feed: failed to construct WebSocket', error);
      }
      this.scheduleReconnect();
      return;
    }
    this.currentSocket = ws;
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => this.onSilenceTimeout(), SILENCE_THRESHOLD_MS);

    ws.addEventListener('open', this.handleOpen);
    ws.addEventListener('message', this.handleMessage as EventListener);
    ws.addEventListener('close', this.handleClose);
    ws.addEventListener('error', this.handleError);
  }

  private handleOpen = (): void => {
    this.attempt = 0;
    this.store.setStatus('open');
    console.log(`[ws] connected to ${this.activePair}@${this.activeInterval}m`);
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => this.onSilenceTimeout(), SILENCE_THRESHOLD_MS);
    this.sendSubscribe();
  };

  private handleMessage = (event: MessageEvent): void => {
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => this.onSilenceTimeout(), SILENCE_THRESHOLD_MS);
    let payload: unknown;
    try {
      payload = JSON.parse(typeof event.data === 'string' ? event.data : '');
    } catch {
      console.warn('live-feed: invalid JSON', event.data);
      return;
    }
    this.dispatch(payload);
  };

  private handleClose = (event: CloseEvent): void => {
    this.clearSilenceTimer();
    if (event.code === 1000) {
      // If a new attach is in progress, it has already set 'connecting'.
      // Don't override it with 'closed'.
      if (this.activePair !== null) return;
      console.log('[ws] disconnected');
      this.store.setStatus('closed');
      return;
    }
    console.log(`[ws] connection lost (code: ${event.code}), reconnecting...`);
    this.store.setStatus('reconnecting');
    this.scheduleReconnect();
  };

  private handleError = (): void => {
    // The 'close' event will fire right after 'error' and own the
    // reconnect scheduling; nothing to do here besides logging.
    if (typeof console !== 'undefined') {
      console.warn('live-feed: socket error');
    }
  };

  private sendSubscribe(): void {
    if (!this.currentSocket || this.currentSocket.readyState !== WebSocket.OPEN) return;
    if (!this.activePair || this.activeInterval === null) return;
    try {
      this.currentSocket.send(
        JSON.stringify({
          method: 'subscribe',
          params: {
            channel: 'ohlc',
            symbol: [this.activePair],
            interval: this.activeInterval,
          },
        })
      );
    } catch {
      // ignore — the close handler will schedule a reconnect
    }
  }

  private dispatch(payload: unknown): void {
    if (!payload || typeof payload !== 'object') {
      console.warn('live-feed: non-object payload', payload);
      return;
    }
    const message = payload as {
      channel?: string;
      type?: string;
      method?: string;
      data?: unknown;
    };
    if (message.channel === 'ohlc' && message.type === 'update' && Array.isArray(message.data)) {
      const candle = parseKrakenOhlc(message.data[0]);
      if (candle) {
        console.log('[ws] OHLC tick', candle);
        this.store.applyTick(candle);
        return;
      }
    }
    // Non-OHLC messages (status, heartbeat, subscription confirmations,
    // errors) are silently ignored. The silence timer was already
    // reset in `handleMessage`.
    if (message.channel === 'status' || message.channel === 'heartbeat') {
      return;
    }
    if (
      message.type === 'subscribe' ||
      message.type === 'unsubscribe' ||
      message.method === 'subscribe' ||
      message.method === 'unsubscribe'
    ) {
      return;
    }
    console.warn('live-feed: unknown message', payload);
  }

  private async fetchHistoryAndOpen(pair: string, interval: number): Promise<void> {
    try {
      const candles = await this.fetchHistory(pair, interval);
      if (this.destroyed || this.activePair !== pair || this.activeInterval !== interval) {
        return;
      }
      this.store.clear();
      this.store.replaceCandles(candles);
      console.log(`[ws] history loaded: ${candles.length} candles for ${pair}@${interval}m`);
    } catch (error) {
      console.warn(`[ws] history fetch failed for ${pair}@${interval}m, continuing with WS only`, error);
    }

    if (this.destroyed || this.activePair !== pair || this.activeInterval !== interval) {
      return;
    }
    this.openSocket();
  }

  private async fetchHistory(pair: string, interval: number): Promise<Candle[]> {
    const params = new URLSearchParams({
      pair,
      interval: String(interval),
      count: String(HISTORY_FETCH_COUNT),
    });
    const fetcher = this.fetchOverride ?? defaultFetch;
    const resp = await fetcher<HistoricDataResponse>(`/historic-data/live?${params.toString()}`);
    return historicDataToCandles(resp);
  }

  private async fetchSubscriptions(): Promise<SubscriptionResponse> {
    if (!this.subscriptionsPromise) {
      const fetcher = this.fetchOverride ?? defaultFetch;
      this.subscriptionsPromise = fetcher<SubscriptionResponse>('/subscriptions').catch(
        (error) => {
          // Reset so a future attach() retries rather than reusing
          // a permanently-failed promise.
          this.subscriptionsPromise = null;
          throw error;
        }
      );
    }
    return this.subscriptionsPromise;
  }

  private onSilenceTimeout(): void {
    if (!this.currentSocket) return;
    if (this.currentSocket.readyState === WebSocket.OPEN) {
      // The browser does not surface 0-byte pings for application-level
      // silence, so we manually close and let the close handler reconnect.
      try {
        this.currentSocket.close(4000, 'silence_timeout');
      } catch {
        // ignore
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.destroyed) return;
    if (this.activePair === null || this.activeInterval === null) return;
    const idx = Math.min(this.attempt, BACKOFF_SCHEDULE_MS.length - 1);
    const delay = BACKOFF_SCHEDULE_MS[idx];
    this.attempt += 1;
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      void this.fetchHistoryAndOpen(this.activePair as string, this.activeInterval as number);
    }, delay);
  }

  private detachSocket(code: number): void {
    if (!this.currentSocket) return;
    const ws = this.currentSocket;
    ws.removeEventListener('open', this.handleOpen);
    ws.removeEventListener('message', this.handleMessage as EventListener);
    ws.removeEventListener('close', this.handleClose);
    ws.removeEventListener('error', this.handleError);
    try {
      if (ws.readyState <= WebSocket.OPEN) {
        ws.close(code);
      }
    } catch {
      // ignore
    }
    this.currentSocket = null;
    this.clearSilenceTimer();
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private clearSilenceTimer(): void {
    if (this.silenceTimer !== null) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }
}

function historicDataToCandles(resp: HistoricDataResponse): Candle[] {
  return resp.data.map((r) => ({
    time: Math.floor(new Date(r.timestamp).getTime() / 1000),
    open: r.open,
    high: r.high,
    low: r.low,
    close: r.close,
    volume: r.volume,
  }));
}

async function defaultFetch<T>(endpoint: string): Promise<T> {
  const response = await fetch(`/api/v1${endpoint}`);
  if (!response.ok) {
    throw new Error(`REST ${endpoint} failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

function parseKrakenOhlc(raw: unknown): Candle | null {
  if (!raw || typeof raw !== 'object') return null;
  const record = raw as {
    interval_begin?: unknown;
    open?: unknown;
    high?: unknown;
    low?: unknown;
    close?: unknown;
    volume?: unknown;
  };
  if (typeof record.interval_begin !== 'string') return null;
  const time = Math.floor(new Date(record.interval_begin).getTime() / 1000);
  if (!Number.isFinite(time)) return null;
  const open = numberOrNull(record.open);
  const high = numberOrNull(record.high);
  const low = numberOrNull(record.low);
  const close = numberOrNull(record.close);
  const volume = numberOrNull(record.volume);
  if (open === null || high === null || low === null || close === null || volume === null) {
    return null;
  }
  return { time, open, high, low, close, volume };
}

function numberOrNull(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}
