import { render, act } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Chart } from './Chart';
import { candleStore } from '../store';

// Mock the lightweight-charts library so we can spy on setData / update
// without instantiating a real chart canvas.
const setDataMock = vi.fn();
const updateMock = vi.fn();
vi.mock('lightweight-charts', () => ({
  createChart: () => ({
    applyOptions: vi.fn(),
    addCandlestickSeries: () => ({
      setData: setDataMock,
      update: updateMock,
    }),
    remove: vi.fn(),
  }),
}));

const CANDLE_1 = {
  time: 1704067200,
  open: 100,
  high: 105,
  low: 99,
  close: 103,
  volume: 10,
};

const CANDLE_2 = {
  time: 1704067260,
  open: 103,
  high: 108,
  low: 102,
  close: 106,
  volume: 12,
};

describe('Chart', () => {
  it('calls setData for the initial snapshot', () => {
    setDataMock.mockClear();
    updateMock.mockClear();
    render(<Chart />);
    // The initial snapshot is empty, so setData should not be called yet
    expect(setDataMock).not.toHaveBeenCalled();
  });

  it('calls setData([]) and resets refs on a zero-candle snapshot after being populated', () => {
    setDataMock.mockClear();
    updateMock.mockClear();
    render(<Chart />);

    // Push a populated snapshot
    act(() => {
      candleStore.setCandles([CANDLE_1, CANDLE_2]);
    });
    expect(setDataMock).toHaveBeenCalled();

    setDataMock.mockClear();
    updateMock.mockClear();

    // Push an empty snapshot (simulating a clear())
    act(() => {
      candleStore.clear();
    });
    expect(setDataMock).toHaveBeenCalledWith([]);
  });

  it('re-seeds via setData (not update) on the second populated snapshot after a clear', () => {
    setDataMock.mockClear();
    updateMock.mockClear();
    render(<Chart />);

    // Push first populated snapshot
    act(() => {
      candleStore.setCandles([CANDLE_1]);
    });
    setDataMock.mockClear();
    updateMock.mockClear();

    // Push empty snapshot (clear)
    act(() => {
      candleStore.clear();
    });
    setDataMock.mockClear();
    updateMock.mockClear();

    // Push second populated snapshot
    act(() => {
      candleStore.setCandles([CANDLE_1, CANDLE_2]);
    });
    // Should re-seed via setData, not update
    expect(setDataMock).toHaveBeenCalled();
    expect(updateMock).not.toHaveBeenCalled();
  });
});
