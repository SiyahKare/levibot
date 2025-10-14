"""
Walk-Forward Backtest Engine

Realistic backtesting with no look-ahead bias.
"""
from __future__ import annotations

import numpy as np
import polars as pl


def simulate_trades(
    df: pl.DataFrame,
    predictions: list[float],
    entry_threshold: float = 0.55,
    exit_threshold: float = 0.48,
    fee_bps: float = 2.0,
) -> dict:
    """
    Simulate trading with predictions.
    
    Args:
        df: DataFrame with OHLCV and returns
        predictions: Model predictions (p_up)
        entry_threshold: Enter position if p_up > threshold
        exit_threshold: Exit position if p_up < threshold
        fee_bps: Trading fee in basis points
    
    Returns:
        Performance metrics
    """
    position = 0  # 0 = flat, 1 = long
    equity = [1.0]
    trades = []
    
    for i in range(1, len(df) - 1):
        pred = predictions[i]
        
        # Entry/Exit logic
        if position == 0 and pred > entry_threshold:
            position = 1
        elif position == 1 and pred < exit_threshold:
            position = 0
        
        # Calculate return for next bar
        next_return = df["ret_1"][i + 1] if "ret_1" in df.columns else 0.0
        
        # Apply fee if position changed
        fee = fee_bps / 10000.0 if predictions[i] != predictions[i - 1] else 0.0
        
        # Calculate equity
        bar_return = (next_return if position == 1 else 0.0) - fee
        equity.append(equity[-1] * (1.0 + bar_return))
    
    # Calculate metrics
    equity_arr = np.array(equity)
    returns = np.diff(np.log(equity_arr + 1e-9))
    
    # Annualized metrics (assuming 15m bars)
    periods_per_year = 365 * 24 * 4  # 15m = 4 per hour
    
    cagr = float(equity_arr[-1] ** (periods_per_year / len(equity_arr)) - 1)
    sharpe = float((returns.mean() / (returns.std() + 1e-9)) * np.sqrt(periods_per_year))
    
    # Max drawdown
    cummax = np.maximum.accumulate(equity_arr)
    drawdown = 1 - (equity_arr / cummax)
    max_dd = float(drawdown.max())
    
    return {
        "final_equity": float(equity_arr[-1]),
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "total_bars": len(equity),
    }


def walk_forward_backtest(
    df: pl.DataFrame,
    model,
    feature_cols: list[str],
    entry_threshold: float = 0.55,
    exit_threshold: float = 0.48,
    fee_bps: float = 2.0,
) -> dict:
    """
    Run walk-forward backtest.
    
    Args:
        df: Features DataFrame
        model: Trained model with predict() method
        feature_cols: List of feature column names
        entry_threshold: Entry threshold
        exit_threshold: Exit threshold
        fee_bps: Trading fee in basis points
    
    Returns:
        Performance metrics
    """
    print(f"🔄 Running walk-forward backtest on {len(df)} bars...")
    
    # Get predictions
    X = df.select(feature_cols).to_pandas()
    predictions = model.predict(X).tolist()
    
    # Simulate
    metrics = simulate_trades(
        df,
        predictions,
        entry_threshold=entry_threshold,
        exit_threshold=exit_threshold,
        fee_bps=fee_bps,
    )
    
    print("✅ Backtest complete!")
    print(f"  Final Equity: {metrics['final_equity']:.4f}")
    print(f"  CAGR: {metrics['cagr']:.2%}")
    print(f"  Sharpe: {metrics['sharpe']:.2f}")
    print(f"  Max DD: {metrics['max_dd']:.2%}")
    
    return metrics

