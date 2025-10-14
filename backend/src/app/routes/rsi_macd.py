"""
RSI + MACD Strategy API Routes
"""

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from ...strategies.rsi_macd import RsiMacdConfig, RsiMacdEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy/rsi-macd", tags=["rsi_macd"])

# Global engine instance
_engine: RsiMacdEngine | None = None


def _get_engine() -> RsiMacdEngine:
    """Get or create engine instance"""
    global _engine
    if _engine is None:
        # Load default config (day mode)
        config = _load_config("day")
        _engine = RsiMacdEngine(config, mode="paper")
    return _engine


def _load_config(mode: str = "day") -> RsiMacdConfig:
    """Load config from YAML file"""
    config_path = Path(f"configs/rsi_macd.{mode}.yaml")

    if not config_path.exists():
        logger.warning(f"Config not found: {config_path}, using defaults")
        return RsiMacdConfig(mode=mode)

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return RsiMacdConfig.from_dict(data)


# ─────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────


@router.get("/health")
def rsi_macd_health():
    """Get strategy health and status"""
    engine = _get_engine()
    return engine.health()


@router.get("/params")
def rsi_macd_get_params():
    """Get current strategy parameters"""
    engine = _get_engine()
    return engine.get_params()


@router.post("/params")
def rsi_macd_update_params(params: dict):
    """Update strategy parameters"""
    engine = _get_engine()
    return engine.set_params(params)


@router.post("/run")
def rsi_macd_run(action: str):
    """
    Start/stop the strategy.

    Args:
        action: "start" | "stop"
    """
    engine = _get_engine()

    if action == "start":
        return engine.start()
    elif action == "stop":
        return engine.stop()
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")


@router.get("/pnl")
def rsi_macd_pnl():
    """Get PnL summary"""
    engine = _get_engine()
    return engine.pnl()


@router.get("/trades/recent")
def rsi_macd_trades_recent(limit: int = 100):
    """Get recent trades"""
    engine = _get_engine()
    return {"trades": engine.trades_recent(limit)}


@router.post("/load-preset")
def rsi_macd_load_preset(mode: str):
    """
    Load a preset configuration.

    Args:
        mode: "scalp" | "day" | "swing"
    """
    global _engine

    if mode not in ["scalp", "day", "swing"]:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")

    # Stop existing engine if running
    if _engine and _engine._running:
        _engine.stop()

    # Load new config and create engine
    config = _load_config(mode)
    _engine = RsiMacdEngine(config, mode="paper")

    logger.info(f"Loaded RSI+MACD preset: {mode}")
    return {"status": "loaded", "mode": mode, "config": config.to_dict()}
