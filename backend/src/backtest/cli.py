#!/usr/bin/env python3
"""
Backtest CLI.

Usage:
    python -m backend.src.backtest.cli run --bars data.parquet --signal ensemble
    python -m backend.src.backtest.cli batch --symbols BTCUSDT,ETHUSDT --days 90
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.src.backtest.metrics import calculate_all_metrics
from backend.src.backtest.report import save_reports
from backend.src.backtest.runner_v2 import (
    BacktestRunnerV2,
    benchmark_buy_and_hold,
    benchmark_sma_crossover,
)
from backend.src.backtest.strategies import ensemble_to_position


def load_bars(bars_path: Path) -> pd.DataFrame:
    """Load bars from parquet."""
    if not bars_path.exists():
        raise FileNotFoundError(f"Bars file not found: {bars_path}")

    df = pd.read_parquet(bars_path)

    # Ensure required columns
    required = ["ts", "open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required):
        raise ValueError(f"bars must have columns: {required}")

    return df


def generate_ensemble_signals(bars: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate ensemble signals (placeholder - would call ML models in production).

    Args:
        bars: OHLCV DataFrame

    Returns:
        (prob_up, confidence) tuple
    """
    n = len(bars)

    # Placeholder: simple momentum + mean reversion
    # In production, this would call LGBMProd, TFTProd, EnsemblePredictor
    prices = bars["close"].values
    returns = np.diff(prices, prepend=prices[0]) / prices

    # Simple heuristic: prob_up based on short-term momentum
    prob_up = 0.5 + np.clip(returns * 10, -0.4, 0.4)

    # Confidence: based on volatility
    rolling_vol = pd.Series(returns).rolling(20, min_periods=1).std().values
    confidence = np.clip(1 - rolling_vol * 20, 0.1, 0.9)

    return prob_up, confidence


def run_backtest(
    bars_path: Path,
    signal_type: str = "ensemble",
    fee_bps: float = 5.0,
    slippage_bps: float = 5.0,
    latency_ms: float = 100.0,
    risk_cap: float = 0.2,
    initial_capital: float = 10000.0,
    output_dir: Path | None = None,
) -> dict:
    """
    Run single backtest.

    Args:
        bars_path: Path to bars parquet
        signal_type: Signal type ('ensemble', 'lgbm', 'tft')
        fee_bps: Fee in basis points
        slippage_bps: Slippage in basis points
        latency_ms: Order latency in ms
        risk_cap: Max position size
        initial_capital: Starting capital
        output_dir: Output directory for reports

    Returns:
        Results dict
    """
    print(f"\n🔄 Running backtest: {bars_path.name}")

    # Load bars
    bars = load_bars(bars_path)
    print(f"   Loaded {len(bars):,} bars")

    # Generate signals
    print(f"   Signal type: {signal_type}")
    if signal_type == "ensemble":
        prob_up, confidence = generate_ensemble_signals(bars)
    else:
        # Fallback
        prob_up, confidence = generate_ensemble_signals(bars)

    # Convert to positions
    signals, sizes = ensemble_to_position(prob_up, confidence, risk_cap=risk_cap)

    # Run backtest
    print(f"   Running backtest (fee={fee_bps}bps, slippage={slippage_bps}bps, latency={latency_ms}ms)...")
    runner = BacktestRunnerV2(
        bars,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        latency_ms=latency_ms,
        initial_capital=initial_capital,
    )

    results = runner.run(signals, sizes)

    # Calculate metrics
    metrics = calculate_all_metrics(results["equity_curve"], results["positions"])
    print(f"   Sharpe: {metrics['sharpe']:.3f}, CAGR: {metrics['cagr']:.2%}, MDD: {metrics['mdd']:.2%}")

    # Benchmarks
    print("   Running benchmarks...")
    bh_results = benchmark_buy_and_hold(bars, initial_capital)
    bh_metrics = calculate_all_metrics(bh_results["equity_curve"], np.ones(len(bars)))

    sma_results = benchmark_sma_crossover(bars, 20, 50, initial_capital)
    sma_metrics = calculate_all_metrics(sma_results["equity_curve"], np.zeros(len(bars)))

    print(f"   Buy & Hold Sharpe: {bh_metrics['sharpe']:.3f}")
    print(f"   SMA(20/50) Sharpe: {sma_metrics['sharpe']:.3f}")

    # Save reports
    if output_dir:
        params = {
            "symbol": bars_path.stem.split("_")[0],
            "timeframe": "1m",
            "days": len(bars) // 1440,  # Approx
            "initial_capital": initial_capital,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
            "latency_ms": latency_ms,
            "risk_cap": risk_cap,
            "model": signal_type,
            "snapshot_id": "N/A",
            "n_trades": results["n_trades"],
            "total_fees": results["total_fees"],
            "total_slippage": results["total_slippage"],
        }

        save_reports(
            output_dir,
            metrics,
            bh_metrics,
            params,
            results["trades"],
            results["equity_curve"],
            results["positions"],
            bh_results["equity_curve"],
        )

    print("✅ Backtest complete!\n")

    return {
        "metrics": metrics,
        "bh_metrics": bh_metrics,
        "sma_metrics": sma_metrics,
        "results": results,
    }


