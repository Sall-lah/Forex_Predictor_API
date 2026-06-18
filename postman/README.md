# Postman WebSocket Test Collection

## Files

| File | Description |
|------|-------------|
| `WebSocket_Relay.postman_collection.json` | Importable Postman collection |
| `WebSocket_Messages.md` | Message format reference |

## Quick Start

1. Import `WebSocket_Relay.postman_collection.json` into Postman v10+
2. Open **BFF WebSocket - Subscribe BTC/USD 1m**
3. Add header: `Origin: http://localhost:3000`
4. Click **Connect**
5. Send subscribe message (see below)

## After Connecting

**Subscribe to BTC/USD 1-minute:**
```json
{"action":"subscribe","pair":"BTC/USD","interval":1}
```

**Subscribe to ETH/USD 5-minute:**
```json
{"action":"subscribe","pair":"ETH/USD","interval":5}
```

**Ping (keepalive):**
```json
{"action":"ping"}
```

**Unsubscribe:**
```json
{"action":"unsubscribe","pair":"BTC/USD","interval":1}
```

## Expected Responses

**CandleTick (live update):**
```json
{
  "pair": "BTC/USD",
  "interval": 1,
  "timestamp": "2026-06-18T10:30:00Z",
  "open": 65000.00,
  "high": 65050.00,
  "low": 64980.00,
  "close": 65025.00,
  "volume": 12.5,
  "is_closed": false
}
```

**Pong (response to ping):**
```json
{"type": "pong"}
```

## BFF vs Backend

| Endpoint | Port | Use Case |
|----------|------|----------|
| `ws://localhost:3000/api/v1/ws/stream` | 3000 | Through BFF (browser path) |
| `ws://localhost:8000/api/v1/ws/stream` | 8000 | Direct to backend (debugging) |

Both use the same origin check. Add `Origin: http://localhost:3000` header.

## Origin Check

The BFF and backend both validate the `Origin` header. If you get disconnected immediately:
1. Add header `Origin: http://localhost:3000`
2. Or use the direct backend endpoint (port 8000)

## CLI Alternative

```bash
npm install -g wscat
wscat -c ws://localhost:3000/api/v1/ws/stream -H "Origin: http://localhost:3000"
```
