"""
Backtest report generation (MD/JSON/HTML).

Generates comprehensive backtest reports with charts and metrics.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd


def generate_markdown_report(
    metrics: dict,
    benchmark_metrics: dict,
    params: dict,
    trades: list[dict],
) -> str:
    """
    Generate Markdown report.

    Args:
        metrics: Strategy metrics
        benchmark_metrics: Benchmark metrics
        params: Backtest parameters
        trades: List of trades

    Returns:
        Markdown string
    """
    md = f"""# Backtest Report

**Generated**: {datetime.now(UTC).isoformat()}

---

## Parameters

| Parameter | Value |
|-----------|-------|
| Symbol | {params.get('symbol', 'N/A')} |
| Timeframe | {params.get('timeframe', '1m')} |
| Days | {params.get('days', 'N/A')} |
| Initial Capital | ${params.get('initial_capital', 10000):,.2f} |
| Fee (bps) | {params.get('fee_bps', 5):.1f} |
| Slippage (bps) | {params.get('slippage_bps', 5):.1f} |
| Latency (ms) | {params.get('latency_ms', 100):.0f} |
| Risk Cap | {params.get('risk_cap', 0.2):.1%} |
| Model | {params.get('model', 'ensemble')} |
| Snapshot ID | {params.get('snapshot_id', 'N/A')} |

---

## Performance Metrics

| Metric | Strategy | Buy & Hold | Difference |
|--------|----------|------------|------------|
| **Sharpe Ratio** | {metrics['sharpe']:.3f} | {benchmark_metrics.get('sharpe', 0):.3f} | {metrics['sharpe'] - benchmark_metrics.get('sharpe', 0):+.3f} |
| **Sortino Ratio** | {metrics['sortino']:.3f} | {benchmark_metrics.get('sortino', 0):.3f} | {metrics['sortino'] - benchmark_metrics.get('sortino', 0):+.3f} |
| **CAGR** | {metrics['cagr']:.2%} | {benchmark_metrics.get('cagr', 0):.2%} | {metrics['cagr'] - benchmark_metrics.get('cagr', 0):+.2%} |
| **Max Drawdown** | {metrics['mdd']:.2%} | {benchmark_metrics.get('mdd', 0):.2%} | {metrics['mdd'] - benchmark_metrics.get('mdd', 0):+.2%} |
| **Cum Return** | {metrics['cum_return']:.2%} | {benchmark_metrics.get('cum_return', 0):.2%} | {metrics['cum_return'] - benchmark_metrics.get('cum_return', 0):+.2%} |
| **Hit Rate** | {metrics['hit_rate']:.2%} | - | - |
| **Turnover** | {metrics['turnover']:.1f} | - | - |
| **Final Equity** | ${metrics['final_equity']:,.2f} | ${benchmark_metrics.get('final_equity', 0):,.2f} | ${metrics['final_equity'] - benchmark_metrics.get('final_equity', 0):+,.2f} |

---

## Trade Statistics

| Metric | Value |
|--------|-------|
| Total Trades | {params.get('n_trades', 0)} |
| Total Fees | ${params.get('total_fees', 0):,.2f} |
| Total Slippage | ${params.get('total_slippage', 0):,.2f} |
| Avg Trade Size | ${params.get('total_fees', 0) / max(params.get('n_trades', 1), 1):,.2f} |

---

## Recent Trades (Last 10)

