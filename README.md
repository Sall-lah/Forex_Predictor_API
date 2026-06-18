# Forex Predictor

A monorepo for the Forex Predictor application, containing both the backend API and the frontend web application.

## Setup Instructions

### Prerequisites
- Node.js (for the web frontend)
- Conda (for the backend API environment)

### Unified Development Setup

We provide a unified script that runs both the frontend and backend concurrently. The backend is automatically executed within the required conda environment, so manual activation is not needed.

1. Create the backend conda environment (one-time setup):
   ```bash
   cd api
   conda env create -f environment.yml
   cd ..
   ```
   **Note:** The unified runner requires the conda environment to be explicitly named `forex_prediction` (which is the default configured in `environment.yml`).

2. Install frontend dependencies (one-time setup):
   ```bash
   npm run install:all
   ```

3. Copy `api/.env.example` to `api/.env` and update any configuration values.

4. Launch both the backend API and the frontend web app simultaneously:
   ```bash
   npm run dev
   ```

> **Do not pass `--workers N` to uvicorn.** The realtime relay must run in a single worker. See the *Realtime relay* section below.

## Features

### Backend API
- Built with FastAPI for high performance and automatic interactive API documentation.
- Robust configuration management via environment variables.
- Configured with `pytest` for unit testing.

### Frontend Web App
- Powered by React/Vite for fast development and build processes.
- Styled using Tailwind CSS for responsive and modern UI.
- Designed to consume the Backend API to deliver forex predictions.

## Realtime relay

The backend maintains a single WebSocket connection to Kraken's v2 API
(`wss://ws.kraken.com/v2`), subscribes to the configured (pair,
interval) tuples, and broadcasts each tick to all connected UI
clients.

### Endpoints
- **WebSocket stream:** `ws://<host>/api/v1/ws/stream`
  - Accepts JSON `{"action": "subscribe" | "unsubscribe" | "ping", "pair": "...", "interval": N}` messages.
  - Emits canonical `CandleTick` payloads (ISO-8601 UTC `timestamp`,
    `is_closed` boolean for the forming-closed merge semantics).
- **Health:** `GET /health` now returns
  ```json
  {
    "status": "healthy | degraded | unhealthy",
    "upstream": {
      "kraken_connected": true,
      "last_tick_at": "...",
      "reconnect_count": 0,
      "subscriptions": [{"pair": "BTC/USD", "interval": 1}]
    },
    "clients": { "connected": 0, "slow_disconnects": 0 }
  }
  ```
  Status is `unhealthy` if upstream has been disconnected for > 30s.

### Configuration

| Env var | Default | Purpose |
| --- | --- | --- |
| `KRAKEN_WS_URL` | `wss://ws.kraken.com/v2` | Upstream endpoint |
| `KRAKEN_WS_RECONNECT_BACKOFF_SECONDS` | `1,2,4,8,16,30` | Backoff schedule (seconds) |
| `KRAKEN_WS_PING_INTERVAL` / `_TIMEOUT` | `20` / `20` | WebSocket keepalive |
| `WS_BROADCAST_QUEUE_SIZE` | `64` | Per-client queue depth |
| `WS_SLOW_CLIENT_OVERFLOW_THRESHOLD` | `10` | Force-disconnect a slow client after N drops |
| `WS_RELAY_SUBSCRIPTIONS` | `[]` | JSON list of `{"pair": "...", "interval": N}` |
| `WS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | CSWSH allowlist |

### CSWSH mitigation

- The FastAPI WS endpoint validates `Origin` against `WS_ALLOWED_ORIGINS` and
  closes the upgrade with code `1008` on rejection.
- The BFF (`web/server/app.js`) applies the same allowlist to HTTP CORS
  and to the `/api/v1/ws` path (defense in depth).

### Known scaling limitation

The relay is a process-local singleton (Kraken subscription is
deduplicated to a single upstream connection per process). Running
with `uvicorn --workers N` would open N upstream connections, which
risks hitting Kraken's per-IP subscription budget. The follow-up is
to externalise the relay into a dedicated process that publishes to a
shared bus (Redis pub/sub or NATS); see
`openspec/changes/realtime-websocket-relay/design.md §"Process Topology"`.

### Manual test plan

Run from the repo root with two terminals:

```bash
# Terminal 1 (api)
cd api && uvicorn app.main:app --reload --port 8000

# Terminal 2 (web)
cd web && npm run dev
```

Then exercise:

1. **Smoke** — open `http://localhost:3000`. `HealthStatus` should
   show `LIVE` within 2s; chart should render with ~180 historical
   candles.
2. **Single upstream, multiple clients** — open 5 browser tabs; tail
   the API logs and confirm exactly **one** Kraken subscription.
3. **Live updates** — watch the rightmost candle; `open`/`close` should
   change at sub-second cadence.
4. **Raw WS inspection** — `wscat -c ws://localhost:8000/api/v1/ws/stream`
   should yield `CandleTick` messages, with `is_closed: false` for
   the forming candle.
5. **REST + WS cohesion** — the last REST candle and the first WS
   forming candle share the same `timestamp`; the chart should
   overwrite without flicker.
6. **Upstream drop** — pause the API process; the UI should
   transition to `RECONNECTING` → `LIVE` on resume, and
   `upstream.reconnect_count` should increment.
7. **Slow consumer** — open a Python client that never reads, plus
   three normal tabs; the slow client should be force-disconnected
   and `clients.slow_disconnects` should increment.
8. **BFF WS upgrade** — `wscat -c ws://localhost:3000/api/v1/ws/stream`
   should succeed and stream ticks.
9. **Visibility pause** — switching tabs should close + reopen the
   socket cleanly.
10. **Health endpoint** — `curl http://localhost:8000/health | jq`
    returns the full upstream / clients payload.
