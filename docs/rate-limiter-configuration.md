# Rate Limiter Configuration Guide

## Overview

The API uses token-bucket rate limiting with:

- Global defaults for uncategorized endpoints.
- Per-endpoint overrides for prediction and historic-data routes.
- In-memory storage guardrails for capacity and TTL cleanup.

Configuration is loaded from environment variables in `app/core/config.py`.

## Environment Variables

| Variable | Default | Purpose |
|---|---:|---|
| `RATE_LIMIT_DEFAULT_CAPACITY` | `60` | Burst capacity for endpoints that do not match a specialized policy. |
| `RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND` | `1.0` | Refill speed for the default policy (tokens/second). |
| `RATE_LIMIT_PREDICTION_CAPACITY` | `10` | Burst capacity for prediction endpoints. |
| `RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND` | `0.1666666667` (`10/60`) | Prediction policy refill speed (tokens/second). |
| `RATE_LIMIT_HISTORICAL_CAPACITY` | `100` | Burst capacity for historical data endpoints. |
| `RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND` | `1.6666666667` (`100/60`) | Historical policy refill speed (tokens/second). |
| `RATE_LIMIT_STORAGE_MAX_ENTRIES` | `100000` | Upper bound for in-memory bucket state entries. |
| `RATE_LIMIT_STORAGE_TTL_SECONDS` | `3600` | Expiry window for inactive bucket state entries. |
| `RATE_LIMIT_TRUSTED_PROXY_IPS` | `""` | Comma-separated trusted proxy IPs allowed to influence `X-Forwarded-For` resolution. |
| `RATE_LIMIT_EXEMPT_PATHS` | `"/health,/docs,/redoc,/openapi.json"` | Comma-separated exact exempt paths (after normalization). |

## Per-endpoint Overrides

`RateLimiterService._resolve_policy()` maps endpoint prefixes to specialized policies:

- `"{API_PREFIX}/prediction"` → prediction policy (`RATE_LIMIT_PREDICTION_*`)
- `"{API_PREFIX}/historic-data"` → historical policy (`RATE_LIMIT_HISTORICAL_*`)
- any other path → default policy (`RATE_LIMIT_DEFAULT_*`)

If you add a new endpoint group, add new `RATE_LIMIT_*` variables in `Settings` and map them in `_resolve_policy()`.

## Recommended Starter Profiles

### Balanced Starter

```env
# Global/default
RATE_LIMIT_DEFAULT_CAPACITY=60
RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND=1.0

# Stricter prediction policy
RATE_LIMIT_PREDICTION_CAPACITY=8
RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND=0.1

# Looser historical policy
RATE_LIMIT_HISTORICAL_CAPACITY=180
RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND=3.0

# Storage guardrails
RATE_LIMIT_STORAGE_MAX_ENTRIES=100000
RATE_LIMIT_STORAGE_TTL_SECONDS=3600

# Proxy and exemptions
RATE_LIMIT_TRUSTED_PROXY_IPS=10.0.0.1,10.0.0.2
RATE_LIMIT_EXEMPT_PATHS=/health,/docs,/redoc,/openapi.json
```

## Validation Commands

Run targeted middleware tests after any config or policy change:

```bash
pytest tests/middleware/rate_limit/test_middleware.py -x
```

Start the app locally and exercise prediction/historical routes:

```bash
uvicorn app.main:app --reload
```
