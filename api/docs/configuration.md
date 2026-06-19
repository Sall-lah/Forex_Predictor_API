# Configuration

## Overview

The API uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for typed configuration management. Settings are loaded from environment variables with `.env` file support.

## Environment Variables

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | string | `development` | Runtime environment (`development`, `production`, `testing`) |
| `LOG_LEVEL` | string | `info` | Logging level (`debug`, `info`, `warning`, `error`, `critical`) |

### API Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_VERSION` | string | `v1` | API version string |
| `API_PREFIX` | string | `/api/v1` | URL prefix for all API routes |

### Data Provider Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATA_PROVIDER` | string | `kraken` | Active data provider name |

### Kraken API Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KRAKEN_OHLC_URL` | string | `https://api.kraken.com/0/public/OHLC` | Kraken OHLC endpoint URL |
| `KRAKEN_TIMEOUT` | float | `15.0` | HTTP timeout for Kraken requests (seconds) |

### Trading Subscriptions

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TRADING_SUBSCRIPTIONS` | string | `[]` | JSON-encoded list of subscription objects |

**Format:**
```json
[
  {"pair": "BTC/USD", "interval": 60},
  {"pair": "ETH/USD", "interval": 1}
]
```

**Example `.env`:**
```
TRADING_SUBSCRIPTIONS=[{"pair": "BTC/USD", "interval": 60}, {"pair": "ETH/USD", "interval": 1}]
```

### ML Model Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODEL_DIR` | string | `app/features/prediction/ml_models` | Relative path to model directory |
| `MODEL_FILENAME` | string | `lightgbm_model_forex.pkl` | Model artifact filename |

### Feature Extraction Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PREDICTION_FETCH_CANDLES` | int | `720` | Number of hourly candles to fetch for prediction |
| `MIN_ROWS_FOR_FEATURES` | int | `168` | Minimum rows required for feature extraction (1 week) |

## Computed Properties

The `Settings` class provides computed properties that derive values from the base settings:

### `model_path`

Returns the absolute path to the ML model file.

**Derivation:** `Path(__file__).parent.parent.parent / MODEL_DIR / MODEL_FILENAME`

**Usage:**
```python
from app.core.config import get_settings

settings = get_settings()
model_path = settings.model_path  # e.g., /path/to/api/app/features/prediction/ml_models/lightgbm_model_forex.pkl
```

### `ws_relay_subscriptions`

Parses `TRADING_SUBSCRIPTIONS` JSON into a list of dictionaries.

**Returns:** `list[dict[str, int | str]]`

**Usage:**
```python
from app.core.config import get_settings

settings = get_settings()
subs = settings.ws_relay_subscriptions
# [{"pair": "BTC/USD", "interval": 60}, {"pair": "ETH/USD", "interval": 1}]
```

## Settings Loading Order

Settings are loaded in the following order (later sources override earlier ones):

1. `init_settings` - Constructor arguments
2. `dotenv_settings` - `.env` file
3. `env_settings` - System environment variables
4. `file_secret_settings` - Secret files

**Important:** `.env` file values override system environment variables. This is the opposite of the default pydantic-settings behavior.

## Configuration Loading

### Singleton Pattern

Settings are cached using `functools.lru_cache` to ensure a single instance is used across the application:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... settings definition ...

@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
```

### Usage

```python
from app.core.config import get_settings

# Get cached settings instance
settings = get_settings()

# Access settings
print(settings.ENVIRONMENT)      # "development"
print(settings.API_PREFIX)       # "/api/v1"
print(settings.model_path)       # Path to model file
```

## .env File

The API loads configuration from `api/.env`. Copy `.env.example` to `.env` and customize:

```bash
cp api/.env.example api/.env
```

**Example `.env`:**
```env
ENVIRONMENT=development
LOG_LEVEL=info
API_PREFIX=/api/v1
DATA_PROVIDER=kraken
KRAKEN_OHLC_URL=https://api.kraken.com/0/public/OHLC
KRAKEN_TIMEOUT=15.0
TRADING_SUBSCRIPTIONS=[{"pair": "BTC/USD", "interval": 60}]
MODEL_DIR=app/features/prediction/ml_models
MODEL_FILENAME=lightgbm_model_forex.pkl
PREDICTION_FETCH_CANDLES=720
MIN_ROWS_FOR_FEATURES=168
```
