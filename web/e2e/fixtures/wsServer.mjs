/**
 * Local Kraken WebSocket v2 fixture used by the Playwright e2e suite.
 *
 * Uses Node 22's built-in `WebSocket` server primitives (no external
 * `ws` dependency) so the suite runs without an extra `npm install`.
 *
 * Behaviour:
 *   - Listens on port 5180 (override via WS_FIXTURE_PORT).
 *   - The browser harness (`wsHarness.ts`) rewrites the page's
 *     `wss://ws.kraken.com/v2` WebSocket connection to
 *     `ws://localhost:5180` (no path) so the test browser can
 *     communicate with this fixture.
 *   - On every new connection, the fixture waits for a Kraken v2
 *     subscribe message, then immediately pushes one OHLC update
 *     using the last candle in `candles.json` so the chart appears
 *     "live" without the test waiting on a real upstream.
 *   - Exposes a tiny HTTP control surface on the same port:
 *       POST /push-tick   { symbol?, close: number, time?, interval? }
 *                          -> pushes a Kraken v2 OHLC update frame
 *       POST /close       { code?: number } -> drops all clients
 *       GET  /healthz                       -> 200 OK
 *
 * The Playwright tests use these endpoints to simulate a dropped
 * socket (reconnect test), to push a custom tick (live-tick test),
 * and to drive the Kraken subscribe/unsubscribe flow (pair-switch).
 */

import http from 'node:http';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.WS_FIXTURE_PORT) || 5180;

const candles = JSON.parse(readFileSync(join(__dirname, 'candles.json'), 'utf8'));
const lastCandle = candles[candles.length - 1];
const lastCandleTime = Math.floor(new Date(lastCandle.timestamp).getTime() / 1000);

const clients = new Set();

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/healthz') {
    res.writeHead(200, { 'content-type': 'text/plain' });
    res.end('ok');
    return;
  }
  if (req.method === 'POST' && req.url === '/close') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      const parsed = body ? safeJson(body) : {};
      // 1004, 1005, 1006, 1015 are reserved and must not appear on
      // the wire from server-initiated closes. Coerce any reserved
      // code to 1011 (server error) so the browser still surfaces
      // the disconnect.
      const requested = typeof parsed?.code === 'number' ? parsed.code : 1011;
      const RESERVED = new Set([1004, 1005, 1006, 1015]);
      const code = RESERVED.has(requested) ? 1011 : requested;
      for (const client of clients) {
        try {
          client.close(code);
        } catch {
          // ignore
        }
      }
      res.writeHead(204);
      res.end();
    });
    return;
  }
  if (req.method === 'POST' && req.url === '/push-tick') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      const parsed = body ? safeJson(body) : {};
      if (!parsed || typeof parsed.close !== 'number') {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ detail: 'close (number) is required' }));
        return;
      }
      const symbol =
        typeof parsed.symbol === 'string' ? parsed.symbol : lastCandle.symbol || 'BTC/USD';
      const interval = typeof parsed.interval === 'number' ? parsed.interval : 60;
      const timeSeconds =
        typeof parsed.time === 'number'
          ? parsed.time
          : (lastCandleTime ?? Math.floor(Date.now() / 1000));
      const intervalBegin = new Date(timeSeconds * 1000).toISOString();
      const high = Math.max(lastCandle.high ?? parsed.close, parsed.close);
      const low = Math.min(lastCandle.low ?? parsed.close, parsed.close);
      const frame = {
        channel: 'ohlc',
        type: 'update',
        data: [
          {
            symbol,
            interval,
            interval_begin: intervalBegin,
            open: String(lastCandle.open ?? parsed.close),
            high: String(high),
            low: String(low),
            close: String(parsed.close),
            volume: String((lastCandle.volume ?? 0) + 1),
          },
        ],
      };
      broadcast(frame);
      res.writeHead(204);
      res.end();
    });
    return;
  }
  res.writeHead(404, { 'content-type': 'text/plain' });
  res.end('not found');
});

