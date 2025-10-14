"""
Backtesting API endpoints (Sprint-10 Epic-D).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRunRequest(BaseModel):
    """Request model for running a backtest."""

    symbol: str = "BTC/USDT"
    days: int = 30
    fee_bps: int = 5
    slippage_bps: int = 5
    max_pos: float = 1.0


@router.get("/reports")
async def list_reports() -> list[dict]:
    """
    List all backtest reports.
    
    TODO: Integrate with backend/src/backtest/runner.py
    For now, return mock data for smoke test.
    """
    # Mock data for smoke test
    return [
        {
            "id": "bt_20251014_001",
            "symbol": "BTC/USDT",
            "window": "30 days",
            "created_at": "2025-10-14T10:00:00Z",
            "metrics": {
                "sharpe": 1.45,
                "sortino": 2.12,
                "max_drawdown": -0.083,
                "win_rate": 0.542,
                "ann_return": 0.235,
                "total_trades": 145,
            },
            "links": {
                "markdown": "/backtest/reports/bt_20251014_001/report.md",
                "json": "/backtest/reports/bt_20251014_001/metrics.json",
            },
        }
    ]


@router.post("/run")
async def run_backtest(request: BacktestRunRequest) -> dict:
    """
    Run a backtest with given parameters.
    
    TODO: Integrate with backend/src/backtest/runner.py
    For now, return mock success for smoke test.
    """
    # Mock response for smoke test
    return {
        "ok": True,
        "id": "bt_20251014_002",
        "status": "queued",
        "message": f"Backtest queued for {request.symbol} ({request.days} days)",
    }


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> dict:
    """Get a specific backtest report."""
    # Mock response
    return {
        "id": report_id,
        "symbol": "BTC/USDT",
        "metrics": {
            "sharpe": 1.45,
            "sortino": 2.12,
            "max_drawdown": -0.083,
        },
    }

