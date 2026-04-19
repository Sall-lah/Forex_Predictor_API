import { createProxyMiddleware } from 'http-proxy-middleware';

// Note: http-proxy-middleware automatically forwards all query parameters (like `interval`)
// directly to the backend target, making redundant validation here unnecessary.
const proxyRoute = createProxyMiddleware({
  target: process.env.API_URL || 'http://localhost:8000',
  changeOrigin: true,
});

export default proxyRoute;
