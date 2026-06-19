# API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints return JSON. Error responses follow the format `{"detail": "<message>"}`.

## Endpoints

### GET /historic-data/live

Fetch live hourly OHLCV data from Kraken.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pair` | string | Yes | — | Trading pair (e.g., `BTC/USD`, `ETH/USD`) |
| `interval` | integer | No | `60` | Time frame interval in minutes. Valid values: `1, 5, 15, 30, 60, 240, 1440, 10080, 21600` |
| `count` | integer | No | `180` | Number of OHLCV records to fetch |

**Response (200):**

```json
{
  "symbol": "BTC/USD",
  "total_records": 180,
  "data": [
    {
      "timestamp": "2026-03-23T14:00:00Z",
      "open": 87234.5,
      "high": 87450.2,
      "low": 87100.0,
      "close": 87380.1,
      "volume": 123.456
    }
  ]
}
```

**Errors:**

| Status | Exception | Description |
|--------|-----------|-------------|
| 422 | `DataValidationError` | Invalid pair or parameters |
| 502 | `DataFetchError` | Failed to fetch data from Kraken |

**Example (curl):**

```bash
curl "http://localhost:8000/api/v1/historic-data/live?pair=BTC/USD&interval=60&count=180"
```

**Example (Python):**

```python
import httpx

response = httpx.get(
    "http://localhost:8000/api/v1/historic-data/live",
    params={"pair": "BTC/USD", "interval": 60, "count": 180}
)
data = response.json()
```

---

### POST /prediction/predict

Predict forex price movement probability using LightGBM model.

**Request Body:**

```json
{
  "pair": "BTC/USD"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pair` | string | Yes | Kraken trading pair (min 1 character) |

**Response (200):**

```json
{
  "pair": "BTC/USD",
  "probability_up": 0.45,
  "probability_down": 0.35,
  "probability_straight": 0.20,
  "computed_at": "2026-06-19T12:00:00Z",
  "valid_until": "2026-06-19T13:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `pair` | string | Trading pair that was analyzed |
| `probability_up` | float | Probability of upward movement (0.0-1.0) |
| `probability_down` | float | Probability of downward movement (0.0-1.0) |
| `probability_straight` | float | Probability of straight/hold movement (0.0-1.0) |
| `computed_at` | datetime | UTC timestamp when prediction was computed |
| `valid_until` | datetime | UTC timestamp when prediction expires |

**Errors:**

| Status | Exception | Description |
|--------|-----------|-------------|
| 422 | `DataValidationError` | Invalid pair or data validation failed |
| 422 | `InsufficientDataError` | Not enough data for feature extraction |
| 502 | `DataFetchError` | Failed to fetch data from Kraken |
| 503 | `ModelNotLoadedError` | ML model unavailable |

**Example (curl):**

```bash
curl -X POST "http://localhost:8000/api/v1/prediction/predict" \
  -H "Content-Type: application/json" \
  -d '{"pair": "BTC/USD"}'
```

**Example (Python):**

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/prediction/predict",
    json={"pair": "BTC/USD"}
)
prediction = response.json()
print(f"Up: {prediction['probability_up']:.2%}")
```

---

### GET /subscriptions

Return configured trading pair subscriptions from environment variables.

**Parameters:** None

**Response (200):**

```json
{
  "subscriptions": [
    {
      "pair": "BTC/USD",
      "intervals": [1, 5, 15, 60, 240]
    },
    {
      "pair": "ETH/USD",
      "intervals": [60]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `subscriptions` | array | List of configured trading pair subscriptions |
| `subscriptions[].pair` | string | Trading pair symbol |
| `subscriptions[].intervals` | array[int] | OHLC interval minutes to subscribe to |

**Example (curl):**

```bash
curl "http://localhost:8000/api/v1/subscriptions"
```

**Example (Python):**

```python
import httpx

response = httpx.get("http://localhost:8000/api/v1/subscriptions")
subs = response.json()["subscriptions"]
for sub in subs:
    print(f"{sub['pair']}: intervals {sub['intervals']}")
```

---

## Schemas

### OHLCVRecord

Single OHLCV candlestick record.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `timestamp` | datetime | — | UTC timestamp for candle start time |
| `open` | float | `> 0` | Opening price |
| `high` | float | `> 0` | Highest price in period |
| `low` | float | `> 0` | Lowest price in period |
| `close` | float | `> 0` | Closing price |
| `volume` | float | `>= 0` | Trade volume in period |

### HistoricDataRequest

Internal request model for historic data service.

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `pair` | string | — | — | Trading pair symbol |
| `count` | integer | `720` | `> 0` | Number of periods to fetch |
| `interval` | integer | `60` | `> 0` | Candle interval in minutes |

### HistoricDataResponse

Response containing historic OHLCV data.

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading pair symbol |
| `total_records` | integer | Number of OHLCV records |
| `data` | array[OHLCVRecord] | OHLCV candlestick records |

### PredictionRequest

Request for forex price movement prediction.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `pair` | string | `min_length=1` | Kraken trading pair |

### PredictionResponse

Response containing prediction probabilities.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `pair` | string | — | Trading pair analyzed |
| `probability_up` | float | `0.0-1.0` | Probability of upward movement |
| `probability_down` | float | `0.0-1.0` | Probability of downward movement |
| `probability_straight` | float | `0.0-1.0` | Probability of straight/hold movement |
| `computed_at` | datetime | — | Prediction computation timestamp (UTC) |
| `valid_until` | datetime | — | Prediction expiration timestamp (UTC) |

### SubscriptionPair

A trading pair and its OHLC intervals.

| Field | Type | Description |
|-------|------|-------------|
| `pair` | string | Trading pair symbol |
| `intervals` | array[int] | OHLC interval minutes |

### SubscriptionResponse

Response containing all configured subscriptions.

| Field | Type | Description |
|-------|------|-------------|
| `subscriptions` | array[SubscriptionPair] | Configured trading pair subscriptions |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Exception Hierarchy

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `BaseAppException` | 500 | Catch-all for unhandled application errors |
| `ModelNotLoadedError` | 503 | ML model artifact missing or corrupt |
| `DataFetchError` | 502 | Upstream data source (Kraken) failed |
| `DataValidationError` | 422 | Domain-level validation failed |
| `InsufficientDataError` | 422 | Not enough data rows for operation |
