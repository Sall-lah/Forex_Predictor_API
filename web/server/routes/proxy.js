/**
 * The BFF reverse-proxies both REST and WebSocket traffic to the
 * FastAPI backend. Two distinct paths are exposed:
 *   - `/api/*` -> /api/* (handled by the existing createProxyMiddleware)
 *   - `/ws/*`  -> /ws/*  (forwarded as-is via the same proxy; the
 *                     `ws: true` flag in the config flips on the
 *                     WebSocket upgrade)
 *
 * The `ws` option is REQUIRED for the upgrade header to be forwarded
 * to the upstream; without it browser WebSockets silently fail at
 * the BFF layer.
 */

import { createProxyMiddleware, fixRequestBody } from 'http-proxy-middleware';

const apiTarget = process.env.API_URL || 'http://localhost:8000';

export const apiProxy = createProxyMiddleware({
  target: apiTarget,
  changeOrigin: true,
  ws: true,
  on: {
    proxyReq: fixRequestBody,
  },
});

export const wsProxy = createProxyMiddleware({
  target: apiTarget,
  changeOrigin: true,
  ws: true,
  pathRewrite: { '^/ws': '/ws' },
  on: {
    proxyReq: fixRequestBody,
  },
});

export default apiProxy;
