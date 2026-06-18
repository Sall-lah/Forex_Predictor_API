/**
 * Tests for `LiveFeedController.dispatch()` wire-format handling.
 *
 * The backend `ConnectionManager._sender_loop` sends the unwrapped
 * `CandleTick` Pydantic model directly (no `{ type: "tick", candle }`
 * wrapper). The frontend MUST accept that format and also tolerate the
 * wrapped format and the keepalive pong.
 */

import { describe, expect, it, vi } from 'vitest';
import { CandleStore } from './CandleStore';
import { LiveFeedController } from './LiveFeedController';

function makeController() {
  const store = new CandleStore();
  const controller = new LiveFeedController(store);
  return { store, controller };
}

function getPrivate<T>(obj: object, key: string): T {
  return (obj as unknown as Record<string, T>)[key];
}

describe('LiveFeedController.dispatch', () => {
  it('applies an unwrapped CandleTick payload from the backend', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');

    // This is exactly what backend `_sender_loop` produces via
    // `tick.model_dump(mode="json")`.
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      pair: 'BTC/USD',
      interval: 1,
      timestamp: '2024-01-01T00:01:00.000Z',
      open: 100.0,
      high: 105.0,
      low: 99.0,
      close: 103.0,
      volume: 1.5,
      is_closed: false,
    });

    expect(applySpy).toHaveBeenCalledTimes(1);
    const applied = applySpy.mock.calls[0]?.[0];
    expect(applied).toBeDefined();
    expect(applied!.time).toBe(Math.floor(new Date('2024-01-01T00:01:00.000Z').getTime() / 1000));
    expect(applied!.open).toBe(100.0);
    expect(applied!.high).toBe(105.0);
    expect(applied!.low).toBe(99.0);
    expect(applied!.close).toBe(103.0);
    expect(applied!.volume).toBe(1.5);
  });

  it('accepts a wrapped { type: "tick", candle } payload', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      type: 'tick',
      candle: {
        time: 1704067200,
        open: 1,
        high: 2,
        low: 0.5,
        close: 1.5,
        volume: 1,
      },
    });
    expect(applySpy).toHaveBeenCalledTimes(1);
    expect(applySpy.mock.calls[0]?.[0]?.close).toBe(1.5);
  });

  it('accepts a numeric (epoch) timestamp on the unwrapped payload', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      pair: 'BTC/USD',
      interval: 1,
      timestamp: 1704067200,
      open: 1,
      high: 2,
      low: 0.5,
      close: 1.5,
      volume: 1,
    });
    expect(applySpy).toHaveBeenCalledTimes(1);
    expect(applySpy.mock.calls[0]?.[0]?.time).toBe(1704067200);
  });

  it('silently acknowledges a keepalive pong without applying a tick', () => {
    const { store, controller } = makeController();
    const applySpy = vi.spyOn(store, 'applyTick');
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, { type: 'pong' });
    expect(applySpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });

  it('applies a status update when wrapped', () => {
    const { store, controller } = makeController();
    const statusSpy = vi.spyOn(store, 'setStatus');
    getPrivate<DispatchFn>(controller, 'dispatch').call(controller, {
      type: 'status',
      status: 'reconnecting',
    });
    expect(statusSpy).toHaveBeenCalledWith('reconnecting');
  });
});

type DispatchFn = (payload: unknown) => void;
