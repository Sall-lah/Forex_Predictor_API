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
  5. Return probabilities for movement classes
"""

import logging
import pickle
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    ModelNotLoadedError,
    InsufficientDataError,
)
from app.features.prediction.schemas import PredictionRequest, PredictionResponse
from app.shared.ohlcv import KrakenProvider, OHLCVDataFrame
from ta import momentum, trend, volatility

from app.core.config import get_settings

settings = get_settings()
from app.core.exceptions import (
    DataValidationError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.shared.ohlcv import OHLCVDataFrame
from app.features.prediction.schemas import PredictionRequest, PredictionResponse
from app.shared.ohlcv import OHLCVDataFrame, DataProvider, get_provider

logger = logging.getLogger(__name__)


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
                "Model artifact is unavailable. "
                f"Resolved model path: {model_path}. "
                "Please ensure the configured MODEL_DIR and MODEL_FILENAME point to "
                "a readable trained model artifact."
            )

        try:
            logger.info("Loading LightGBM model from %s", model_path)
            model = joblib.load(model_path)
            logger.info("LightGBM model loaded successfully")
            return model
        except (
            OSError,
            ValueError,
            EOFError,
            ImportError,
            AttributeError,
            KeyError,
            pickle.UnpicklingError,
        ) as error:
            raise ModelNotLoadedError(
                "Unable to deserialize model artifact. "
                f"Resolved model path: {model_path}. "
                f"Root cause: {error}"
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
    COLUMNS_TO_DROP = ["timestamp", "open", "high", "low", "close"]

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
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract all features from OHLCV data.

        Args:
            df: DataFrame with OHLCV columns (timestamp, open, high, low, close, volume)

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
        df["ema_9"] = trend.EMAIndicator(close=close, window=9).ema_indicator()
        df["ema_21"] = trend.EMAIndicator(close=close, window=21).ema_indicator()
        df["ema_50"] = trend.EMAIndicator(close=close, window=50).ema_indicator()

        # Average Directional Index
        df["adx"] = trend.ADXIndicator(high=high, low=low, close=close).adx()

        # Aroon Oscillator
        df["aroon_osc"] = trend.AroonIndicator(high, low).aroon_indicator()

        # Commodity Channel Index
        df["cci"] = trend.CCIIndicator(high=high, low=low, close=close).cci()

        # Vortex Indicator
        vortex = trend.VortexIndicator(high=high, low=low, close=close)
        df["vortex_indicator_pos"] = vortex.vortex_indicator_pos()
        df["vortex_indicator_neg"] = vortex.vortex_indicator_neg()

        # MACD
        macd = trend.MACD(close=close)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()

        # KAMA
        df["kama_indicator"] = momentum.KAMAIndicator(close=close).kama()

        # Awesome Oscillator
        df["awesome_oscillator"] = momentum.AwesomeOscillatorIndicator(
            high=high, low=low
        ).awesome_oscillator()

        return df

    def _compute_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum-based technical indicators."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # RSI with different periods
        df["rsi_42h"] = momentum.RSIIndicator(close=close, window=42).rsi()
        df["rsi_35h"] = momentum.RSIIndicator(close=close, window=35).rsi()
        df["rsi_28h"] = momentum.RSIIndicator(close=close, window=28).rsi()
        df["rsi_21h"] = momentum.RSIIndicator(close=close, window=21).rsi()
        df["rsi_14h"] = momentum.RSIIndicator(close=close, window=14).rsi()
        df["rsi_7h"] = momentum.RSIIndicator(close=close, window=7).rsi()

        # Rate of Change with different periods
        df["roc_3d"] = momentum.ROCIndicator(close=close, window=72).roc()
        df["roc_2d"] = momentum.ROCIndicator(close=close, window=48).roc()
        df["roc_24h"] = momentum.ROCIndicator(close=close, window=24).roc()
        df["roc_12h"] = momentum.ROCIndicator(close=close, window=12).roc()
        df["roc_4h"] = momentum.ROCIndicator(close=close, window=4).roc()
        df["roc_2h"] = momentum.ROCIndicator(close=close, window=2).roc()
        df["roc_1h"] = momentum.ROCIndicator(close=close, window=1).roc()

        # Williams %R
        df["william_r"] = momentum.WilliamsRIndicator(
            high=high, low=low, close=close
        ).williams_r()

        # Ultimate Oscillator
        df["ultimate_oscillator"] = momentum.UltimateOscillator(
            high=high, low=low, close=close
        ).ultimate_oscillator()

        # Stochastic Oscillator
        stoch = momentum.StochasticOscillator(high=high, low=low, close=close)
        df["stoch"] = stoch.stoch()
        df["stoch_signal"] = stoch.stoch_signal()

        # PPO
        ppo = momentum.PercentagePriceOscillator(close=close)
        df["ppo"] = ppo.ppo()
        df["ppo_signal"] = ppo.ppo_signal()

        # Stochastic RSI
        df["stoch_rsi"] = momentum.StochRSIIndicator(close=close).stochrsi()

        return df

    def _compute_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility-based technical indicators."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Average True Range
        df["atr"] = volatility.AverageTrueRange(
            high=high, low=low, close=close
        ).average_true_range()

        # Bollinger Bands
        bollinger = volatility.BollingerBands(close=close)
        df["boillinger_wband"] = bollinger.bollinger_wband()
        df["bollinger_pband"] = bollinger.bollinger_pband()

        # Donchian Channel
        donchian = volatility.DonchianChannel(high=high, low=low, close=close)
        df["donchian_channel_wband"] = donchian.donchian_channel_wband()
        df["donchian_channel_pband"] = donchian.donchian_channel_pband()

        # Keltner Channel
        keltner = volatility.KeltnerChannel(high=high, low=low, close=close)
        df["keltner_channel_hband"] = keltner.keltner_channel_hband()

        return df

    def _compute_custom_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute custom-defined features."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Weekly return (168 hours = 1 week)
        df["custom_weekly_return"] = close.pct_change(periods=168)

        # Multi-window returns
        df["custom_3d_return"] = close.pct_change(periods=72)
        df["custom_2d_return"] = close.pct_change(periods=48)
        df["custom_24h_return"] = close.pct_change(periods=24)

        # High-Low range percentage
        df["custom_hl_range_pct"] = (high - low) / close

        # Trend consistency (close > EMA50 over last 24 periods)
        df["custom_trend_consistency"] = (close > close.rolling(50).mean()).astype(
            int
        ).rolling(24).sum() / 24

        # Volatility calculations (rolling std of pct_change)
        df["custom_3d_volatility"] = close.pct_change().rolling(window=72).std()
        df["custom_2d_volatility"] = close.pct_change().rolling(window=48).std()
        df["custom_24h_volatility"] = close.pct_change().rolling(window=24).std()
        df["custom_12h_volatility"] = close.pct_change().rolling(window=12).std()
        df["custom_4h_volatility"] = close.pct_change().rolling(window=4).std()
        df["custom_2h_volatility"] = close.pct_change().rolling(window=2).std()

        # Close position within rolling high-low range
        df["custom_close_pos_3d"] = (close - low.rolling(72).min()) / (
            high.rolling(72).max() - low.rolling(72).min() + 1e-9
        )
        df["custom_close_pos_2d"] = (close - low.rolling(48).min()) / (
            high.rolling(48).max() - low.rolling(48).min() + 1e-9
        )
        df["custom_close_pos_24h"] = (close - low.rolling(24).min()) / (
            high.rolling(24).max() - low.rolling(24).min() + 1e-9
        )
        df["custom_close_pos_12h"] = (close - low.rolling(12).min()) / (
            high.rolling(12).max() - low.rolling(12).min() + 1e-9
        )
        df["custom_close_pos_4h"] = (close - low.rolling(6).min()) / (
            high.rolling(6).max() - low.rolling(6).min() + 1e-9
        )
        df["custom_close_pos_2h"] = (close - low.rolling(4).min()) / (
            high.rolling(4).max() - low.rolling(4).min() + 1e-9
        )

        # Volatility-adjusted returns
        df["custom_3d_vol_adj_return"] = close.pct_change() / (
            df["custom_3d_volatility"] + 1e-9
        )
        df["custom_2d_vol_adj_return"] = close.pct_change() / (
            df["custom_2d_volatility"] + 1e-9
        )
        df["custom_24h_vol_adj_return"] = close.pct_change() / (
            df["custom_24h_volatility"] + 1e-9
        )
        df["custom_12h_vol_adj_return"] = close.pct_change() / (
            df["custom_12h_volatility"] + 1e-9
        )
        df["custom_4h_vol_adj_return"] = close.pct_change() / (
            df["custom_4h_volatility"] + 1e-9
        )
        df["custom_2h_vol_adj_return"] = close.pct_change() / (
            df["custom_2h_volatility"] + 1e-9
        )

        return df


class PredictionService:
    """
    Business logic orchestrator for forex predictions.

    Coordinates:
    - Data fetching via Kraken API
    - Feature extraction and alignment
    - Machine learning inference
    - Prediction response formatting
    - Prediction caching
    """

    def __init__(
        self,
        api_client: KrakenProvider | None = None,
        model_loader: ModelLoader | None = None,
        preprocessor: OHLCVPreprocessor | None = None,
    ):
        self.api_client = api_client or KrakenProvider()
        self.model_loader = model_loader or ModelLoader()
        self.preprocessor = preprocessor or OHLCVPreprocessor()
        
        self._cache: dict[tuple[str, int], PredictionResponse] = {}
        self._cache_lock = threading.Lock()

    def _get_cache_key(self, normalized_pair: str) -> tuple[str, int]:
        now_utc = datetime.now(timezone.utc)
        hour_timestamp = int(now_utc.replace(minute=0, second=0, microsecond=0).timestamp())
        return (normalized_pair, hour_timestamp)

    def _get_valid_until(self) -> datetime:
        now_utc = datetime.now(timezone.utc)
        hour_start = now_utc.replace(minute=0, second=0, microsecond=0)
        return hour_start + timedelta(hours=1, minutes=2)

    def _get_cached(self, key: tuple[str, int]) -> PredictionResponse | None:
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached:
                if datetime.now(timezone.utc) < cached.valid_until:
                    return cached
                del self._cache[key]
            return None

    def _set_cached(self, key: tuple[str, int], response: PredictionResponse) -> None:
        with self._cache_lock:
            self._cache[key] = response

    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        from app.shared.ohlcv.pair_normalizer import normalize_pair
        normalized_pair = normalize_pair(request.pair)
        
        cache_key = self._get_cache_key(normalized_pair)
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        logger.info("Loading LightGBM model")
        model = self.model_loader.get_model()
        if not hasattr(model, "predict_proba"):
            raise ModelNotLoadedError("Model missing predict_proba method")

        historic_df = await self._fetch_historic_dataframe(normalized_pair)
        feature_df = self._extract_features(historic_df, normalized_pair)
        latest_features = self._select_latest_feature_row(feature_df)
        
        logger.info("Aligning features to model schema")
        required_features = self._resolve_model_feature_names(model)
        aligned_features = self._align_and_validate_features(
            latest_features, required_features
        )

        logger.info("Making prediction for '%s'", normalized_pair)
        probabilities = self._execute_inference(model, aligned_features)
        prob_straight, prob_up, prob_down = self._extract_probabilities(probabilities)

        response = PredictionResponse(
            pair=normalized_pair,
            probability_up=prob_up,
            probability_down=prob_down,
            probability_straight=prob_straight,
            computed_at=datetime.now(timezone.utc),
            valid_until=self._get_valid_until()
        )
        
        self._set_cached(cache_key, response)
        return response

    async def _fetch_historic_dataframe(self, normalized_pair: str) -> pd.DataFrame:
        logger.info("Fetching OHLCV data for '%s'", normalized_pair)
        payload = await self.api_client.fetch_ohlcv_data(
            normalized_pair, count=720, interval=60
        )
        ohlcv_data = OHLCVDataFrame.from_provider_response(payload)

        logger.info(
            "Fetched %d candles for '%s' (interval: 60m)",
            len(ohlcv_data.df),
            normalized_pair,
        )
        return ohlcv_data.df

    def _extract_features(self, df: pd.DataFrame, normalized_pair: str) -> pd.DataFrame:
        logger.info("Extracting features for '%s'", normalized_pair)
        features = self.preprocessor.extract_features(df)
        logger.info(
            "Feature extraction completed: %d rows, %d features",
            len(features),
            len(features.columns),
        )
        return features

    def _select_latest_feature_row(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise InsufficientDataError("No valid feature rows available after preprocessing")
        return df.iloc[[-1]]

    def _execute_inference(self, model: Any, aligned_features: pd.DataFrame) -> Any:
        try:
            return model.predict_proba(aligned_features)
        except Exception as error:
            raise RuntimeError(f"Model inference failed: {error}") from error

    @staticmethod
    def _resolve_model_feature_names(model: Any) -> list[str]:
        feature_names: Any | None = getattr(model, "feature_name_", None)

        if not isinstance(feature_names, (list, tuple, pd.Index, np.ndarray)):
            feature_names = None

        if feature_names is None:
            feature_name_method = getattr(model, "feature_name", None)
            if callable(feature_name_method):
                method_result = feature_name_method()
                if isinstance(method_result, (list, tuple, pd.Index, np.ndarray)):
                    feature_names = method_result

        if feature_names is None:
            raise DataValidationError(
                "Model metadata missing feature names required for alignment"
            )

        resolved_feature_names = [str(name) for name in feature_names if str(name)]
        if not resolved_feature_names:
            raise DataValidationError(
                "Model metadata returned empty feature names for alignment"
            )

        return resolved_feature_names

    @staticmethod
    def _align_and_validate_features(
        latest_features: pd.DataFrame, required_features: list[str]
    ) -> pd.DataFrame:
        missing_columns = [
            column
            for column in required_features
            if column not in latest_features.columns
        ]
        if missing_columns:
            raise DataValidationError(
                "Missing model-required feature columns: " + ", ".join(missing_columns)
            )

        aligned_features = latest_features.reindex(columns=required_features)

        try:
            feature_values = aligned_features.to_numpy(dtype=np.float64, copy=False)
        except (TypeError, ValueError) as error:
            raise DataValidationError(
                "Aligned model features must be numeric for inference"
            ) from error

        if not np.isfinite(feature_values).all():
            non_finite_mask = ~np.isfinite(aligned_features)
            bad_cols = aligned_features.columns[non_finite_mask.any(axis=0)].tolist()
            raise DataValidationError(
                f"Aligned model features contain non-finite values (NaN/Inf) in columns: {', '.join(bad_cols)}"
            )

        return aligned_features

    @staticmethod
    def _extract_probabilities(probabilities: Any) -> tuple[float, float, float]:
        try:
            class_zero_probability = probabilities[0][0]
            class_one_probability = probabilities[0][1]
            class_two_probability = probabilities[0][2]
        except (TypeError, IndexError, KeyError) as error:
            raise DataValidationError(
                "Invalid model output: expected predict_proba[[class_0, class_1, class_2]]"
            ) from error

        try:
            probability_straight = float(class_zero_probability)
            probability_up = float(class_one_probability)
            probability_down = float(class_two_probability)
        except (TypeError, ValueError) as error:
            raise DataValidationError(
                "Invalid model output: class probabilities must be numeric"
            ) from error

        for label, value in (
            ("class-0", probability_straight),
            ("class-1", probability_up),
            ("class-2", probability_down),
        ):
            if value < 0.0 or value > 1.0:
                raise DataValidationError(
                    f"Invalid model output: {label} probability out of range [0, 1]"
                )

        return probability_straight, probability_up, probability_down
