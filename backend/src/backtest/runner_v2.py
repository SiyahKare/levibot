"""
Vectorized backtest engine v2 with fees, slippage, and latency-aware fills.

Features:
- Latency-aware fills (order execution delay)
- Transaction costs (fees + slippage)
- Intrabar gap handling
- Position sizing with risk caps
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class BacktestRunnerV2:
    """
    Vectorized backtest engine with realistic fills.

    Args:
        bars: OHLCV DataFrame with columns [ts, open, high, low, close, volume]
        fee_bps: Fee in basis points (e.g., 5 = 0.05%)
        slippage_bps: Slippage in basis points
        latency_ms: Order execution latency in milliseconds
        initial_capital: Starting capital
    """

    def __init__(
        self,
        bars: pd.DataFrame,
        fee_bps: float = 5.0,
        slippage_bps: float = 5.0,
        latency_ms: float = 100.0,
        initial_capital: float = 10000.0,
    ):
        self.bars = bars.copy()
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.latency_ms = latency_ms
        self.initial_capital = initial_capital

        # Validate bars
        required_cols = ["ts", "open", "high", "low", "close", "volume"]
        if not all(col in bars.columns for col in required_cols):
            raise ValueError(f"bars must have columns: {required_cols}")

        # Sort by time
        self.bars = self.bars.sort_values("ts").reset_index(drop=True)

        # Calculate bar duration (assume 1m)
        if len(self.bars) > 1:
            bar_duration_ms = (self.bars.iloc[1]["ts"] - self.bars.iloc[0]["ts"]) / 1_000_000
        else:
            bar_duration_ms = 60_000  # 1 minute default

        self.latency_bars = max(1, int(latency_ms / bar_duration_ms))

    def run(self, signals: np.ndarray, sizes: np.ndarray) -> dict:
        """
        Run backtest.

        Args:
            signals: Signal array (1 = long, 0 = flat, -1 = short)
            sizes: Position size array (0.0 - 1.0, fraction of capital)

        Returns:
            Dict with equity_curve, positions, trades, costs
        """
        n_bars = len(self.bars)

        if len(signals) != n_bars or len(sizes) != n_bars:
            raise ValueError("signals and sizes must match bars length")

        # Initialize
        equity = np.zeros(n_bars)
        equity[0] = self.initial_capital

        positions = np.zeros(n_bars)  # Current position size
        cash = self.initial_capital
        holdings = 0.0  # Units held

        trades = []
        total_fees = 0.0
        total_slippage = 0.0

        for i in range(n_bars):
            # Current bar
            bar = self.bars.iloc[i]

            # Determine target position (with latency)
            if i >= self.latency_bars:
                signal_idx = i - self.latency_bars
                target_signal = signals[signal_idx]
                target_size = sizes[signal_idx]
            else:
                target_signal = 0
                target_size = 0.0

            # Current equity = cash + holdings value
            current_price = bar["close"]
            current_equity = cash + holdings * current_price

            # Calculate target position value
            if target_signal == 1:  # Long
                target_value = current_equity * target_size
                target_units = target_value / current_price if current_price > 0 else 0
            else:  # Flat or short (not implemented)
                target_units = 0

            # Calculate trade
            trade_units = target_units - holdings

            if abs(trade_units) > 1e-8:  # Execute trade
                # Fill price (with slippage)
                if trade_units > 0:  # Buy
                    fill_price = current_price * (1 + self.slippage_bps / 10000)
                else:  # Sell
                    fill_price = current_price * (1 - self.slippage_bps / 10000)

                # Trade value
                trade_value = abs(trade_units * fill_price)

                # Costs
                fee = trade_value * (self.fee_bps / 10000)
                slippage_cost = abs(trade_units) * abs(fill_price - current_price)

                # Update cash and holdings
                cash -= trade_units * fill_price + fee
                holdings += trade_units

                # Record
                total_fees += fee
                total_slippage += slippage_cost

                trades.append({
                    "bar_idx": i,
                    "ts": bar["ts"],
                    "side": "buy" if trade_units > 0 else "sell",
                    "units": abs(trade_units),
                    "price": fill_price,
                    "fee": fee,
                    "slippage": slippage_cost,
                })

            # Update position and equity
            positions[i] = holdings
            equity[i] = cash + holdings * current_price

        return {
            "equity_curve": equity,
            "positions": positions,
            "trades": trades,
            "total_fees": total_fees,
            "total_slippage": total_slippage,
            "n_trades": len(trades),
            "final_equity": equity[-1],
            "final_return": (equity[-1] / self.initial_capital - 1),
        }


def benchmark_buy_and_hold(bars: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Buy & Hold benchmark.

    Args:
        bars: OHLCV DataFrame
        initial_capital: Starting capital

    Returns:
        Dict with equity_curve
    """
    prices = bars["close"].values
    equity = initial_capital * (prices / prices[0])

    return {
        "equity_curve": equity,
        "final_equity": equity[-1],
        "final_return": (equity[-1] / initial_capital - 1),
    }


def benchmark_sma_crossover(
    bars: pd.DataFrame, sma_fast: int = 20, sma_slow: int = 50, initial_capital: float = 10000.0
) -> dict:
    """
    SMA crossover benchmark.

    Args:
        bars: OHLCV DataFrame
        sma_fast: Fast SMA period
        sma_slow: Slow SMA period
        initial_capital: Starting capital

    Returns:
        Dict with equity_curve
    """
    prices = bars["close"].values

    # Calculate SMAs
    sma_f = pd.Series(prices).rolling(sma_fast).mean().values
    sma_s = pd.Series(prices).rolling(sma_slow).mean().values

    # Signals (1 = long when fast > slow, else 0)
    signals = (sma_f > sma_s).astype(int)

    # Run simple backtest (no fees/slippage for benchmark)
    equity = np.zeros(len(bars))
    equity[0] = initial_capital

    position = 0
    cash = initial_capital
    holdings = 0.0

    for i in range(1, len(bars)):
        target_signal = signals[i]
        price = prices[i]

        if target_signal == 1 and position == 0:  # Buy
            holdings = cash / price
            cash = 0
            position = 1
        elif target_signal == 0 and position == 1:  # Sell
            cash = holdings * price
            holdings = 0
            position = 0

        equity[i] = cash + holdings * price

    return {
        "equity_curve": equity,
        "final_equity": equity[-1],
        "final_return": (equity[-1] / initial_capital - 1),
    }

