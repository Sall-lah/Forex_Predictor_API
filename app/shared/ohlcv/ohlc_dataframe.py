"""OHLCV DataFrame parsing, validation, and record conversion utilities.

This module isolates transformation and validation logic from transport code to
keep responsibilities clear and reusable across features.
"""

import pandas as pd

from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
)


class OHLCVDataFrame:
    """Encapsulates OHLCV parsing, validation, and record conversion."""

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, dataframe: pd.DataFrame) -> None:
        """Initialize wrapper with an OHLCV DataFrame."""
        self.df = dataframe

    @classmethod
    def from_kraken_response(cls, payload: dict) -> "OHLCVDataFrame":
        """Parse Kraken payload into normalized OHLCV DataFrame."""
        try:
            result = payload["result"]
            pair_key = next(key for key in result if key != "last")
            raw_candles = result[pair_key]
            last_completed_candle = result["last"]

            df = pd.DataFrame(
                raw_candles,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "vwap",
                    "volume",
                    "count",
                ],
            )

            if not df.empty and last_completed_candle != df.iloc[-1]["timestamp"]:
                df = df.iloc[:-1]

            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df = df.set_index("timestamp").sort_index().reset_index(drop=False)

            return cls(df)

        except (KeyError, ValueError, TypeError, StopIteration) as error:
            raise DataFetchError(f"Failed to parse Kraken response: {error}") from error

    def to_records(self) -> list[dict[str, object]]:
        """Convert DataFrame rows into JSON-safe dictionaries."""
        clean_df = self.df.where(pd.notnull(self.df), None)
        return clean_df.to_dict(orient="records")

    def validate_columns(self) -> None:
        """Validate that all required OHLCV columns are present."""
        missing = sorted(set(self.REQUIRED_COLUMNS) - set(self.df.columns))
        if missing:
            raise DataValidationError(f"Missing required columns: {', '.join(missing)}")

    def validate_row_count(self, min_rows: int) -> None:
        """Validate minimum DataFrame row count."""
        row_count = len(self.df)
        if row_count < min_rows:
            raise InsufficientDataError(
                f"Only {row_count} rows found, but {min_rows} required"
            )

    def validate(self, min_rows: int = 1) -> None:
        """Run required-column and minimum-row validations."""
        self.validate_columns()
        self.validate_row_count(min_rows)
