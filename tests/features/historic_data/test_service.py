"""
Unit tests for HistoricDataService.

Strategy:
- ``fetch_hourly_ohlcv``: The Kraken HTTP call is mocked via
  ``pytest-mock`` (mocker.patch on ``httpx.get``).  No live network
  traffic is made, keeping tests deterministic and fast.
- ``compute_indicators``: Exercises the full pandas/ta pipeline with
  a synthetically generated in-memory DataFrame.
"""

import pytest
import pandas as pd
import numpy as np

from app.core.exceptions import DataFetchError, InsufficientDataError
from app.features.historic_data.service import HistoricDataService


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_kraken_payload(n_rows: int = 50) -> dict:
    """
    Build a minimal Kraken-style OHLC JSON payload with *n_rows* candles.

    Why synthetic: Avoids hitting the real API and keeps the data shape
    exactly as Kraken documents (strings for prices, int for timestamp).
    """
    base_ts = 1_700_000_000  # arbitrary Unix timestamp
    candles = [
        [
            base_ts + i * 3600,    # timestamp (int)
            f"{84000 + i}.00",     # open  (str)
            f"{84100 + i}.00",     # high  (str)
            f"{83900 + i}.00",     # low   (str)
            f"{84050 + i}.00",     # close (str)
            f"{84025 + i}.00",     # vwap  (str)
            f"{10 + i}.5",         # volume (str)
            100,                   # count (int)
        ]
        for i in range(n_rows)
    ]
    return {"result": {"XXBTZUSD": candles, "last": base_ts + n_rows * 3600}, "error": []}


def _make_mock_response(payload: dict, status_code: int = 200):
    """Return a simple object mimicking an httpx.Response."""

    class _MockResponse:
        def __init__(self, data, code):
            self._data = data
            self.status_code = code

        def raise_for_status(self):
            # Only raise for genuine HTTP errors; 200 is fine.
            if self.status_code >= 400:
                import httpx
                raise httpx.HTTPStatusError(
                    "error", request=None, response=self  # type: ignore[arg-type]
                )

        def json(self):
            return self._data

    return _MockResponse(payload, status_code)


# ---------------------------------------------------------------------------
# HistoricDataService.fetch_hourly_ohlcv
# ---------------------------------------------------------------------------

class TestFetchHourlyOhlcv:
    """Tests for the Kraken-backed live data method."""

    def test_returns_enriched_response_on_success(self, mocker):
        """Happy path: mocked Kraken response produces enriched records."""
        payload = _build_kraken_payload(n_rows=60)
        mocker.patch("app.features.historic_data.service.httpx.get", return_value=_make_mock_response(payload))

        svc = HistoricDataService()
        result = svc.fetch_hourly_ohlcv("XXBTZUSD")

        assert result.symbol == "XXBTZUSD"
        assert result.total_records == 60
        # First records lack enough lookback for SMA/RSI — they are None.
        assert result.data[0].sma is None
        # Last record should have all indicators populated.
        last = result.data[-1]
        assert last.macd is not None
        assert last.macd_signal is not None

    def test_raises_data_fetch_error_on_network_failure(self, mocker):
        """Network-level exception must be wrapped in DataFetchError."""
        import httpx

        mocker.patch("app.features.historic_data.service.httpx.get", side_effect=httpx.ConnectError("timeout"))

        svc = HistoricDataService()
        with pytest.raises(DataFetchError, match="Network error"):
            svc.fetch_hourly_ohlcv("XXBTZUSD")

    def test_raises_data_fetch_error_on_kraken_api_error(self, mocker):
        """Kraken error body (non-empty ``error`` list) must raise DataFetchError."""
        payload = {"result": {}, "error": ["EQuery:Unknown asset pair"]}
        mocker.patch("app.features.historic_data.service.httpx.get", return_value=_make_mock_response(payload))

        svc = HistoricDataService()
        with pytest.raises(DataFetchError, match="Kraken API returned an error"):
            svc.fetch_hourly_ohlcv("BADPAIR")

    def test_raises_data_fetch_error_on_parse_failure(self, mocker):
        """
        Malformed response (result dict has no pair key) must raise DataFetchError.

        Why: An empty result dict causes StopIteration inside the generator
        expression.  The service catches this via the broad except clause
        that includes StopIteration.
        """
        bad_payload = {"error": [], "result": {}}  # no pair key → StopIteration
        mocker.patch("app.features.historic_data.service.httpx.get", return_value=_make_mock_response(bad_payload))

        svc = HistoricDataService()
        with pytest.raises(DataFetchError):
            svc.fetch_hourly_ohlcv("XXBTZUSD")

    def test_raises_insufficient_data_error_for_short_series(self, mocker):
        """
        A very short series (<26 rows) should raise InsufficientDataError
        because MACD requires 26 periods minimum.
        """
        payload = _build_kraken_payload(n_rows=10)
        mocker.patch("app.features.historic_data.service.httpx.get", return_value=_make_mock_response(payload))

        svc = HistoricDataService()
        with pytest.raises(InsufficientDataError):
            svc.fetch_hourly_ohlcv("XXBTZUSD")


