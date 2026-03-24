"""
Global pytest fixtures shared across all test modules.

Why conftest.py at root: Pytest auto-discovers it for every test in
the tree, making TestClient and sample data fixtures available without
explicit imports.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    FastAPI TestClient fixture, reused for the whole test module.

    Scope is 'module' to avoid spinning up the ASGI app on every test
    while still isolating module-level state.
    """
    return TestClient(app)
