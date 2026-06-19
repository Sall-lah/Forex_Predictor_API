# Architecture

## Module Structure

```
api/app/
├── main.py                    # FastAPI app, exception handlers, router mount
├── api/
│   └── router.py              # Central router aggregation
├── core/
│   ├── config.py              # Typed settings (pydantic-settings)
│   └── exceptions.py          # Domain exception hierarchy
├── features/
│   ├── historic_data/         # OHLCV data fetching feature
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── prediction/            # ML prediction feature
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── ml_models/         # LightGBM model artifacts
│   └── subscriptions/         # Trading pair subscriptions
│       ├── router.py
│       └── schemas.py
├── middleware/                 # Cross-cutting middleware (placeholder)
└── shared/
    └── ohlcv/                 # Shared OHLCV infrastructure
        ├── base.py            # DataProvider Protocol
        ├── factory.py         # Provider factory
        ├── kraken_provider.py # Kraken HTTP client
        ├── ohlc_dataframe.py  # DataFrame wrapper
        └── pair_normalizer.py # Pair name normalization
```

## Layer Architecture

The API follows a three-layer architecture pattern:

```
┌─────────────────────────────────────────────┐
│              HTTP Layer (Routers)            │
│  - Parse request parameters/body            │
│  - Validate via Pydantic schemas            │
│  - Dependency injection for services        │
├─────────────────────────────────────────────┤
│           Business Logic (Services)         │
│  - Orchestrate workflows                    │
│  - Coordinate shared modules                │
│  - Raise domain exceptions                  │
├─────────────────────────────────────────────┤
│        Shared Infrastructure                │
│  - KrakenProvider: HTTP transport           │
│  - OHLCVDataFrame: Data validation          │
│  - Pair normalizer: Symbol mapping          │
└─────────────────────────────────────────────┘
```

### Router Layer

Routers define HTTP contracts and handle input parsing. Each feature has its own router module.

**Responsibilities:**
- Define endpoint paths, methods, and response models
- Parse query parameters and request bodies via Pydantic
- Inject service dependencies via `Depends()`
- Delegate business logic to services

**Example pattern:**
```python
router = APIRouter()

def get_service() -> HistoricDataService:
    return HistoricDataService()

@router.get("/live", response_model=HistoricDataResponse)
async def get_live_data(
    pair: str = Query(...),
    service: HistoricDataService = Depends(get_service),
) -> HistoricDataResponse:
    request = HistoricDataRequest(pair=pair, ...)
    return await service.get_live_data(request)
```

### Service Layer

Services contain business logic and orchestrate workflows. They are framework-agnostic and raise domain exceptions.

**Responsibilities:**
- Execute feature-specific workflows
- Coordinate shared modules (data fetching, preprocessing)
- Manage caching (prediction cache)
- Raise domain exceptions on failure

**Key services:**
- `HistoricDataService`: Fetches and validates OHLCV data
- `PredictionService`: Full ML pipeline (fetch → preprocess → infer → respond)
- `ModelLoader`: Thread-safe singleton for ML model loading

### Shared Infrastructure

Reusable modules for data transport and validation.

**Modules:**
- `KrakenProvider`: Async HTTP client for Kraken OHLC API
- `OHLCVDataFrame`: DataFrame wrapper with column/row validation
- `pair_normalizer`: Maps user-friendly pair names to Kraken canonical forms

## Data Flow

### Historic Data Flow

```
Client Request
     │
     ▼
GET /historic-data/live?pair=BTC/USD
     │
     ▼
Router: Parse query params → HistoricDataRequest
     │
     ▼
HistoricDataService.get_live_data()
     │
     ├──► KrakenProvider.fetch_ohlcv_data()
     │         │
     │         ▼
     │    Kraken API (HTTPS)
     │         │
     │         ▼
     │    Raw OHLCV JSON
     │
     ├──► OHLCVDataFrame.from_provider_response()
     │         │
     │         ▼
     │    Validate columns, row count
     │
     └──► Map to OHLCVRecord Pydantic models
              │
              ▼
     HistoricDataResponse
              │
              ▼
         JSON Response
```

### Prediction Flow

```
Client Request
     │
     ▼
POST /prediction/predict  {"pair": "BTC/USD"}
     │
     ▼
Router: Parse body → PredictionRequest
     │
     ▼
PredictionService.predict()
     │
     ├──► normalize_pair() → "XXBTZUSD"
     │
     ├──► Check prediction cache (per-hour TTL)
     │
     ├──► KrakenProvider.fetch_ohlcv_data() (720 candles)
     │
     ├──► OHLCVPreprocessor.extract_features()
     │         │
     │         ├──► Trend indicators (EMA, ADX, MACD, etc.)
     │         ├──► Momentum indicators (RSI, ROC, etc.)
     │         ├──► Volatility indicators (ATR, Bollinger, etc.)
     │         └──► Custom features (returns, ranges, etc.)
     │
     ├──► Align features to model schema
     │
     ├──► ModelLoader.get_model() → LightGBM
     │
     ├──► model.predict_proba()
     │
     └──► Map probabilities to PredictionResponse
              │
              ▼
         JSON Response
```

## Dependency Injection Pattern

The API uses FastAPI's `Depends()` mechanism for service instantiation:

```python
def get_service() -> HistoricDataService:
    """Factory function - creates new instance per request."""
    return HistoricDataService()

@router.get("/live")
async def get_live_data(
    service: HistoricDataService = Depends(get_service),
):
    ...
```

**Pattern details:**
- Services have `None` defaults for dependencies with internal fallback
- Each request gets a fresh service instance
- Makes services testable via mock injection

**Example from PredictionService:**
```python
class PredictionService:
    def __init__(
        self,
        api_client: KrakenProvider | None = None,
        model_loader: ModelLoader | None = None,
        preprocessor: OHLCVPreprocessor | None = None,
    ):
        self._api_client = api_client or KrakenProvider()
        self._model_loader = model_loader or ModelLoader()
        self._preprocessor = preprocessor or OHLCVPreprocessor()
```

## Router Composition

```
app.main.app
  └── include_router(api_router, prefix="/api/v1")
        ├── include_router(historic_data_router, prefix="/historic-data")
        │     └── GET /live
        ├── include_router(prediction_router, prefix="/prediction")
        │     └── POST /predict
        └── include_router(subscriptions_router, prefix="")
              └── GET /subscriptions
```

## Supported Trading Pairs

The pair normalizer maps user-friendly names to Kraken canonical forms:

| Input Forms | Canonical (Kraken) |
|-------------|-------------------|
| `BTC/USD`, `BTCUSD`, `XBT/USD`, `XBTUSD` | `XXBTZUSD` |
| `ETH/USD`, `ETHUSD` | `XETHZUSD` |