server.on('upgrade', (req, socket, head) => {
  if (req.headers.upgrade?.toLowerCase() !== 'websocket') {
    socket.destroy();
    return;
  }
  const key = req.headers['sec-websocket-key'];
  if (!key) {
    socket.destroy();
    return;
  }
  const accept = createAcceptValue(key);
  const headers = [
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${accept}`,
    '',
    '',
  ].join('\r\n');
  socket.write(headers);

  const client = wrapSocket(socket);
  clients.add(client);

  // After receiving a subscribe message, push a single tick using
  // the last fixture candle. The pair/interval come from the
  // subscribe message so the pair-switch test exercises the right
  // values.
  client.on('message', (raw) => {
    let parsed = null;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return;
    }
    if (!parsed || parsed.method !== 'subscribe') return;
    const params = parsed.params ?? {};
    const symbol = Array.isArray(params.symbol) ? params.symbol[0] : 'BTC/USD';
    const interval = typeof params.interval === 'number' ? params.interval : 60;
    const intervalBegin = lastCandle.timestamp;
    const initialFrame = {
      channel: 'ohlc',
      type: 'update',
      data: [
        {
          symbol,
          interval,
          interval_begin: intervalBegin,
          open: String(lastCandle.open),
          high: String(Math.max(lastCandle.high, lastCandle.close + 0.0001)),
          low: String(lastCandle.low),
          close: String(lastCandle.close + 0.0001),
          volume: String(lastCandle.volume + 1),
        },
      ],
    };
    try {
      client.send(JSON.stringify(initialFrame));
    } catch {
      // ignore
    }
  });
});

function broadcast(payload) {
  const data = JSON.stringify(payload);
  for (const client of clients) {
    try {
      client.send(data);
    } catch {
      // ignore
    }
  }
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

/**
 * Wrap a raw TCP socket in a tiny object that exposes `send` (text
 * frame), `close`, and a 'message' callback wired from data frames.
 *
 * Frame format reference: RFC 6455. We only emit / consume small
 * text frames (opcode 0x1) and close frames (opcode 0x8).
 */
function wrapSocket(socket) {
  const handlers = { message: null, close: null };
  const api = {
    send(text) {
      const payload = Buffer.from(text, 'utf8');
      const len = payload.length;
      // Server-to-client frames must NOT be masked (no 0x80 bit on
      // the second byte, and no 4-byte mask key).
      let header;
      if (len < 126) {
        header = Buffer.from([0x81, len]);
      } else if (len < 65536) {
        header = Buffer.alloc(4);
        header[0] = 0x81;
        header[1] = 126;
        header.writeUInt16BE(len, 2);
      } else {
        header = Buffer.alloc(10);
        header[0] = 0x81;
        header[1] = 127;
        header.writeBigUInt64BE(BigInt(len), 2);
      }
      socket.write(Buffer.concat([header, payload]));
    },
    close(code = 1000) {
      const payload = Buffer.alloc(2);
      payload.writeUInt16BE(code, 0);
      const header = Buffer.from([0x88, payload.length]);
      socket.write(Buffer.concat([header, payload]));
      socket.end();
    },
    on(name, fn) {
      handlers[name] = fn;
    },
  };
  socket.on('data', (chunk) => {
    handleFrame(chunk, socket, handlers, api);
  });
  socket.on('close', () => {
    clients.delete(api);
    if (handlers.close) handlers.close();
  });
  socket.on('error', () => {
    try {
      socket.destroy();
    } catch {
      // ignore
    }
  });
  return api;
}

function handleFrame(chunk, socket, handlers, api) {
  if (chunk.length < 2) return;
  const opcode = chunk[0] & 0x0f;
  let offset = 2;
  let len = chunk[1] & 0x7f;
  if (len === 126) {
    len = chunk.readUInt16BE(2);
    offset = 4;
  } else if (len === 127) {
    len = Number(chunk.readBigUInt64BE(2));
    offset = 10;
  }
  if (chunk.length < offset + len) return; // incomplete frame
  const payload = chunk.slice(offset, offset + len).toString('utf8');
  if (opcode === 0x1 && handlers.message) {
    handlers.message(payload);
  } else if (opcode === 0x8) {
    if (handlers.close) handlers.close();
    try {
      socket.end();
    } catch {
      // ignore
    }
  }
}

function createAcceptValue(key) {
  // Per RFC 6455: SHA-1 of (key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').
  return crypto
    .createHash('sha1')
    .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');
}

server.listen(PORT, () => {
  console.log(`krakenWsServer listening on http://localhost:${PORT}`);
  console.log(`  - WS at ws://localhost:${PORT} (Kraken v2 protocol)`);
  console.log(`  - HTTP control surface: /healthz, /push-tick, /close`);
});
