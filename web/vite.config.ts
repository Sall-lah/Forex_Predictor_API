import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (err.code === 'ECONNREFUSED') {
              console.error('\x1b[33m[proxy] Backend not running. Start with: npm run dev:api\x1b[0m');
            }
          });
        },
      },
      '/ws': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (err.code === 'ECONNREFUSED') {
              console.error('\x1b[33m[proxy] Backend not running. Start with: npm run dev:api\x1b[0m');
            }
          });
        },
      },
    },
  },
});