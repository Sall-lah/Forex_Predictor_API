import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';

import healthRoute from './routes/health.js';
import proxyRoute, { wsProxy } from './routes/proxy.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Explicit CORS allowlist read from ALLOWED_ORIGINS (comma-separated).
// Falls back to the dev defaults so the existing local setup keeps
// working without configuration changes.
const allowedOrigins = (process.env.ALLOWED_ORIGINS ||
  'http://localhost:3000,http://localhost:5173')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(
  cors({
    origin: (origin, callback) => {
      // Allow non-browser requests (no Origin header) and same-origin.
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
        return;
      }
      callback(new Error(`CORS: origin '${origin}' not allowed`));
    },
    credentials: true,
  })
);

// Defense-in-depth origin check on the WebSocket path. The FastAPI
// side also enforces this via WS_ALLOWED_ORIGINS, but a second check
// at the BFF layer prevents spoofed origins from reaching the
// upstream proxy entirely.
app.use('/api/v1/ws', (req, res, next) => {
  const origin = req.headers.origin;
  if (origin && !allowedOrigins.includes(origin)) {
    res.status(403).json({ detail: 'Origin not allowed' });
    return;
  }
  next();
});

// BFF health check
app.use('/health', healthRoute);

// Proxy API requests (REST + WebSocket via `ws: true` in the proxy config)
app.use('/api', proxyRoute);

// WebSocket relay path. The new `LiveFeedController` opens a socket
// at `ws://<host>/ws/candles?pair=...&interval=...`; the proxy keeps
// the upgrade header intact so it reaches the backend.
app.use('/ws', wsProxy);

// Serve static React files
app.use(express.static(path.join(__dirname, '..', 'dist')));

// Fallback to index.html for SPA routing
app.get(/(.*)/, (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

export default app;
