import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Chart } from './Chart';
import type { OHLCVData } from '../hooks/useMarketData';
import type { CandleTick } from '../types';

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

const sampleData: OHLCVData[] = [
  { time: '2024-01-01T00:00:00Z', open: 1, high: 2, low: 0.5, close: 1.5, volume: 1 },
];

const sampleTick: CandleTick = {
  pair: 'XXBTZUSD',
  interval: 1,
  timestamp: '2024-01-01T00:01:00Z',
  open: 2,
  high: 3,
  low: 1.5,
  close: 2.5,
  volume: 1,
  is_closed: false,
};

describe('Chart', () => {
  it('calls setData for the initial REST snapshot only', () => {
    setDataMock.mockClear();
    updateMock.mockClear();
    render(<Chart data={sampleData} liveTick={null} />);
    expect(setDataMock).toHaveBeenCalled();
  });

  it('calls series.update for a live tick, not setData', () => {
    setDataMock.mockClear();
    updateMock.mockClear();
    const { rerender } = render(<Chart data={sampleData} liveTick={null} />);
    setDataMock.mockClear();
    rerender(<Chart data={sampleData} liveTick={sampleTick} />);
    expect(updateMock).toHaveBeenCalled();
    // setData should NOT be called again on a tick rerender.
    expect(setDataMock).not.toHaveBeenCalled();
  });
});
