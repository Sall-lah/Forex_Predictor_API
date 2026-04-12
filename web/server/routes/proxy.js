import { createProxyMiddleware } from 'http-proxy-middleware';

const proxyRoute = createProxyMiddleware({
  target: process.env.API_URL || 'http://localhost:8000',
  changeOrigin: true,
});

export default proxyRoute;
