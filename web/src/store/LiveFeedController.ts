/**
 * `LiveFeedController` owns the WebSocket connection to the backend
 * `/ws/candles` endpoint and translates incoming messages into
 * `candleStore` updates.
 *
 * Responsibilities
 * ----------------
 * - Open exactly one WebSocket per `(pair, interval)` change; the
 *   previous socket is closed with code `1000` before a new one opens.
 * - Dispatch `{ type: 'tick', candle }` messages via
 *   `candleStore.applyTick()`.
 * - Dispatch `{ type: 'status', status }` messages via
 *   `candleStore.setStatus()`.
 * - Treat 3 seconds of silence on an open socket as a dropped
 *   connection: close the socket and switch the store to
 *   `'reconnecting'`.
 * - Reconnect with exponential back-off
 *   `1s -> 2s -> 4s -> 8s -> 16s -> 30s` (capped at 30 s) and reset
 *   the counter on a successful `'open'`.
 */

import type { CandleStore } from './CandleStore';
import type { Candle, LiveStatus } from './types';

const BACKOFF_SCHEDULE_MS = [1000, 2000, 4000, 8000, 16000, 30000];
const SILENCE_THRESHOLD_MS = 3000;

function buildWsUrl(pair: string, interval: number): string {
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:'
    ? 'wss:'
    : 'ws:';
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:3000';
  const params = new URLSearchParams({ pair, interval: String(interval) });
  return `${protocol}//${host}/ws/candles?${params.toString()}`;
}

export class LiveFeedController {
  private readonly store: CandleStore;
  private currentSocket: WebSocket | null = null;
  private activePair: string | null = null;
  private activeInterval: number | null = null;
  private attempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  constructor(store: CandleStore) {
    this.store = store;
  }

  attach(pair: string, interval: number): void {
    if (this.destroyed) return;
    if (this.activePair === pair && this.activeInterval === interval && this.currentSocket) {
      return;
    }

    this.detachSocket(1000);
    this.activePair = pair;
    this.activeInterval = interval;
    this.attempt = 0;
    this.openSocket();
  }

  detach(): void {
    this.destroyed = true;
    this.clearReconnectTimer();
    this.clearSilenceTimer();
    this.detachSocket(1000);
    this.store.setStatus('closed');
  }

  private openSocket(): void {
    if (this.destroyed || this.activePair === null || this.activeInterval === null) {
      return;
    }
    this.store.setStatus('connecting');
    let ws: WebSocket;
    try {
      ws = new WebSocket(buildWsUrl(this.activePair, this.activeInterval));
    } catch (error) {
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
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => this.onSilenceTimeout(), SILENCE_THRESHOLD_MS);
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
      this.store.setStatus('closed');
      return;
    }
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

  private dispatch(payload: unknown): void {
    if (!payload || typeof payload !== 'object') {
      console.warn('live-feed: non-object payload', payload);
      return;
    }
    const message = payload as { type?: string; candle?: Candle; status?: LiveStatus };
    if (message.type === 'tick' && message.candle) {
      this.store.applyTick(message.candle);
      return;
    }
    if (message.type === 'status' && message.status) {
      this.store.setStatus(message.status);
      return;
    }
    console.warn('live-feed: unknown message', payload);
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
    const idx = Math.min(this.attempt, BACKOFF_SCHEDULE_MS.length - 1);
    const delay = BACKOFF_SCHEDULE_MS[idx];
    this.attempt += 1;
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.openSocket();
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
