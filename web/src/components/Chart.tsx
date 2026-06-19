/**
 * `Chart` renders a single `lightweight-charts` candlestick series
 * driven by `candleStore`. It owns no props and no prop array - all
 * data flows through the external store via `useSyncExternalStore`.
 *
 * Design tokens (`web/src/design/tokens.ts`) provide the colour
 * palette; the chart updates its size on `window.resize` and uses the
 * 480/360 px default height breakpoints.
 */

import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react';
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type Time,
} from 'lightweight-charts';
import { candleStore } from '../store';
import type { Candle, Snapshot } from '../store';
import { colors } from '../design/tokens';

const LARGE_VIEWPORT_PX = 1024;
const HEIGHT_LARGE = 480;
const HEIGHT_SMALL = 360;

function snapshotToCandlestickData(
  snapshot: Snapshot
): readonly CandlestickData<Time>[] {
  const out: CandlestickData<Time>[] = [];
  for (const c of snapshot.candles) {
    out.push({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    });
  }
  return out;
}

export const Chart: React.FC = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const lastTickTimeRef = useRef<number | null>(null);
  const initialisedRef = useRef(false);

  const snapshot = useSyncExternalStore(
    candleStore.subscribe,
    candleStore.getSnapshot
  );

  // Build / teardown the chart instance whenever the container mounts.
  const setContainer = useCallback((node: HTMLDivElement | null) => {
    containerRef.current = node;
    if (!node) {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
      }
      initialisedRef.current = false;
      return;
    }
    if (chartRef.current) return;

    const isLarge = window.innerWidth >= LARGE_VIEWPORT_PX;
    const height = isLarge ? HEIGHT_LARGE : HEIGHT_SMALL;
    const chart = createChart(node, {
      width: node.clientWidth,
      height,
      layout: {
        background: { color: colors.surface },
        textColor: colors.textMuted,
        fontFamily: 'Inter, sans-serif',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: colors.border },
        horzLines: { color: colors.border },
      },
      rightPriceScale: { borderColor: colors.border },
      timeScale: { borderColor: colors.border },
    });
    const series = chart.addCandlestickSeries({
      upColor: colors.bull,
      downColor: colors.bear,
      borderVisible: false,
      wickUpColor: colors.bull,
      wickDownColor: colors.bear,
    });
    chartRef.current = chart;
    seriesRef.current = series;

    // Seed with the current snapshot so the chart isn't empty.
    const data = snapshotToCandlestickData(candleStore.getSnapshot());
    if (data.length > 0) {
      series.setData([...data]);
      initialisedRef.current = true;
      lastTickTimeRef.current = data[data.length - 1].time as number;
    }

    const handleResize = () => {
      if (!chartRef.current || !node) return;
      const large = window.innerWidth >= LARGE_VIEWPORT_PX;
      chartRef.current.applyOptions({
        width: node.clientWidth,
        height: large ? HEIGHT_LARGE : HEIGHT_SMALL,
      });
    };
    window.addEventListener('resize', handleResize);

    // Clean up the listener when the container unmounts.
    const observer = new MutationObserver(() => {
      if (!document.body.contains(node)) {
        window.removeEventListener('resize', handleResize);
        observer.disconnect();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }, []);

  useEffect(() => {
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
      }
    };
  }, []);

  // Apply snapshot changes. The first non-empty render seeds via
  // `setData`; subsequent updates use `series.update` so the chart
  // does not rebuild the entire history per tick.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const data = snapshotToCandlestickData(snapshot);
    if (!initialisedRef.current && data.length > 0) {
      series.setData([...data]);
      initialisedRef.current = true;
      lastTickTimeRef.current = data[data.length - 1].time as number;
      return;
    }
    if (data.length === 0) {
      // Clear the visible series when the store is wiped (target change,
      // reconnect, or unmount). Only act if the chart was previously
      // initialised — a zero-candle snapshot before any data is a no-op.
      if (initialisedRef.current) {
        series.setData([]);
        initialisedRef.current = false;
        lastTickTimeRef.current = null;
      }
      return;
    }
    const last = data[data.length - 1];
    if (lastTickTimeRef.current === null) {
      series.setData([...data]);
      lastTickTimeRef.current = last.time as number;
      return;
    }
    if (last.time === lastTickTimeRef.current) {
      series.update(last);
    } else {
      // New bar OR a back-fill. setData is the safe choice because
      // timestamps may be out of order on the first REST poll.
      series.setData([...data]);
      lastTickTimeRef.current = last.time as number;
    }
  }, [snapshot]);

  return (
    <div
      ref={setContainer}
      data-testid="chart-canvas"
      style={{ width: '100%', height: '100%' }}
    />
  );
};

// Re-export for test scaffolding.
export type { Candle };
