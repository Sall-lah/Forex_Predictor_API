"""Minimal placeholder web server for the Forex Predictor monorepo.

This server intentionally uses only the Python standard library and serves
the local ``index.html`` file from the ``web/`` directory.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"


def run_startup_check() -> int:
    """Validate placeholder startup requirements without binding a port."""
    if not INDEX_PATH.exists():
        print(f"Startup check failed: missing {INDEX_PATH.name}")
        return 1

    try:
        INDEX_PATH.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Startup check failed: cannot read {INDEX_PATH.name} ({error})")
        return 1

    print("Startup check passed: web placeholder is ready.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create CLI parser for placeholder server commands."""
    parser = argparse.ArgumentParser(
        description="Run the Forex Predictor web placeholder."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (default: 8000).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate startup prerequisites and exit.",
    )
    return parser


def main() -> int:
    """Run startup check or start the placeholder web server."""
    args = build_parser().parse_args()

    if args.check:
        return run_startup_check()

    handler = partial(SimpleHTTPRequestHandler, directory=str(BASE_DIR))
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"Serving Forex Predictor Web placeholder on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down placeholder server.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
