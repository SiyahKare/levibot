"""
Feature Engineer

Calculate technical indicators and create ML features.
"""
from __future__ import annotations

import polars as pl


class FeatureEngineer:
    """
    Feature engineering for time-series data.
    
    Features:
    - Price/volume features
    - Technical indicators (RSI, EMA, BB, ATR)
    - Returns and volatility
    - Labels for supervised learning
    """
    
    @staticmethod
    def calculate_returns(df: pl.DataFrame, periods: list[int] = [1, 3, 6, 12]) -> pl.DataFrame:
        """Calculate log returns for multiple periods."""
        for period in periods:
            df = df.with_columns(
                (pl.col("close").log() - pl.col("close").log().shift(period)).alias(f"ret_{period}")
            )
        return df
    
    @staticmethod
    def calculate_rsi(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
        """Calculate RSI indicator."""
        delta = pl.col("close") - pl.col("close").shift(1)
        
        gain = delta.clip(lower_bound=0)
        loss = (-delta).clip(lower_bound=0)
        
        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df = df.with_columns(rsi.alias(f"rsi_{period}"))
        return df
    
    @staticmethod
    def calculate_ema(df: pl.DataFrame, periods: list[int] = [21, 55, 200]) -> pl.DataFrame:
        """Calculate EMA indicators."""
        for period in periods:
            df = df.with_columns(
                pl.col("close").ewm_mean(span=period).alias(f"ema_{period}")
            )
        return df
    
    @staticmethod
    def calculate_bollinger_bands(df: pl.DataFrame, period: int = 20, std: float = 2.0) -> pl.DataFrame:
        """Calculate Bollinger Bands."""
        sma = pl.col("close").rolling_mean(window_size=period)
        rolling_std = pl.col("close").rolling_std(window_size=period)
        
        bb_upper = sma + (std * rolling_std)
        bb_lower = sma - (std * rolling_std)
        bb_pct = (pl.col("close") - bb_lower) / (bb_upper - bb_lower)
        
        df = df.with_columns([
            bb_upper.alias("bb_upper"),
            bb_lower.alias("bb_lower"),
            bb_pct.alias("bb_pct"),
        ])
        return df
    
    @staticmethod
    def calculate_atr(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
        """Calculate Average True Range."""
        high_low = pl.col("high") - pl.col("low")
        high_close = (pl.col("high") - pl.col("close").shift(1)).abs()
        low_close = (pl.col("low") - pl.col("close").shift(1)).abs()
        
        true_range = pl.max_horizontal([high_low, high_close, low_close])
        atr = true_range.rolling_mean(window_size=period)
        
        df = df.with_columns(atr.alias(f"atr_{period}"))
        return df
    
    @staticmethod
    def calculate_volatility(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
        """Calculate realized volatility."""
        returns = pl.col("close").log() - pl.col("close").log().shift(1)
        vol = returns.rolling_std(window_size=period)
        
        df = df.with_columns(vol.alias(f"realized_vol_{period}"))
        return df
    
    @staticmethod
    def calculate_z_score(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
        """Calculate z-score (price standardization)."""
        mean = pl.col("close").rolling_mean(window_size=period)
        std = pl.col("close").rolling_std(window_size=period)
        z_score = (pl.col("close") - mean) / std
        
        df = df.with_columns(z_score.alias(f"z_score_{period}"))
        return df
    
    @staticmethod
    def create_labels(df: pl.DataFrame, forward_periods: int = 3) -> pl.DataFrame:
        """
        Create training labels.
        
        Args:
            df: DataFrame with price data
            forward_periods: Number of periods ahead to predict
        
        Returns:
            DataFrame with labels:
            - label_return_N: future return
            - label_direction: -1 (down), 0 (flat), 1 (up)
        """
        # Future return
        future_return = (
            pl.col("close").shift(-forward_periods).log() - pl.col("close").log()
        )
        
        df = df.with_columns(future_return.alias(f"label_return_{forward_periods}"))
        
        # Direction labels (-1, 0, 1)
        # Thresholds: ±0.5% for 15m, adjust based on timeframe
        threshold = 0.005
        
        label_direction = (
            pl.when(future_return > threshold).then(1)
            .when(future_return < -threshold).then(-1)
            .otherwise(0)
        )
        
        df = df.with_columns(label_direction.alias("label_direction"))
        
        return df
    
    @staticmethod
    def add_regime_features(df: pl.DataFrame) -> pl.DataFrame:
        """
        Add regime classification features.
        
        Regimes:
        - Volatility: low/med/high
        - Trend: uptrend/downtrend/sideways
        """
        # Volatility regime (based on realized vol percentiles)
        vol_col = "realized_vol_20"
        if vol_col in df.columns:
            vol_quantiles = df.select(pl.col(vol_col).quantile([0.33, 0.67])).to_numpy().flatten()
            
            regime_vol = (
                pl.when(pl.col(vol_col) <= vol_quantiles[0]).then(pl.lit("low"))
                .when(pl.col(vol_col) <= vol_quantiles[1]).then(pl.lit("med"))
                .otherwise(pl.lit("high"))
            )
            
            df = df.with_columns(regime_vol.alias("regime_vol"))
        
        # Trend regime (based on EMA crossovers)
        if "ema_21" in df.columns and "ema_55" in df.columns:
            regime_trend = (
                pl.when(pl.col("ema_21") > pl.col("ema_55")).then(pl.lit("uptrend"))
                .when(pl.col("ema_21") < pl.col("ema_55")).then(pl.lit("downtrend"))
                .otherwise(pl.lit("sideways"))
            )
            
            df = df.with_columns(regime_trend.alias("regime_trend"))
        
        return df
    
    @classmethod
    def engineer_features(cls, df: pl.DataFrame, include_labels: bool = True) -> pl.DataFrame:
        """
        Complete feature engineering pipeline.
        
        Args:
            df: Raw OHLCV data
            include_labels: Whether to create labels (for training)
        
        Returns:
            DataFrame with all features
        """
        print(f"🔧 Engineering features for {len(df)} rows...")
        
        # Returns
        df = cls.calculate_returns(df, periods=[1, 3, 6, 12])
        
        # Technical indicators
        df = cls.calculate_rsi(df, period=14)
        df = cls.calculate_ema(df, periods=[21, 55, 200])
        df = cls.calculate_bollinger_bands(df, period=20)
        df = cls.calculate_atr(df, period=14)
        
        # Volatility
        df = cls.calculate_volatility(df, period=20)
        df = cls.calculate_z_score(df, period=20)
        
        # Regime features
        df = cls.add_regime_features(df)
        
        # Labels (for training)
        if include_labels:
            df = cls.create_labels(df, forward_periods=3)
        
        # Drop rows with NaN (from rolling calculations)
        df = df.drop_nulls()
        
        print(f"✅ Engineered {len(df)} rows with {len(df.columns)} features")
        
        return df
    
    @staticmethod
    def get_feature_columns() -> list[str]:
        """Get list of feature columns (excluding OHLCV, labels, metadata)."""
        return [
            # Returns
            "ret_1", "ret_3", "ret_6", "ret_12",
            # Technical
            "rsi_14", "ema_21", "ema_55", "ema_200",
            "bb_upper", "bb_lower", "bb_pct", "atr_14",
            # Volatility
            "realized_vol_20", "z_score_20",
        ]
    
    @staticmethod
    def prepare_for_ml(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
        """
        Prepare features for ML training.
        
        Args:
            df: Engineered features DataFrame
        
        Returns:
            (X_features, y_labels) tuple
        """
        feature_cols = FeatureEngineer.get_feature_columns()
        
        # Add regime as one-hot encoded features
        if "regime_vol" in df.columns:
            df = df.with_columns([
                (pl.col("regime_vol") == "low").cast(pl.Int64).alias("regime_vol_low"),
                (pl.col("regime_vol") == "med").cast(pl.Int64).alias("regime_vol_med"),
                (pl.col("regime_vol") == "high").cast(pl.Int64).alias("regime_vol_high"),
            ])
            feature_cols.extend(["regime_vol_low", "regime_vol_med", "regime_vol_high"])
        
        if "regime_trend" in df.columns:
            df = df.with_columns([
                (pl.col("regime_trend") == "uptrend").cast(pl.Int64).alias("regime_trend_up"),
                (pl.col("regime_trend") == "downtrend").cast(pl.Int64).alias("regime_trend_down"),
                (pl.col("regime_trend") == "sideways").cast(pl.Int64).alias("regime_trend_side"),
            ])
            feature_cols.extend(["regime_trend_up", "regime_trend_down", "regime_trend_side"])
        
        X = df.select(feature_cols)
        y = df.select(["label_direction"]) if "label_direction" in df.columns else None
        
        return X, y

