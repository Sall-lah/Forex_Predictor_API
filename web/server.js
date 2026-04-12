import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

// BFF health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'web-bff' });
});

// Proxy API requests
app.use(
  '/api',
  createProxyMiddleware({
    target: process.env.API_URL || 'http://localhost:8000',
    changeOrigin: true,
  })
);

// Serve static React files
app.use(express.static(path.join(__dirname, 'dist')));

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`BFF Server running on port ${PORT}`);
});