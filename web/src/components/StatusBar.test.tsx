import { render, screen, act, cleanup } from '@testing-library/react';
import { describe, expect, it, beforeEach } from 'vitest';
import { StatusBar } from './StatusBar';
import { candleStore } from '../store';

describe('StatusBar', () => {
  beforeEach(() => {
    cleanup();
    candleStore.clear();
    candleStore.setStatus('idle');
  });

  it('renders latest OHLC values', () => {
    act(() => {
      candleStore.setCandles([
        { time: 1704067200, open: 1.1, high: 1.2, low: 1.0, close: 1.15, volume: 100 },
      ]);
    });

    render(<StatusBar pair="BTC/USD" interval={60} />);

    expect(screen.getByText('BTC/USD · 60m')).toBeInTheDocument();
    expect(screen.getByTestId('stat-close')).toHaveTextContent('1.15000');
    expect(screen.getByTestId('stat-open')).toHaveTextContent('1.10000');
    expect(screen.getByTestId('stat-high')).toHaveTextContent('1.20000');
    expect(screen.getByTestId('stat-low')).toHaveTextContent('1.00000');
  });

  it('displays connection status chip', () => {
    act(() => {
      candleStore.setStatus('open');
    });

    render(<StatusBar pair="ETH/USD" interval={5} />);

    expect(screen.getByTestId('live-status')).toBeInTheDocument();
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('reacts to store snapshot changes', () => {
    render(<StatusBar pair="BTC/USD" interval={60} />);

    expect(screen.getByTestId('stat-close')).toHaveTextContent('—');

    act(() => {
      candleStore.setCandles([
        { time: 1704067200, open: 2.0, high: 2.5, low: 1.8, close: 2.3, volume: 50 },
      ]);
    });

    expect(screen.getByTestId('stat-close')).toHaveTextContent('2.30000');
  });
});
