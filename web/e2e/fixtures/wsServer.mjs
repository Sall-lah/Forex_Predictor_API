/**
 * Local WebSocket fixture used by the Playwright e2e suite.
 *
 * Uses Node 22's built-in `WebSocket` and `WebSocketServer` (no
 * external `ws` dependency) so the suite can run without an extra
 * `npm install`.
 *
 * Behaviour:
 *   - Listens on port 5180 (override via WS_FIXTURE_PORT).
 *   - On every new connection, immediately pushes a single tick for
 *     the last candle in `candles.json` so the chart updates.
 *   - Exposes a tiny HTTP control surface on the same port:
 *       POST /push-tick   { close: number, time?: number } -> pushes a tick
 *       POST /close       { code?: number }              -> drops all clients
 *       GET  /healthz                                   -> 200 OK
 *
 * The Playwright tests use these endpoints to simulate a dropped
 * socket (reconnect test) and to push a custom tick (live-tick test).
 */

import http from 'node:http';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.WS_FIXTURE_PORT) || 5180;

const candles = JSON.parse(
  readFileSync(join(__dirname, 'candles.json'), 'utf8')
);
const lastCandle = candles[candles.length - 1];

/**
 * In-memory set of open WebSocket clients. We can't use the `ws`
 * package, so we implement the tiny server protocol by hand on top
 * of the Node `http` upgrade flow.
 */
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
      const tick = {
        type: 'tick',
        candle: {
          time: typeof parsed.time === 'number' ? parsed.time : lastCandle.time,
          open: lastCandle.open,
          high: Math.max(lastCandle.high, parsed.close),
          low: Math.min(lastCandle.low, parsed.close),
          close: parsed.close,
          volume: lastCandle.volume + 1,
        },
      };
      broadcast(tick);
      res.writeHead(204);
      res.end();
    });
    return;
  }
  res.writeHead(404, { 'content-type': 'text/plain' });
  res.end('not found');
});

server.on('upgrade', (req, socket, head) => {
  // Lightweight WebSocket handshake. We do not parse extensions; the
  // browser client only requires the basic upgrade flow.
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

  // Push the immediate tick so the chart updates from "live" without
  // the test having to wait for a real upstream.
  const initialTick = {
    type: 'tick',
    candle: { ...lastCandle, close: lastCandle.close + 0.00010 },
  };
  try {
    client.send(JSON.stringify(initialTick));
  } catch {
    // ignore
  }
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
 * text frames (opcode 0x1) and ignore everything else.
 */
function wrapSocket(socket) {
  const handlers = { message: null, close: null };
  socket.on('data', (chunk) => {
    handleFrame(chunk, socket, handlers);
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
  return api;
}

function handleFrame(chunk, socket, handlers) {
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
    // close frame
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
  console.log(`wsServer listening on http://localhost:${PORT}`);
  console.log(`  - WS at ws://localhost:${PORT}/ws/candles?...`);
  console.log(`  - HTTP control surface: /healthz, /push-tick, /close`);
});
