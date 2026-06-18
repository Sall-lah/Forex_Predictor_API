/**
 * Generate 180 deterministic OHLCV candles starting at a fixed UTC
 * timestamp. Used by the Playwright e2e suite.
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = `${__dirname}/candles.json`;

// Fixed starting candle: 2024-05-19 00:00:00 UTC.
const START = 1716086400;
const INTERVAL = 60 * 60; // 1h
const COUNT = 180;

const candles = [];
let lastClose = 1.08000;
for (let i = 0; i < COUNT; i += 1) {
  const time = START + i * INTERVAL;
  // Deterministic pseudo-random walk so the chart shows structure.
  const drift = Math.sin(i * 0.13) * 0.0008 + ((i * 17) % 11) * 0.0001;
  const open = lastClose;
  const close = Math.max(0.5, open + drift);
  const high = Math.max(open, close) + 0.0006;
  const low = Math.min(open, close) - 0.0005;
  const volume = 80 + (i % 30) * 3;
  candles.push({
    time,
    open: round(open, 5),
    high: round(high, 5),
    low: round(low, 5),
    close: round(close, 5),
    volume: round(volume, 2),
  });
  lastClose = close;
}

function round(value, decimals) {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(candles, null, 2));
console.log(`wrote ${COUNT} candles to ${OUT}`);
