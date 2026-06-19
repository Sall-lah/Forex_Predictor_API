import http from 'node:http';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const PROXY_TARGET = 'http://localhost:8000';
const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 1000;

function configureProxyRetry(
  proxy: Parameters<
    NonNullable<Parameters<typeof defineConfig>[0]['server']['proxy'][string]['configure']>
  >[0],
  path: string,
) {
  proxy.on(
    'error',
    (err: NodeJS.ErrnoException, req: http.IncomingMessage, res: http.ServerResponse) => {
      if (err.code !== 'ECONNREFUSED') {
        console.error(`\x1b[31m[proxy] ${path} error:\x1b[0m`, err.message);
        return;
      }

      const retries = Number((req as Record<string, unknown>).__retryCount || 0);
      if (retries >= MAX_RETRIES) {
        console.error(
          '\x1b[33m[proxy] Backend still not running after retries. Start with: npm run dev:api\x1b[0m',
        );
        if (res instanceof http.ServerResponse) {
          res.writeHead(502);
          res.end('Backend not available');
        }
        return;
      }

      (req as Record<string, unknown>).__retryCount = retries + 1;
      console.warn(
        `\x1b[33m[proxy] Backend not ready, retry ${retries + 1}/${MAX_RETRIES} (${path})\x1b[0m`,
      );

      setTimeout(() => {
        proxy.web(req, res, { target: PROXY_TARGET });
      }, RETRY_DELAY_MS);
    },
  );
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: PROXY_TARGET,
        changeOrigin: true,
        configure: (proxy) => configureProxyRetry(proxy, '/api'),
      },
    },
  },
});