def run_batch(
    symbols: list[str],
    days: int = 90,
    output_dir: Path = Path("backend/reports/backtests"),
    **kwargs,
):
    """
    Run batch backtests.

    Args:
        symbols: List of symbols
        days: Number of days
        output_dir: Output directory
        **kwargs: Additional backtest params
    """
    print(f"\n🔄 Running batch backtests for {len(symbols)} symbols ({days} days)")

    results_summary = []

    for symbol in symbols:
        # Assume bars are in data/bars/{symbol}_1m.parquet
        bars_path = Path(f"backend/data/bars/{symbol}_1m.parquet")

        if not bars_path.exists():
            print(f"⚠️ Skipping {symbol}: bars not found")
            continue

        # Output dir for this symbol
        symbol_output = output_dir / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_{symbol}_{days}d"

        # Run backtest
        result = run_backtest(bars_path, output_dir=symbol_output, **kwargs)

        results_summary.append({
            "symbol": symbol,
            "sharpe": result["metrics"]["sharpe"],
            "cagr": result["metrics"]["cagr"],
            "mdd": result["metrics"]["mdd"],
            "final_equity": result["metrics"]["final_equity"],
        })

    # Print summary
    print("\n📊 Batch Summary:")
    print(f"{'Symbol':<12} {'Sharpe':<10} {'CAGR':<10} {'MDD':<10} {'Final Equity':<15}")
    print("-" * 60)
    for r in results_summary:
        print(f"{r['symbol']:<12} {r['sharpe']:<10.3f} {r['cagr']:<10.2%} {r['mdd']:<10.2%} ${r['final_equity']:<15,.2f}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Backtest CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run single backtest")
    run_parser.add_argument("--bars", type=str, required=True, help="Path to bars parquet")
    run_parser.add_argument("--signal", type=str, default="ensemble", help="Signal type")
    run_parser.add_argument("--fee-bps", type=float, default=5.0, help="Fee (bps)")
    run_parser.add_argument("--slippage-bps", type=float, default=5.0, help="Slippage (bps)")
    run_parser.add_argument("--latency-ms", type=float, default=100.0, help="Latency (ms)")
    run_parser.add_argument("--risk-cap", type=float, default=0.2, help="Risk cap")
    run_parser.add_argument("--initial-capital", type=float, default=10000.0, help="Initial capital")
    run_parser.add_argument("--out", type=str, help="Output directory")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run batch backtests")
    batch_parser.add_argument("--symbols", type=str, required=True, help="Symbols (comma-separated)")
    batch_parser.add_argument("--days", type=int, default=90, help="Days")
    batch_parser.add_argument("--out-dir", type=str, default="backend/reports/backtests", help="Output dir")

    args = parser.parse_args()

    if args.command == "run":
        output_dir = Path(args.out) if args.out else None
        run_backtest(
            Path(args.bars),
            signal_type=args.signal,
            fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps,
            latency_ms=args.latency_ms,
            risk_cap=args.risk_cap,
            initial_capital=args.initial_capital,
            output_dir=output_dir,
        )

    elif args.command == "batch":
        symbols = [s.strip() for s in args.symbols.split(",")]
        run_batch(symbols, days=args.days, output_dir=Path(args.out_dir))

    return 0


if __name__ == "__main__":
    sys.exit(main())

