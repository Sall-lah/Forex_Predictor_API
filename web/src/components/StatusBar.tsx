/**
 * `StatusBar` shows the latest candle's OHLC plus a small connection
 * status chip. The whole component subscribes to `candleStore` once
 * via `useSyncExternalStore` and pulls the latest candle from the
 * snapshot.
 */

import { useSyncExternalStore } from 'react';
import { candleStore } from '../store';
import type { Candle, LiveStatus } from '../store';
import { colors, fontSizes, fontWeights, spacing } from '../design/tokens';

const STATUS_LABEL: Record<LiveStatus, string> = {
  idle: 'Idle',
  connecting: 'Connecting',
  open: 'Live',
  closed: 'Closed',
  reconnecting: 'Reconnecting',
};

const STATUS_COLOR: Record<LiveStatus, string> = {
  idle: colors.textMuted,
  connecting: colors.info,
  open: colors.bull,
  closed: colors.textMuted,
  reconnecting: colors.reconnecting,
};

function pickLatest(candles: readonly Candle[]): Candle | null {
  return candles.length > 0 ? (candles[candles.length - 1] as Candle) : null;
}

function formatPrice(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '—';
  return value.toFixed(5);
}

export const StatusBar: React.FC<{ pair: string; interval: number }> = ({
  pair,
  interval,
}) => {
  const snapshot = useSyncExternalStore(
    candleStore.subscribe,
    candleStore.getSnapshot
  );
  const last = pickLatest(snapshot.candles);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: `${spacing.sm}px ${spacing.md}px`,
        background: colors.surfaceElevated,
        borderRadius: 8,
        border: `1px solid ${colors.border}`,
        color: colors.textPrimary,
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: spacing.lg }}>
        <span
          style={{
            fontSize: fontSizes.md,
            fontWeight: fontWeights.semibold,
            color: colors.textMuted,
          }}
        >
          {pair} · {interval}m
        </span>
        <Stat label="Close" value={formatPrice(last?.close ?? null)} emphasis />
        <Stat label="Open" value={formatPrice(last?.open ?? null)} />
        <Stat label="High" value={formatPrice(last?.high ?? null)} />
        <Stat label="Low" value={formatPrice(last?.low ?? null)} />
      </div>
      <div
        aria-label="live-status"
        data-testid="live-status"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: spacing.xs,
          padding: `2px ${spacing.sm}px`,
          borderRadius: 999,
          fontSize: fontSizes.xs,
          fontWeight: fontWeights.bold,
          color: STATUS_COLOR[snapshot.status],
          border: `1px solid ${STATUS_COLOR[snapshot.status]}`,
        }}
      >
        <span
          style={{
            display: 'inline-block',
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: STATUS_COLOR[snapshot.status],
          }}
        />
        {STATUS_LABEL[snapshot.status]}
      </div>
    </div>
  );
};

const Stat: React.FC<{ label: string; value: string; emphasis?: boolean }> = ({
  label,
  value,
  emphasis,
}) => (
  <div style={{ display: 'flex', flexDirection: 'column' }}>
    <span
      style={{
        fontSize: fontSizes.xs,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        color: colors.textMuted,
      }}
    >
      {label}
    </span>
    <span
      data-testid={`stat-${label.toLowerCase()}`}
      style={{
        fontSize: emphasis ? fontSizes.lg : fontSizes.md,
        fontWeight: emphasis ? fontWeights.bold : fontWeights.medium,
        color: emphasis ? colors.bull : colors.textPrimary,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {value}
    </span>
  </div>
);
