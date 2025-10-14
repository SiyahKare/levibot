"""
Automation API — Trading automation status and controls
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body

router = APIRouter(prefix="/automation", tags=["automation"])


def _get_paper_stats() -> dict[str, Any]:
    """Get paper trading portfolio stats"""
    try:
        from ...exec.paper_portfolio import get_paper_portfolio

        portfolio = get_paper_portfolio()

        # Calculate today's trades
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = sum(
            1
            for trade in portfolio.trade_history
            if datetime.fromisoformat(trade["opened_at"]) >= today_start
        )

        # Calculate Sharpe & Max DD (simplified)
        total_pnl = sum(p.unrealized_pnl for p in portfolio.positions.values())
        realized_pnl = portfolio.total_realized_pnl

        # Regime detection (based on recent PnL)
        if realized_pnl > 50:
            regime = "BULLISH"
        elif realized_pnl < -50:
            regime = "BEARISH"
        else:
            regime = "NEUTRAL"

        return {
            "trades_today": trades_today,
            "open_positions": len(portfolio.positions),
            "realized_pnl": realized_pnl,
            "unrealized_pnl": total_pnl,
            "regime": regime,
            "equity": portfolio.cash_balance + portfolio.total_position_value,
        }
    except Exception as e:
        return {
            "trades_today": 0,
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "regime": "NEUTRAL",
            "equity": 10000.0,
            "error": str(e),
        }


@router.get("/status")
async def get_automation_status():
    """Get automation status with real paper trading data"""
    try:
        from ...infra.flags_store import load_flags

        # Load flags
        flags = load_flags()

        # Get paper portfolio stats
        stats = _get_paper_stats()

        # AI trading enabled status
        ai_enabled = flags.get("enable_ai_trading", False)
        killed = flags.get("killed", False)

        # Effective enabled status
        enabled = ai_enabled and not killed

        # Risk parameters from flags
        max_positions = flags.get("max_open_positions", 5)
        max_trade_usd = flags.get("guardrails_max_trade_usd", 500.0)
        confidence_threshold = flags.get("guardrails_confidence_threshold", 0.6)

        # Calculate stop loss and take profit from risk config
        stop_loss_pct = (
            abs(flags.get("max_daily_loss", -200.0)) / 10000.0
        )  # Convert to fraction
        take_profit_pct = 0.03  # 3% default

        # Policy thresholds
        policy = {"entry": confidence_threshold, "exit": confidence_threshold - 0.2}

        # Sharpe and Max DD (TODO: calculate from trade history)
        sharpe = None
        max_dd = None

        return {
            "enabled": enabled,
            "killed": killed,
            "cycle_count": stats["trades_today"],
            "trades_today": stats["trades_today"],
            "max_positions": max_positions,
            "min_confidence": confidence_threshold,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
            "canary_fraction": 0.0,  # TODO: implement canary mode
            "policy": policy,
            "regime": stats["regime"],
            "sharpe": sharpe,
            "max_dd": max_dd,
            "equity": stats["equity"],
            "open_positions": stats["open_positions"],
        }
    except Exception as e:
        # Fallback response on error
        return {
            "enabled": False,
            "killed": False,
            "cycle_count": 0,
            "trades_today": 0,
            "max_positions": 5,
            "min_confidence": 0.6,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.03,
            "canary_fraction": 0.0,
            "policy": {"entry": 0.6, "exit": 0.4},
            "regime": "NEUTRAL",
            "sharpe": None,
            "max_dd": None,
            "error": str(e),
        }


@router.post("/start")
async def start_automation(
    canary_fraction: float = Body(default=0.0), min_conf: float = Body(default=0.6)
):
    """Start automation with configuration"""
    try:
        from ...infra.flags_store import load_flags, merge_flags

        flags = load_flags()

        # Enable AI trading
        flags["enable_ai_trading"] = True
        flags["killed"] = False

        # Update confidence threshold if provided
        if min_conf is not None:
            flags["guardrails_confidence_threshold"] = min_conf

        # Save flags
        merge_flags(flags)

        return {
            "ok": True,
            "enabled": True,
            "canary_fraction": canary_fraction,
            "min_confidence": min_conf,
            "message": "Automation enabled",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
