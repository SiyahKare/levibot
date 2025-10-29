"""Fitness function for genetic algorithm optimization."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from .genes import Chromosome
from .label import triple_barrier

logger = logging.getLogger(__name__)


def regime_ok(ema_fast: float, ema_slow: float) -> bool:
    """Check if regime filter allows trading (uptrend)."""
    return (ema_fast / (ema_slow + 1e-9) - 1.0) > 0


def build_X(df: pd.DataFrame, chrom: Chromosome) -> pd.DataFrame:
    """
    Build feature matrix from OHLCV data.

    Args:
        df: OHLCV DataFrame
        chrom: Chromosome with parameters

    Returns:
        Feature DataFrame
    """
    f = pd.DataFrame(index=df.index)
    close = df["close"].astype(float)
    ret = np.log(close).diff().fillna(0)

    # Basic returns
    f["ret_1"] = ret
    f["ret_5"] = ret.rolling(5).sum()
    f["ret_10"] = ret.rolling(10).sum()

    # Moving averages
    f["ema_fast"] = close.ewm(span=chrom.ema_fast, adjust=False).mean()
    f["ema_slow"] = close.ewm(span=chrom.ema_slow, adjust=False).mean()
    f["sma_20"] = close.rolling(20).mean()
    f["sma_50"] = close.rolling(50).mean()

    # RSI calculation
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / chrom.rsi_len, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / chrom.rsi_len, adjust=False).mean()
    rs = up / (dn + 1e-12)
    f["rsi"] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    bb_period = 20
    bb_std = close.rolling(bb_period).std()
    f["bb_upper"] = close.rolling(bb_period).mean() + 2 * bb_std
    f["bb_lower"] = close.rolling(bb_period).mean() - 2 * bb_std
    f["bb_width"] = (f["bb_upper"] - f["bb_lower"]) / close.rolling(bb_period).mean()
    f["bb_position"] = (close - f["bb_lower"]) / (f["bb_upper"] - f["bb_lower"] + 1e-12)

    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    f["macd"] = ema_12 - ema_26
    f["macd_signal"] = f["macd"].ewm(span=9, adjust=False).mean()
    f["macd_histogram"] = f["macd"] - f["macd_signal"]

    # Volume features
    if "volume" in df.columns:
        f["volume_sma"] = df["volume"].rolling(20).mean()
        f["volume_ratio"] = df["volume"] / (f["volume_sma"] + 1e-12)
    else:
        f["volume_ratio"] = 1.0

    # Volatility
    f["volatility"] = ret.rolling(20).std()
    f["volatility_ratio"] = f["volatility"] / f["volatility"].rolling(50).mean()

    # Price position
    f["price_position"] = (close - close.rolling(50).min()) / (
        close.rolling(50).max() - close.rolling(50).min() + 1e-12
    )

    return f.replace([np.inf, -np.inf], 0).fillna(0)


def train_and_score(
    train_df: pd.DataFrame, valid_df: pd.DataFrame, chrom: Chromosome
) -> tuple[float, dict[str, Any]]:
    """
    Train model and score on validation set.

    Args:
        train_df: Training OHLCV data
        valid_df: Validation OHLCV data
        chrom: Chromosome with parameters

    Returns:
        Tuple of (fitness_score, metrics_dict)
    """
    try:
        # Generate labels
        y_train = triple_barrier(
            train_df["close"], chrom.tb_u_bps, chrom.tb_d_bps, chrom.tb_t_bars
        )
        y_valid = triple_barrier(
            valid_df["close"], chrom.tb_u_bps, chrom.tb_d_bps, chrom.tb_t_bars
        )

        # Build features
        X_train = build_X(train_df, chrom)
        X_valid = build_X(valid_df, chrom)

        # Align indices
        common_idx = X_train.index.intersection(y_train.index)
        X_train = X_train.loc[common_idx]
        y_train = y_train.loc[common_idx]

        common_idx = X_valid.index.intersection(y_valid.index)
        X_valid = X_valid.loc[common_idx]
        y_valid = y_valid.loc[common_idx]

        if len(X_train) < 100 or len(X_valid) < 50:
            logger.warning("Insufficient data for training/validation")
            return -10.0, {"error": "insufficient_data"}

        # Train model
        if chrom.model_type == 0:
            model = LogisticRegression(
                max_iter=400, C=chrom.lr_C, n_jobs=1, random_state=42
            )
        else:
            model = RandomForestClassifier(
                n_estimators=chrom.rf_n_estimators,
                max_depth=chrom.rf_max_depth,
                n_jobs=1,
                random_state=42,
            )

        model.fit(X_train, y_train)

        # Get predictions
        y_pred = model.predict(X_valid)
        y_proba = (
            model.predict_proba(X_valid) if hasattr(model, "predict_proba") else None
        )

        # Apply rule-based overlay
        signals = []
        for i in range(len(X_valid)):
            # Regime filter
            if chrom.regime_filter:
                if not regime_ok(
                    X_valid["ema_fast"].iloc[i], X_valid["ema_slow"].iloc[i]
                ):
                    signals.append(0)
                    continue

            # RSI rules
            rsi = X_valid["rsi"].iloc[i]
            if rsi < chrom.rsi_buy:
                signals.append(1)
            elif rsi > chrom.rsi_sell:
                signals.append(-1)
            else:
                signals.append(int(np.sign(y_pred[i])))

        signals = np.array(signals)

        # Calculate backtest metrics
        metrics = calculate_backtest_metrics(valid_df, signals, chrom, X_valid)

        # Calculate fitness
        fitness = calculate_fitness(metrics)

        return fitness, metrics

    except Exception as e:
        logger.error(f"Error in train_and_score: {e}")
        return -10.0, {"error": str(e)}


def calculate_backtest_metrics(
    df: pd.DataFrame, signals: np.ndarray, chrom: Chromosome, features: pd.DataFrame
) -> dict[str, Any]:
    """Calculate backtest metrics from signals."""
    try:
        # Simple backtest simulation
        close = df["close"].values
        returns = np.diff(np.log(close))

        # Align signals with returns
        if len(signals) > len(returns):
            signals = signals[: len(returns)]
        elif len(signals) < len(returns):
            signals = np.pad(signals, (0, len(returns) - len(signals)), "constant")

        # Calculate strategy returns
        strategy_returns = signals[:-1] * returns  # Exclude last signal

        # Basic metrics
        total_return = np.sum(strategy_returns)
        sharpe = (
            np.mean(strategy_returns)
            / (np.std(strategy_returns) + 1e-12)
            * np.sqrt(252)
        )

        # Drawdown
        cumulative = np.cumprod(1 + strategy_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Volatility
        ann_vol = np.std(strategy_returns) * np.sqrt(252)

        # Hit rate
        hit_rate = np.mean(strategy_returns > 0) if len(strategy_returns) > 0 else 0

        # Turnover (simplified)
        turnover = np.mean(np.abs(np.diff(signals))) if len(signals) > 1 else 0

        # Costs (simplified)
        costs = turnover * 0.0005  # 5 bps per trade

        return {
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "ann_vol": ann_vol,
            "hit_rate": hit_rate,
            "turnover": turnover,
            "costs": costs,
            "num_trades": np.sum(np.abs(np.diff(signals))),
            "avg_trade_return": (
                np.mean(strategy_returns[strategy_returns != 0])
                if np.any(strategy_returns != 0)
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Error calculating backtest metrics: {e}")
        return {
            "total_return": -1.0,
            "sharpe": -1.0,
            "max_drawdown": -1.0,
            "ann_vol": 1.0,
            "hit_rate": 0.0,
            "turnover": 1.0,
            "costs": 1.0,
            "num_trades": 0,
            "avg_trade_return": 0.0,
        }


def calculate_fitness(metrics: dict[str, Any]) -> float:
    """Calculate fitness score from metrics."""
    try:
        sharpe = metrics.get("sharpe", -1.0)
        max_dd = abs(metrics.get("max_drawdown", 1.0))
        turnover = metrics.get("turnover", 1.0)
        costs = metrics.get("costs", 1.0)
        ann_vol = metrics.get("ann_vol", 1.0)

        # Base fitness
        fitness = sharpe - 0.5 * max_dd - 5e-5 * turnover - costs

        # Penalty for constraint violations
        if max_dd > 0.25:
            fitness -= 10.0
        if ann_vol > 0.35:
            fitness -= 10.0
        if sharpe < 0:
            fitness -= 5.0

        return fitness

    except Exception as e:
        logger.error(f"Error calculating fitness: {e}")
        return -10.0
