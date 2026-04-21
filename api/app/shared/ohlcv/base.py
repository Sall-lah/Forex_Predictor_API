from typing import Protocol

class DataProvider(Protocol):
    """Protocol for all OHLCV data providers."""
    
    def fetch_ohlcv_data(self, pair: str, count: int, interval: int = 1) -> list[dict[str, object]]:
        ...