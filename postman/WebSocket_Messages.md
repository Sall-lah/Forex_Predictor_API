# WebSocket Relay - Test Messages

## Prerequisites

1. Start the API server: `uvicorn app.main:app --app-dir api --reload`
2. Open Postman v10+ with WebSocket support
3. Import the collection: `WebSocket_Relay.postman_collection.json`

## Connection

**Endpoint:** `ws://localhost:8000/api/v1/ws/stream`

## Messages to Send

### Subscribe to BTC/USD 1-minute candles

```json
{
  "action": "subscribe",
  "pair": "BTC/USD",
  "interval": 1
}
```

### Subscribe to ETH/USD 5-minute candles

```json
{
  "action": "subscribe",
  "pair": "ETH/USD",
  "interval": 5
}
```

### Unsubscribe from BTC/USD

```json
{
  "action": "unsubscribe",
  "pair": "BTC/USD",
  "interval": 1
}
```

### Ping (keepalive)

```json
{
  "action": "ping"
}
```

## Expected Responses

### CandleTick (live update)

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

### Pong (response to ping)

```json
{
  "type": "pong"
}
```

### Status (connection status)

```json
{
  "type": "status",
  "last_successful_tick_at": "2026-06-18T10:30:00Z",
  "reconnect_count": 0,
  "kraken_connected": true
}
```

## Testing Scenarios

### 1. Basic Connection Test

1. Connect to `ws://localhost:8000/api/v1/ws/stream`
2. Verify connection is established
3. Send a ping message
4. Verify pong response

### 2. Subscribe and Receive Ticks

1. Connect to the WebSocket
2. Send subscribe message for BTC/USD 1m
3. Wait for CandleTick messages
4. Verify messages contain correct pair and interval

### 3. Multiple Subscriptions

1. Connect to the WebSocket
2. Subscribe to BTC/USD 1m
3. Subscribe to ETH/USD 5m
4. Verify ticks for both pairs

### 4. Unsubscribe

1. Connect and subscribe to BTC/USD
2. Verify ticks are received
3. Send unsubscribe message
4. Verify no more BTC/USD ticks

### 5. Slow Consumer Test

1. Connect but don't read messages
2. Wait for overflow threshold
3. Verify client is disconnected

## Troubleshooting

### Connection Refused

- Ensure API server is running on port 8000
- Check if port is not blocked by firewall

### Origin Rejected

- The WebSocket checks the Origin header
- Add `Origin: http://localhost:3000` to headers if needed
- Or set `WS_ALLOWED_ORIGINS` in `.env`

### No Messages Received

- Check if Kraken WebSocket is connected
- Verify subscription message format
- Check API logs for errors

## Environment Variables

```bash
# In api/.env
KRAKEN_WS_URL=wss://ws.kraken.com/v2
WS_ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```
