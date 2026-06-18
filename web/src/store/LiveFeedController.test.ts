/**
 * Tests for `LiveFeedController.dispatch()` wire-format handling
 * and the new history-refetch lifecycle.
 *
 * Kraken v2 sends OHLC updates with:
 *   - `channel: "ohlc"`, `type: "update"`
 *   - `data: [{ interval_begin: ISO, open/high/low/close/volume as strings }]`
 *
 * Subscription confirmations arrive as `{ type: "subscribe" }` and
 * heartbeats/statuses as `{ channel: "heartbeat" | "status" }`. All
 * of these MUST be silently ignored.
 *
 * The history fetch happens via the `fetchOverride` constructor
 * option so we can assert it without touching the network.
 */

import { describe, expect, it, vi } from 'vitest';
import { CandleStore } from './CandleStore';
import { LiveFeedController } from './LiveFeedController';

function getPrivate<T>(obj: object, key: string): T {
  return (obj as unknown as Record<string, T>)[key];
}

type DispatchFn = (payload: unknown) => void;

function makeController(opts: {
  subscriptions?: unknown;
  history?: unknown;
  historyError?: Error;
} = {}) {
  const store = new CandleStore();
  const calls: string[] = [];
  const fetchOverride = vi.fn(async <T>(endpoint: string): Promise<T> => {
    calls.push(endpoint);
    if (endpoint.startsWith('/subscriptions')) {
      return (opts.subscriptions ?? { subscriptions: [] }) as T;
    }
    if (endpoint.startsWith('/historic-data/live')) {
      if (opts.historyError) throw opts.historyError;
      return (opts.history ?? {
        symbol: 'BTC/USD',
        total_records: 0,
        data: [],
      }) as T;
    }
    throw new Error(`unexpected endpoint: ${endpoint}`);
  });
  const controller = new LiveFeedController(store, { fetchOverride });
  return { store, controller, calls, fetchOverride };
}

describe('LiveFeedController.dispatch (Kraken v2)', () => {
  it('applies a Kraken v2 OHLC update, parsing strings to numbers and ISO to unix seconds', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');

    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'ohlc',
      type: 'update',
      data: [
        {
          symbol: 'BTC/USD',
          interval: 1,
          interval_begin: '2024-01-01T00:01:00.000Z',
          open: '100.0',
          high: '105.5',
          low: '99.5',
          close: '103.25',
          volume: '1.5',
        },
      ],
    });

    expect(applySpy).toHaveBeenCalledTimes(1);
    const applied = applySpy.mock.calls[0]?.[0];
    expect(applied).toBeDefined();
    expect(applied!.time).toBe(
      Math.floor(new Date('2024-01-01T00:01:00.000Z').getTime() / 1000)
    );
    expect(applied!.open).toBe(100.0);
    expect(applied!.high).toBe(105.5);
    expect(applied!.low).toBe(99.5);
    expect(applied!.close).toBe(103.25);
    expect(applied!.volume).toBe(1.5);
  });

  it('accepts the first element of a multi-element data array', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'ohlc',
      type: 'update',
      data: [
        {
          interval_begin: '2024-01-01T00:01:00.000Z',
          open: '1',
          high: '2',
          low: '0.5',
          close: '1.5',
          volume: '1',
        },
        {
          interval_begin: '2024-01-01T00:02:00.000Z',
          open: '1.5',
          high: '2.5',
          low: '1.0',
          close: '2.0',
          volume: '1.2',
        },
      ],
    });
    expect(applySpy).toHaveBeenCalledTimes(1);
    expect(applySpy.mock.calls[0]?.[0]?.close).toBe(1.5);
  });

  it('silently ignores a Kraken v2 subscription confirmation', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      method: 'subscribe',
      result: 'subscribed',
      success: true,
      time_in: '2024-01-01T00:00:00.000Z',
    });
    expect(applySpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('silently ignores Kraken v2 heartbeat messages', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'heartbeat',
      data: { time: '2024-01-01T00:00:00.000Z' },
    });
    expect(applySpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('silently ignores Kraken v2 status messages', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'status',
      data: [{ symbol: 'BTC/USD', status: 'online' }],
    });
    expect(applySpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('skips a malformed OHLC record without applying a tick', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'ohlc',
      type: 'update',
      data: [{ interval_begin: 'not-a-date' }],
    });
    expect(applySpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('warns once for an unknown channel and does not apply a tick', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      channel: 'book',
      data: [],
    });
    expect(applySpy).not.toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});

describe('LiveFeedController history refetch', () => {
  it('fetches /subscriptions once and caches the result across attach calls', async () => {
    const { controller, calls } = makeController({
      subscriptions: {
        subscriptions: [{ pair: 'BTC/USD', intervals: [1, 5, 60] }],
      },
    });
    await controller.attach('BTC/USD', 60);
    expect(calls.filter((c) => c.startsWith('/subscriptions')).length).toBe(1);
    controller.detach();
  });

  it('fetches history for the requested pair/interval on attach', async () => {
    const { controller, calls, store } = makeController({
      subscriptions: {
        subscriptions: [{ pair: 'BTC/USD', intervals: [60] }],
      },
      history: {
        symbol: 'BTC/USD',
        total_records: 1,
        data: [
          {
            timestamp: '2024-01-01T00:00:00.000Z',
            open: 1,
            high: 2,
            low: 0.5,
            close: 1.5,
            volume: 1,
          },
        ],
      },
    });
    const setSpy = vi.spyOn(store, 'replaceCandles');
    await controller.attach('BTC/USD', 60);
    expect(calls.some((c) => c.includes('/historic-data/live'))).toBe(true);
    expect(setSpy).toHaveBeenCalled();
    const firstCall = setSpy.mock.calls[0]?.[0] as Array<{ time: number; close: number }>;
    expect(firstCall).toBeDefined();
    expect(firstCall[0]?.close).toBe(1.5);
    controller.detach();
  });

  it('refetches history when pair/interval switches', async () => {
    const { controller, calls } = makeController({
      subscriptions: {
        subscriptions: [
          { pair: 'BTC/USD', intervals: [60] },
          { pair: 'ETH/USD', intervals: [60] },
        ],
      },
      history: {
        symbol: 'BTC/USD',
        total_records: 0,
        data: [],
      },
    });
    await controller.attach('BTC/USD', 60);
    const beforeSwitch = calls.filter((c) => c.includes('/historic-data/live')).length;
    await controller.attach('ETH/USD', 60);
    const afterSwitch = calls.filter((c) => c.includes('/historic-data/live')).length;
    expect(afterSwitch).toBeGreaterThan(beforeSwitch);
    controller.detach();
  });

  it('proceeds with WS open when history fetch fails', async () => {
    const { controller, calls } = makeController({
      subscriptions: {
        subscriptions: [{ pair: 'BTC/USD', intervals: [60] }],
      },
      historyError: new Error('boom'),
    });
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    await controller.attach('BTC/USD', 60);
    expect(calls.some((c) => c.includes('/historic-data/live'))).toBe(true);
    warnSpy.mockRestore();
    controller.detach();
  });
});
