# Web Placeholder

This directory is a **placeholder app boundary** for the future frontend.
It is intentionally minimal and does not implement real frontend features yet.

## Run locally

From inside `web/`:

```bash
python server.py
```

Then open `http://127.0.0.1:8000` to view the landing page.

## Validate startup without opening a port

From inside `web/`:

```bash
python server.py --check
```

The command validates required placeholder files and exits with status code `0` on success.
