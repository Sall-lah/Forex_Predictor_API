/**
 * `CandlesPage` is the sole page of the new frontend. It composes
 * `Chart`, `StatusBar`, and `ReconnectingBanner` and owns the
 * `useCandles` hook that drives the data layer.
 *
 * On unmount the page calls `candleStore.destroy()` so the underlying
 * WebSocket is closed cleanly and any pending timers are cancelled.
 */

import { useEffect, useState } from 'react';
import { Chart } from '../components/Chart';
import { StatusBar } from '../components/StatusBar';
import { ReconnectingBanner } from '../components/ReconnectingBanner';
import { useCandles } from '../hooks/useCandles';
import { candleStore } from '../store';
import { colors, spacing } from '../design/tokens';

const SUPPORTED_PAIRS = ['BTC/USD', 'ETH/USD'] as const;
const SUPPORTED_INTERVALS = [1, 5, 15, 60, 240] as const;

type SupportedPair = (typeof SUPPORTED_PAIRS)[number];
type SupportedInterval = (typeof SUPPORTED_INTERVALS)[number];

export const CandlesPage: React.FC = () => {
  const [pair, setPair] = useState<SupportedPair>('BTC/USD');
  const [interval, setInterval] = useState<SupportedInterval>(60);

  const { status, error } = useCandles(pair, interval);

  useEffect(() => {
    return () => {
      candleStore.destroy();
    };
  }, []);

  return (
    <main
      data-testid="candles-page"
      style={{
        minHeight: '100vh',
        background: colors.surface,
        color: colors.textPrimary,
        fontFamily: 'Inter, sans-serif',
        padding: spacing.md,
        boxSizing: 'border-box',
      }}
    >
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: spacing.md,
        }}
      >
        <h1
          style={{
            fontSize: 22,
            fontWeight: 700,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: colors.textPrimary,
            margin: 0,
          }}
        >
          Forex Candles
        </h1>
        <nav
          aria-label="controls"
          style={{
            display: 'flex',
            gap: spacing.sm,
            alignItems: 'center',
          }}
        >
          <select
            aria-label="pair"
            data-testid="pair-select"
            value={pair}
            onChange={(e) => setPair(e.target.value as SupportedPair)}
            style={selectStyle}
          >
            {SUPPORTED_PAIRS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <select
            aria-label="interval"
            data-testid="interval-select"
            value={interval}
            onChange={(e) =>
              setInterval(Number(e.target.value) as SupportedInterval)
            }
            style={selectStyle}
          >
            {SUPPORTED_INTERVALS.map((i) => (
              <option key={i} value={i}>
                {i}m
              </option>
            ))}
          </select>
        </nav>
      </header>

      <ReconnectingBanner />

      {error && (
        <div
          data-testid="error-banner"
          style={{
            background: colors.bear,
            color: '#000',
            padding: `${spacing.xs}px ${spacing.md}px`,
            borderRadius: 6,
            marginBottom: spacing.sm,
            fontWeight: 600,
          }}
        >
          {error.message}
        </div>
      )}

      <div
        data-testid="status-bar-container"
        style={{ marginBottom: spacing.md }}
      >
        <StatusBar pair={pair} interval={interval} />
      </div>

      <section
        aria-label="chart"
        data-testid="chart-section"
        style={{
          background: colors.surfaceElevated,
          borderRadius: 8,
          border: `1px solid ${colors.border}`,
          padding: spacing.sm,
          minHeight: 360,
        }}
      >
        <Chart />
      </section>

      <footer
        style={{
          marginTop: spacing.md,
          color: colors.textMuted,
          fontSize: 12,
        }}
      >
        WebSocket status: <strong>{status}</strong>
      </footer>
    </main>
  );
};

const selectStyle: React.CSSProperties = {
  background: colors.surfaceElevated,
  color: colors.textPrimary,
  border: `1px solid ${colors.border}`,
  borderRadius: 6,
  padding: '6px 10px',
  fontFamily: 'Inter, sans-serif',
  fontSize: 13,
};