| Timestamp | Side | Units | Price | Fee | Slippage |
|-----------|------|-------|-------|-----|----------|
"""

    # Add last 10 trades
    for trade in trades[-10:]:
        ts = pd.Timestamp(trade['ts'], unit='ms').strftime('%Y-%m-%d %H:%M')
        md += f"| {ts} | {trade['side']} | {trade['units']:.4f} | ${trade['price']:.2f} | ${trade['fee']:.2f} | ${trade['slippage']:.4f} |\n"

    md += "\n---\n\n**Status**: "
    
    if metrics['sharpe'] >= benchmark_metrics.get('sharpe', 0) + 0.2:
        md += "✅ **PASS** (Sharpe > Benchmark + 0.2)\n"
    else:
        md += "⚠️ **WARNING** (Sharpe not significantly better than benchmark)\n"

    return md


def generate_json_report(
    metrics: dict,
    benchmark_metrics: dict,
    params: dict,
    trades: list[dict],
    equity_curve: np.ndarray,
    positions: np.ndarray,
) -> dict:
    """
    Generate JSON report.

    Args:
        metrics: Strategy metrics
        benchmark_metrics: Benchmark metrics
        params: Backtest parameters
        trades: List of trades
        equity_curve: Equity curve array
        positions: Position array

    Returns:
        Report dict
    """
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "params": params,
        "metrics": metrics,
        "benchmark": benchmark_metrics,
        "trades": trades,
        "equity_curve": equity_curve.tolist(),
        "positions": positions.tolist(),
        "status": "pass" if metrics['sharpe'] >= benchmark_metrics.get('sharpe', 0) + 0.2 else "warning",
    }

    return report


def generate_html_report(
    metrics: dict,
    benchmark_metrics: dict,
    params: dict,
    trades: list[dict],
    equity_curve: np.ndarray,
    benchmark_equity: np.ndarray,
) -> str:
    """
    Generate HTML report with embedded charts.

    Args:
        metrics: Strategy metrics
        benchmark_metrics: Benchmark metrics
        params: Backtest parameters
        trades: List of trades
        equity_curve: Strategy equity curve
        benchmark_equity: Benchmark equity curve

    Returns:
        HTML string
    """
    # Prepare data for charts (simplified - would use plotly/chart.js in production)
    equity_data = ",".join([f"{v:.2f}" for v in equity_curve[::max(1, len(equity_curve)//200)]])  # Sample
    benchmark_data = ",".join([f"{v:.2f}" for v in benchmark_equity[::max(1, len(benchmark_equity)//200)]])

    status_badge = "✅ PASS" if metrics['sharpe'] >= benchmark_metrics.get('sharpe', 0) + 0.2 else "⚠️ WARNING"
    status_color = "#22c55e" if "PASS" in status_badge else "#f59e0b"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {params.get('symbol', 'N/A')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8fafc;
        }}
        h1, h2 {{ color: #1e293b; }}
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            background: {status_color};
            color: white;
            font-weight: 600;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metric-label {{ color: #64748b; font-size: 14px; }}
        .metric-value {{ font-size: 24px; font-weight: 700; color: #1e293b; margin-top: 8px; }}
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
    </style>
</head>
<body>
    <h1>📊 Backtest Report</h1>
    <span class="badge">{status_badge}</span>
    
    <h2>Parameters</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th></tr>
        <tr><td>Symbol</td><td>{params.get('symbol', 'N/A')}</td></tr>
        <tr><td>Timeframe</td><td>{params.get('timeframe', '1m')}</td></tr>
        <tr><td>Days</td><td>{params.get('days', 'N/A')}</td></tr>
        <tr><td>Initial Capital</td><td>${params.get('initial_capital', 10000):,.2f}</td></tr>
        <tr><td>Fee (bps)</td><td>{params.get('fee_bps', 5):.1f}</td></tr>
        <tr><td>Slippage (bps)</td><td>{params.get('slippage_bps', 5):.1f}</td></tr>
        <tr><td>Latency (ms)</td><td>{params.get('latency_ms', 100):.0f}</td></tr>
        <tr><td>Model</td><td>{params.get('model', 'ensemble')}</td></tr>
        <tr><td>Snapshot ID</td><td>{params.get('snapshot_id', 'N/A')}</td></tr>
    </table>
    
    <h2>Performance Metrics</h2>
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Sharpe Ratio</div>
            <div class="metric-value {'positive' if metrics['sharpe'] > 0 else ''}">{metrics['sharpe']:.3f}</div>
            <small>Benchmark: {benchmark_metrics.get('sharpe', 0):.3f}</small>
        </div>
        <div class="metric-card">
            <div class="metric-label">CAGR</div>
            <div class="metric-value {'positive' if metrics['cagr'] > 0 else 'negative'}">{metrics['cagr']:.2%}</div>
            <small>Benchmark: {benchmark_metrics.get('cagr', 0):.2%}</small>
        </div>
        <div class="metric-card">
            <div class="metric-label">Max Drawdown</div>
            <div class="metric-value negative">{metrics['mdd']:.2%}</div>
            <small>Benchmark: {benchmark_metrics.get('mdd', 0):.2%}</small>
        </div>
        <div class="metric-card">
            <div class="metric-label">Hit Rate</div>
            <div class="metric-value">{metrics['hit_rate']:.2%}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Final Equity</div>
            <div class="metric-value">${metrics['final_equity']:,.2f}</div>
            <small>Return: {metrics['cum_return']:.2%}</small>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Trades</div>
            <div class="metric-value">{params.get('n_trades', 0)}</div>
            <small>Fees: ${params.get('total_fees', 0):,.2f}</small>
        </div>
    </div>
    
    <h2>Equity Curve</h2>
    <p><em>Chart placeholder - Strategy: [{equity_data[:100]}...] vs Benchmark: [{benchmark_data[:100]}...]</em></p>
    <p><small>In production, embed Chart.js/Plotly here for interactive visualization.</small></p>
    
    <h2>Recent Trades</h2>
    <table>
        <tr><th>Timestamp</th><th>Side</th><th>Units</th><th>Price</th><th>Fee</th></tr>
"""

    for trade in trades[-10:]:
        ts = pd.Timestamp(trade['ts'], unit='ms').strftime('%Y-%m-%d %H:%M')
        html += f"        <tr><td>{ts}</td><td>{trade['side']}</td><td>{trade['units']:.4f}</td><td>${trade['price']:.2f}</td><td>${trade['fee']:.2f}</td></tr>\n"

    html += """    </table>
    
    <hr>
    <p><small>Generated: """ + datetime.now(UTC).isoformat() + """</small></p>
</body>
</html>
"""

    return html


