"""
Strategy signal-to-position logic.

Converts ensemble ML predictions to position sizing with risk management.
"""
from __future__ import annotations

import numpy as np


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

