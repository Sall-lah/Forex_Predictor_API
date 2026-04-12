import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';

import healthRoute from './routes/health.js';
import proxyRoute from './routes/proxy.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.use(cors());

// BFF health check
app.use('/health', healthRoute);

// Proxy API requests
app.use('/api', proxyRoute);

// Serve static React files
app.use(express.static(path.join(__dirname, '..', 'dist')));

// Fallback to index.html for SPA routing
app.get(/(.*)/, (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

export default app;
