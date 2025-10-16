"""
Strategy signal-to-position logic.

Converts ensemble ML predictions to position sizing with risk management.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ensemble_to_position(
    prob_up: np.ndarray,
    confidence: np.ndarray | None = None,
    risk_cap: float = 0.2,
    kelly_fraction: float = 0.25,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert ensemble predictions to signals and position sizes.

    Args:
        prob_up: Probability of upward movement (0.0 - 1.0)
        confidence: Optional confidence scores (0.0 - 1.0)
        risk_cap: Maximum position size (fraction of capital)
        kelly_fraction: Kelly criterion fraction (conservative: 0.25)

    Returns:
        (signals, sizes) tuple
        - signals: 1 = long, 0 = flat
        - sizes: Position size (0.0 - risk_cap)
    """
    n = len(prob_up)

    # Default confidence if not provided
    if confidence is None:
        confidence = np.abs(prob_up - 0.5) * 2  # Scale to 0-1

    # Signals: long if prob_up > 0.5
    signals = (prob_up > 0.5).astype(int)

    # Position sizing: Kelly fraction * confidence, capped
    kelly_size = kelly_fraction * confidence
    sizes = np.clip(kelly_size, 0, risk_cap)

    # Zero size if no signal
    sizes = sizes * signals

    return signals, sizes


def apply_stop_loss(
    equity_curve: np.ndarray,
    positions: np.ndarray,
    stop_loss_pct: float = 0.05,
) -> np.ndarray:
    """
    Apply stop-loss: flatten position if drawdown exceeds threshold.

    Args:
        equity_curve: Equity curve array
        positions: Position array
        stop_loss_pct: Stop-loss threshold (e.g., 0.05 = 5%)

    Returns:
        Modified positions with stop-loss applied
    """
    if len(equity_curve) == 0:
        return positions

    positions_modified = positions.copy()
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max

    # Flatten position when drawdown exceeds threshold
    stop_triggered = drawdown < -stop_loss_pct

    positions_modified[stop_triggered] = 0

    return positions_modified


def apply_take_profit(
    equity_curve: np.ndarray,
    positions: np.ndarray,
    take_profit_pct: float = 0.10,
) -> np.ndarray:
    """
    Apply take-profit: flatten position if gain exceeds threshold.

    Args:
        equity_curve: Equity curve array
        positions: Position array
        take_profit_pct: Take-profit threshold (e.g., 0.10 = 10%)

    Returns:
        Modified positions with take-profit applied
    """
    if len(equity_curve) == 0:
        return positions

    positions_modified = positions.copy()
    initial_equity = equity_curve[0]
    gain = (equity_curve - initial_equity) / initial_equity

    # Flatten position when gain exceeds threshold
    take_profit_triggered = gain > take_profit_pct

    positions_modified[take_profit_triggered] = 0

    return positions_modified


def fib_rsi_reversion_strategy(bars: pd.DataFrame, rsi: pd.Series) -> pd.Series:
    """
    Fibonacci Retracement + RSI Mean Reversion Strategy.
    
    Rules:
    - Long bias: Price < 61.8% level AND RSI < 30 (oversold)
    - Short bias: Price > 38.2% level AND RSI > 70 (overbought)
    - Mean revert: Price between 38.2-61.8% → small position toward mid-zone
    
    Args:
        bars: OHLCV DataFrame with columns ['high', 'low', 'close']
        rsi: RSI series (0-100)
        
    Returns:
        Position series (-1.0 to +1.0)
        - +1.0: Full long
        - -1.0: Full short
        - 0.0: Flat
        - 0.3/-0.3: Mean reversion position
    """
    # Calculate Fibonacci levels (2-day window @ 1m = 2880 bars)
    hi = bars['high'].rolling(2880, min_periods=2880).max()
    lo = bars['low'].rolling(2880, min_periods=2880).min()
    
    lvl_382 = hi - (hi - lo) * 0.382
    lvl_618 = hi - (hi - lo) * 0.618
    
    c = bars['close']
    
    # Position logic
    pos = np.where(
        (c < lvl_618) & (rsi < 30),  # Oversold below 61.8%
        +1.0,
        np.where(
            (c > lvl_382) & (rsi > 70),  # Overbought above 38.2%
            -1.0,
            np.where(
                (c <= lvl_382) & (c >= lvl_618),  # Mean reversion zone
                0.3 * np.sign(((lvl_382 + lvl_618) / 2) - c),
                0.0
            )
        )
    )
    
    return pd.Series(pos, index=bars.index).fillna(0.0)

