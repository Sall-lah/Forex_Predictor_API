# Forex Predictor API

Backend API for Forex Predictor monorepo. Please see the [root README.md](../README.md) for full project setup.

## Configuration

Configuration is loaded from `api/.env` (see `.env.example` for available variables).

## Running

### Local Development

```bash
uvicorn api.app.main:app --app-dir .
```

Or from repository root:

```bash
uvicorn api.app.main:app --app-dir api/
```

### With Custom Port

```bash
uvicorn api.app.main:app --app-dir api/ --port 8001
```

## Environment

The API loads configuration from `api/.env`. Copy `.env.example` to `.env` and customize values.

## Testing

```bash
pytest api/tests/
```

---

*Last updated: 2026-04-12*