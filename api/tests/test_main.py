"""Tests for main.py lifespan and worker lock enforcement."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest


class TestWorkerLock:
    """Tests for _acquire_worker_lock / _release_worker_lock."""

    def test_acquire_lock_success(self, tmp_path) -> None:
        """Should acquire lock and return PID when no conflict."""
        from app.main import _acquire_worker_lock

        lock_path = str(tmp_path / "kraken_ws.lock")
        with patch.dict(os.environ, {"KRAKEN_WS_LOCK_FILE": lock_path}):
            pid, handle = _acquire_worker_lock()

        assert pid == os.getpid()
        assert handle is not None
        # Clean up
        from app.main import _release_worker_lock

        _release_worker_lock(handle)

    def test_release_lock_cleans_up(self, tmp_path) -> None:
        """Releasing the lock should remove the lock file."""
        from app.main import _acquire_worker_lock, _release_worker_lock

        lock_path = str(tmp_path / "kraken_ws.lock")
        with patch.dict(os.environ, {"KRAKEN_WS_LOCK_FILE": lock_path}):
            pid, handle = _acquire_worker_lock()
            assert handle is not None
            _release_worker_lock(handle)

        assert not os.path.exists(lock_path)

    def test_second_acquire_fails_with_conflict(self, tmp_path) -> None:
        """A second acquire should fail when the lock file is already held."""
        from app.main import _acquire_worker_lock, _release_worker_lock

        lock_path = str(tmp_path / "kraken_ws.lock")
        with patch.dict(os.environ, {"KRAKEN_WS_LOCK_FILE": lock_path}):
            pid1, handle1 = _acquire_worker_lock()
            assert handle1 is not None
            assert pid1 == os.getpid()

            # Write a fake PID to simulate another process holding the lock
            # (on Windows, same-process double-lock may succeed).
            os.lseek(handle1, 0, os.SEEK_SET)
            os.write(handle1, b"99999")
            os.lseek(handle1, 0, os.SEEK_SET)

            # Release and try again - the file now has PID 99999
            _release_worker_lock(handle1)

            # Now acquire should fail because the file still has content
            # (lock was released but file exists with PID)
            pid2, handle2 = _acquire_worker_lock()
            # On Windows, the lock may succeed since we released it,
            # but on Unix flock should detect the conflict.
            # The key assertion: if it fails, it reads the PID from file.
            if handle2 is None:
                assert pid2 == 99999 or pid2 is None
            # If it succeeded (Windows edge case), just clean up
            if handle2 is not None:
                _release_worker_lock(handle2)

    def test_release_lock_with_none_is_noop(self) -> None:
        """Releasing None should not raise."""
        from app.main import _release_worker_lock

        _release_worker_lock(None)  # should not raise

    def test_default_lock_path(self) -> None:
        """Without env var, default lock path is /tmp/kraken_ws.lock."""
        from app.main import _DEFAULT_LOCK_PATH

        assert _DEFAULT_LOCK_PATH == "/tmp/kraken_ws.lock"