def save_reports(
    output_dir: Path,
    metrics: dict,
    benchmark_metrics: dict,
    params: dict,
    trades: list[dict],
    equity_curve: np.ndarray,
    positions: np.ndarray,
    benchmark_equity: np.ndarray,
):
    """
    Save all report formats.

    Args:
        output_dir: Output directory
        metrics: Strategy metrics
        benchmark_metrics: Benchmark metrics
        params: Backtest parameters
        trades: List of trades
        equity_curve: Strategy equity curve
        positions: Position array
        benchmark_equity: Benchmark equity curve
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_report = generate_markdown_report(metrics, benchmark_metrics, params, trades)
    md_path = output_dir / "report.md"
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"💾 Saved Markdown: {md_path}")

    # JSON
    json_report = generate_json_report(
        metrics, benchmark_metrics, params, trades, equity_curve, positions
    )
    json_path = output_dir / "report.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    print(f"💾 Saved JSON: {json_path}")

    # HTML
    html_report = generate_html_report(
        metrics, benchmark_metrics, params, trades, equity_curve, benchmark_equity
    )
    html_path = output_dir / "report.html"
    with open(html_path, "w") as f:
        f.write(html_report)
    print(f"💾 Saved HTML: {html_path}")

    # Save arrays (numpy)
    np.save(output_dir / "equity_curve.npy", equity_curve)
    np.save(output_dir / "positions.npy", positions)
    np.save(output_dir / "benchmark_equity.npy", benchmark_equity)
    print(f"💾 Saved arrays: {output_dir}")