# ---------------------------------------------------------------------------
# HistoricDataService._parse_kraken_response
# ---------------------------------------------------------------------------

class TestParseKrakenResponse:
    """Unit tests for the internal Kraken JSON → DataFrame parser."""

    def test_correct_columns_and_dtypes(self):
        payload = _build_kraken_payload(n_rows=5)
        df = HistoricDataService._parse_kraken_response(payload)

        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        assert df["close"].dtype == np.float64
        # Timestamp column must be timezone-aware UTC datetime.
        assert str(df["timestamp"].dtype) == "datetime64[ns, UTC]"

    def test_rows_sorted_by_timestamp(self):
        payload = _build_kraken_payload(n_rows=10)
        df = HistoricDataService._parse_kraken_response(payload)
        assert df["timestamp"].is_monotonic_increasing

    def test_last_sentinel_key_is_skipped(self):
        """The 'last' key in Kraken's result dict must not be used as pair key."""
        payload = _build_kraken_payload(n_rows=5)
        # Swap the order so 'last' appears first — parser must still find pair key.
        payload["result"] = dict(
            [("last", 9999999999)] + list(payload["result"].items())
        )
        df = HistoricDataService._parse_kraken_response(payload)
        assert len(df) == 5


# ---------------------------------------------------------------------------
# HistoricDataService.compute_indicators  (existing functionality, regression)
# ---------------------------------------------------------------------------

class TestComputeIndicators:
    """Regression tests ensuring the existing POST endpoint logic is intact."""

    def _make_request(self, n: int = 30):
        from datetime import datetime, timedelta, timezone
        from app.features.historic_data.schemas import HistoricDataRequest, OHLCVRecord

        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        records = [
            OHLCVRecord(
                timestamp=base + timedelta(hours=i),
                open=float(100 + i),
                high=float(101 + i),
                low=float(99 + i),
                close=float(100 + i),
                volume=float(1000 + i),
            )
            for i in range(n)
        ]
        return HistoricDataRequest(symbol="BTC/USD", records=records)

    def test_response_has_correct_record_count(self):
        svc = HistoricDataService()
        result = svc.compute_indicators(self._make_request(n=30))
        assert result.total_records == 30
        assert result.symbol == "BTC/USD"

    def test_indicator_fields_populated_at_end(self):
        svc = HistoricDataService()
        result = svc.compute_indicators(self._make_request(n=30))
        last = result.data[-1]
        assert last.sma is not None
        assert last.rsi is not None
        assert last.macd is not None

    def test_raises_insufficient_data_error(self):
        svc = HistoricDataService()
        with pytest.raises(InsufficientDataError):
            svc.compute_indicators(self._make_request(n=5))
