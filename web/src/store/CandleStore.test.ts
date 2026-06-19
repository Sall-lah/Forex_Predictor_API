import { describe, expect, it, vi } from 'vitest';
import { CandleStore } from './CandleStore';

const CANDLE_A = {
  time: 1704067200,
  open: 100,
  high: 105,
  low: 99,
  close: 103,
  volume: 10,
};
const CANDLE_B = {
  time: 1704067260,
  open: 103,
  high: 108,
  low: 102,
  close: 106,
  volume: 12,
};

describe('CandleStore', () => {
  describe('clear()', () => {
    it('empties a populated store', () => {
      const store = new CandleStore();
      store.setCandles([CANDLE_A, CANDLE_B]);
      expect(store.getCandles().length).toBe(2);

      store.clear();

      expect(store.getCandles()).toEqual([]);
      expect(store.getSnapshot().lastUpdatedAt).toBeNull();
    });

    it('preserves status', () => {
      const store = new CandleStore();
      store.setStatus('open');
      store.setCandles([CANDLE_A]);

      store.clear();

      expect(store.getStatus()).toBe('open');
    });

    it('publishes a new snapshot reference on a populated store', () => {
      const store = new CandleStore();
      store.setCandles([CANDLE_A]);
      const snapBefore = store.getSnapshot();

      store.clear();

      const snapAfter = store.getSnapshot();
      expect(snapAfter).not.toBe(snapBefore);
      expect(snapAfter.candles).toEqual([]);
    });

    it('is a no-op on an already-cleared store (same snapshot reference, no listener fires)', () => {
      const store = new CandleStore();
      store.clear(); // ensure cleared
      const snapBefore = store.getSnapshot();
      const listener = vi.fn();
      store.subscribe(listener);

      store.clear();

      expect(store.getSnapshot()).toBe(snapBefore);
      expect(listener).not.toHaveBeenCalled();
    });

    it('is a no-op when store has never been written to', () => {
      const store = new CandleStore();
      const snapBefore = store.getSnapshot();
      const listener = vi.fn();
      store.subscribe(listener);

      store.clear();

      expect(store.getSnapshot()).toBe(snapBefore);
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('setCandles() merge semantics', () => {
    it('merges by time, keeping existing candles not present in the new payload', () => {
      const store = new CandleStore();
      store.setCandles([CANDLE_A, CANDLE_B]);

      // Only send CANDLE_A again — CANDLE_B should survive
      store.setCandles([CANDLE_A]);

      expect(store.getCandles().length).toBe(2);
    });

    it('does not overwrite existing candles with older values', () => {
      const store = new CandleStore();
      store.setCandles([CANDLE_A]);

      const updated = { ...CANDLE_A, close: 999 };
      store.setCandles([updated]);

      // setCandles keeps the first candle (existing WS-sourced one)
      expect(store.getCandles()[0]?.close).toBe(103);
    });
  });

  describe('replaceCandles() wipe-and-fill', () => {
    it('replaces the entire series, removing old candles', () => {
      const store = new CandleStore();
      store.setCandles([CANDLE_A, CANDLE_B]);
      expect(store.getCandles().length).toBe(2);

      store.replaceCandles([CANDLE_B]);

      expect(store.getCandles().length).toBe(1);
      expect(store.getCandles()[0]?.time).toBe(CANDLE_B.time);
    });
  });

  describe('setStatus()', () => {
    it('publishes only when the status actually changes', () => {
      const store = new CandleStore();
      const listener = vi.fn();
      store.subscribe(listener);

      store.setStatus('open');
      expect(listener).toHaveBeenCalledTimes(1);

      store.setStatus('open'); // same value
      expect(listener).toHaveBeenCalledTimes(1);

      store.setStatus('closed');
      expect(listener).toHaveBeenCalledTimes(2);
    });
  });
});
