"""
Service layer for forex price prediction.

Architecture:
- ModelLoader: Singleton for loading and caching the LightGBM model
- OHLCVPreprocessor: Handles feature extraction from raw OHLCV data
- PredictionService: Orchestrates the complete prediction workflow
  1. Fetch OHLCV data from Kraken
  2. Preprocess and extract features
  3. Load ML model
  4. Make prediction
  5. Return probability of upward movement
"""

import logging
import threading
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import ta

from app.core.config import get_settings
from app.core.exceptions import (
    DataValidationError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.features.historic_data.service import KrakenAPIClient, OHLCVDataFrame
from app.features.prediction.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelLoader:
    """
    Thread-safe singleton for loading and caching the LightGBM prediction model.

    Responsibilities:
    - Load model from disk on first access
    - Cache the loaded model in memory
    - Validate model file exists
    - Thread-safe initialization

    Design pattern: Thread-safe singleton with lazy initialization
    """

    _instance: "ModelLoader | None" = None
    _lock: threading.Lock = threading.Lock()
    _model: Any | None = None

    def __new__(cls) -> "ModelLoader":
        """
        Create singleton instance with thread-safe double-checked locking.

        Returns:
            Singleton ModelLoader instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self) -> Any:
        """
        Get the cached LightGBM model, loading it if necessary.

        Returns:
            Loaded LightGBM model instance

        Raises:
            ModelNotLoadedError: If model file doesn't exist or loading fails
        """
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = self._load_model()
        return self._model

    @staticmethod
    def _load_model() -> Any:
        """
        Load the LightGBM model from disk.

        Returns:
            Loaded model instance

        Raises:
            ModelNotLoadedError: If model file doesn't exist or loading fails
        """
        model_path = settings.model_path
        if not model_path.exists():
            raise ModelNotLoadedError(
                f"Model file not found at {model_path}. "
                "Please ensure the model is trained and saved."
            )

        try:
            logger.info("Loading LightGBM model from %s", model_path)
            model = joblib.load(model_path)
            logger.info("LightGBM model loaded successfully")
            return model
        except Exception as error:
            raise ModelNotLoadedError(
                f"Failed to load model from {model_path}: {error}"
            ) from error

    def clear_cache(self) -> None:
        """
        Clear the cached model instance.

        Useful for testing or when the model file is updated.
        """
        with self._lock:
            self._model = None
        logger.info("Model cache cleared")


class OHLCVPreprocessor:
    """
    Preprocessor for OHLCV data to extract technical indicators and custom features.

    Responsibilities:
    - Validate input data structure
    - Compute technical indicators (trend, momentum, volatility)
    - Compute custom features (returns, volatility, position metrics)
    - Drop unnecessary columns
    - Return feature-ready DataFrame for ML model
    """

    # Required input columns
    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    # Columns to drop after feature extraction
    COLUMNS_TO_DROP = ["open", "high", "low", "close"]

    def validate_input(self, df: pd.DataFrame) -> None:
        """
        Validate that input DataFrame has required structure.

        Args:
            df: Input DataFrame with OHLCV data

        Raises:
            DataValidationError: If required columns are missing
            InsufficientDataError: If not enough rows for feature computation
        """
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise DataValidationError(
                f"Missing required columns: {', '.join(missing_cols)}"
            )

        # Check minimum row count
        if len(df) < settings.MIN_ROWS_FOR_FEATURES:
            raise InsufficientDataError(
                f"Need at least {settings.MIN_ROWS_FOR_FEATURES} rows for feature extraction, got {len(df)}"
            )

    def extract_features(
        self, df: pd.DataFrame, asset: Literal["BTCUSD", "ETHUSD"]
    ) -> pd.DataFrame:
        """
        Extract all features from OHLCV data.

        Args:
            df: DataFrame with OHLCV columns (timestamp, open, high, low, close, volume)
            asset: Asset name (BTCUSD or ETHUSD)

        Returns:
            DataFrame with extracted features, OHLC columns dropped

        Raises:
            DataValidationError: If input validation fails
            InsufficientDataError: If insufficient data for features
        """
        # Validate input
        self.validate_input(df)

        # Make a copy to avoid modifying original
        df_features = df.copy()

        # Add asset column
        df_features["asset"] = asset

        # Compute features
        df_features = self._compute_trend_indicators(df_features)
        df_features = self._compute_momentum_indicators(df_features)
        df_features = self._compute_volatility_indicators(df_features)
        df_features = self._compute_custom_features(df_features)

        # Drop original OHLC columns
        df_features = df_features.drop(columns=self.COLUMNS_TO_DROP)

        # Drop rows with NaN (from rolling calculations)
        initial_rows = len(df_features)
        df_features = df_features.dropna()
        final_rows = len(df_features)

        logger.info(
            "Feature extraction completed: %d -> %d rows after dropping NaN",
            initial_rows,
            final_rows,
        )

        if len(df_features) == 0:
            raise InsufficientDataError(
                "All rows contained NaN after feature computation"
            )

        return df_features

    def _compute_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trend-based technical indicators."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Exponential Moving Averages
        df["ema_9"] = ta.trend.EMAIndicator(close=close, window=9).ema_indicator()
        df["ema_21"] = ta.trend.EMAIndicator(close=close, window=21).ema_indicator()
        df["ema_50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()

        # Average Directional Index
        df["adx"] = ta.trend.ADXIndicator(
            high=high, low=low, close=close, window=14
        ).adx()

        # Aroon Oscillator
        df["aroon_osc"] = ta.trend.AroonIndicator(
            close=close, window=25
        ).aroon_indicator()

        # Commodity Channel Index
        df["cci"] = ta.trend.CCIIndicator(
            high=high, low=low, close=close, window=20
        ).cci()

        # Vortex Indicator
        vortex = ta.trend.VortexIndicator(high=high, low=low, close=close, window=14)
        df["vortex_indicator_pos"] = vortex.vortex_indicator_pos()
        df["vortex_indicator_neg"] = vortex.vortex_indicator_neg()

        # MACD
        macd = ta.trend.MACD(close=close)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()

        # KAMA
        df["kama_indicator"] = ta.momentum.KAMAIndicator(
            close=close, window=10, pow1=2, pow2=30
        ).kama()

        # Awesome Oscillator
        df["awesome_oscillator"] = ta.momentum.AwesomeOscillatorIndicator(
            high=high, low=low
        ).awesome_oscillator()

        return df

    def _compute_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum-based technical indicators."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # RSI with different periods
        df["rsi_21h"] = ta.momentum.RSIIndicator(close=close, window=21).rsi()
        df["rsi_14h"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        df["rsi_7h"] = ta.momentum.RSIIndicator(close=close, window=7).rsi()

        # Rate of Change with different periods
        df["roc_24h"] = ta.momentum.ROCIndicator(close=close, window=24).roc()
        df["roc_12h"] = ta.momentum.ROCIndicator(close=close, window=12).roc()
        df["roc_4h"] = ta.momentum.ROCIndicator(close=close, window=4).roc()
        df["roc_2h"] = ta.momentum.ROCIndicator(close=close, window=2).roc()
        df["roc_1h"] = ta.momentum.ROCIndicator(close=close, window=1).roc()

        # Williams %R
        df["william_r"] = ta.momentum.WilliamsRIndicator(
            high=high, low=low, close=close, lbp=14
        ).williams_r()

        # Ultimate Oscillator
        df["ultimate_oscillator"] = ta.momentum.UltimateOscillator(
            high=high, low=low, close=close
        ).ultimate_oscillator()

        # Stochastic Oscillator
        stoch = ta.momentum.StochasticOscillator(
            high=high, low=low, close=close, window=14, smooth_window=3
        )
        df["stoch"] = stoch.stoch()
        df["stoch_signal"] = stoch.stoch_signal()

        # PPO
        ppo = ta.momentum.PercentagePriceOscillator(close=close)
        df["ppo"] = ppo.ppo()
        df["ppo_signal"] = ppo.ppo_signal()

        # Stochastic RSI
        df["stoch_rsi"] = ta.momentum.StochRSIIndicator(
            close=close, window=14, smooth1=3, smooth2=3
        ).stochrsi()

        return df

    def _compute_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility-based technical indicators."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Average True Range
        df["atr"] = ta.volatility.AverageTrueRange(
            high=high, low=low, close=close, window=14
        ).average_true_range()

        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        df["bollinger_wband"] = bollinger.bollinger_wband()
        df["bollinger_pband"] = bollinger.bollinger_pband()

        # Donchian Channel
        donchian = ta.volatility.DonchianChannel(
            high=high, low=low, close=close, window=20
        )
        df["donchian_channel_wband"] = donchian.donchian_channel_wband()
        df["donchian_channel_pband"] = donchian.donchian_channel_pband()

        # Keltner Channel
        keltner = ta.volatility.KeltnerChannel(
            high=high, low=low, close=close, window=20
        )
        df["keltner_channel_hband"] = keltner.keltner_channel_hband()

        return df

    def _compute_custom_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute custom-defined features."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Weekly return (168 hours = 1 week)
        df["custom_weekly_return"] = close.pct_change(periods=168) * 100

        # High-Low range percentage
        df["custom_hl_range_pct"] = ((high - low) / close) * 100

        # Trend consistency (close > EMA50 over last 24 periods)
        ema_50 = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
        df["custom_trend_consistency"] = (close > ema_50).rolling(
            window=24
        ).mean() * 100

        # Volatility calculations (rolling std of pct_change)
        pct_change = close.pct_change()
        df["custom_24h_volatility"] = pct_change.rolling(window=24).std() * 100
        df["custom_12h_volatility"] = pct_change.rolling(window=12).std() * 100
        df["custom_4h_volatility"] = pct_change.rolling(window=4).std() * 100
        df["custom_2h_volatility"] = pct_change.rolling(window=2).std() * 100

        # Close position within rolling high-low range
        for window in [24, 12, 4, 2]:
            rolling_high = high.rolling(window=window).max()
            rolling_low = low.rolling(window=window).min()
            range_val = rolling_high - rolling_low
            # Avoid division by zero
            df[f"custom_close_pos_{window}h"] = np.where(
                range_val > 0, (close - rolling_low) / range_val, 0.5
            )

        # Volatility-adjusted returns
        for window in [24, 12, 4, 2]:
            ret = close.pct_change(periods=window) * 100
            vol = pct_change.rolling(window=window).std() * 100
            # Avoid division by zero
            df[f"custom_{window}h_vol_adj_return"] = np.where(vol > 0, ret / vol, 0)

        return df


class PredictionService:
    """
    Main service for making forex price predictions.

    Responsibilities:
    - Fetch historical OHLCV data via Kraken API
    - Preprocess data and extract features
    - Load and use ML model for prediction
    - Return prediction probability

    Workflow:
    1. Fetch 1 week of hourly OHLCV data from Kraken
    2. Extract 49 technical indicators and custom features
    3. Take the latest preprocessed row
    4. Use LightGBM model to predict price movement
    5. Return probability of upward movement (class 1)
    """

    def __init__(
        self,
        api_client: KrakenAPIClient | None = None,
        preprocessor: OHLCVPreprocessor | None = None,
        model_loader: ModelLoader | None = None,
    ):
        """
        Initialize service with optional dependencies.

        Args:
            api_client: Client for Kraken API (defaults to KrakenAPIClient)
            preprocessor: Data preprocessor (defaults to OHLCVPreprocessor)
            model_loader: Model loader instance (defaults to ModelLoader singleton)
        """
        self.api_client = api_client or KrakenAPIClient()
        self.preprocessor = preprocessor or OHLCVPreprocessor()
        self.model_loader = model_loader or ModelLoader()

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """
        Make price movement prediction for given trading pair.

        Args:
            request: PredictionRequest with pair and asset info

        Returns:
            PredictionResponse with probability of upward movement

        Raises:
            DataFetchError: If fetching data from Kraken fails
            InsufficientDataError: If insufficient data for feature extraction
            DataValidationError: If data validation fails
            ModelNotLoadedError: If ML model cannot be loaded
        """
        # Step 1: Fetch OHLCV data from Kraken
        logger.info("Fetching OHLCV data for '%s'", request.pair)
        payload = self.api_client.fetch_ohlcv_data(
            request.pair, settings.KRAKEN_DEFAULT_HOURS
        )

        # Step 2: Parse into DataFrame
        ohlcv_data = OHLCVDataFrame.from_kraken_response(payload)
        df = ohlcv_data.df

        logger.info("Fetched %d hourly candles for '%s'", len(df), request.pair)

        # Step 3: Extract features
        logger.info("Extracting features for '%s'", request.asset)
        df_features = self.preprocessor.extract_features(df, request.asset)

        logger.info(
            "Feature extraction completed: %d rows, %d features",
            len(df_features),
            len(df_features.columns),
        )

        # Step 4: Take the latest row for prediction
        latest_features = df_features.iloc[[-1]]  # Keep as DataFrame for model input

        # Step 5: Load model and make prediction
        logger.info("Loading LightGBM model")
        model = self.model_loader.get_model()

        # Step 6: Predict probabilities
        # predict_proba returns [[prob_class_0, prob_class_1]]
        logger.info("Making prediction for '%s'", request.pair)
        probabilities = model.predict_proba(latest_features)

        # Extract probability of class 1 (upward movement)
        prob_up = float(probabilities[0][1])

        logger.info(
            "Prediction completed for '%s': probability_up=%.4f",
            request.pair,
            prob_up,
        )

        return PredictionResponse(
            pair=request.pair,
            asset=request.asset,
            probability_up=prob_up,
        )
