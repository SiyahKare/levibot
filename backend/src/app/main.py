"""
FastAPI main application with engine manager integration.
"""

import os
from copy import deepcopy
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml

from ..engine.manager import get_engine_manager, init_engine_manager
from .routers.ai import router as ai_router
from .routers.analytics import router as analytics_router
from .routers.backtest import router as backtest_router
from .routers.engines import router as engines_router
from .routers.live import router as live_router
from .routers.metrics import router as metrics_router
from .routers.ops import router as ops_router
from .routers.risk import router as risk_router
from .routers.signal_log import router as signal_log_router
from .routers.stream import router as stream_router


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if path.is_dir():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _discover_config_path() -> Path | None:
    env_path = os.getenv("LEVI_CONFIG_PATH")
    if env_path:
        return Path(env_path)

    config_dir = Path("configs")
    preferred = (
        config_dir / "levi.yml",
        config_dir / "levi.yaml",
        config_dir / "engine.yml",
        config_dir / "engine.yaml",
    )
    for candidate in preferred:
        if candidate.exists():
            return candidate

    if config_dir.exists():
        candidates = sorted(
            list(config_dir.glob("*.yml")) + list(config_dir.glob("*.yaml"))
        )
        if candidates:
            return candidates[0]

    return None


def _env_float(name: str) -> float | None:
    value = os.getenv(name)
    if value is None:
        return None
    return float(value)


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None:
        return None
    return int(value)


def _env_str(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    return value


def _load_env_config() -> dict[str, Any]:
    config: dict[str, Any] = {}

    engine_defaults: dict[str, Any] = {}
    if (cycle_interval := _env_float("LEVI_ENGINE_CYCLE_INTERVAL")) is not None:
        engine_defaults["cycle_interval"] = cycle_interval
    if (equity_base := _env_float("LEVI_ENGINE_EQUITY_BASE")) is not None:
        engine_defaults["equity_base"] = equity_base
    if (vol_ann := _env_float("LEVI_ENGINE_VOL_ANN")) is not None:
        engine_defaults["vol_ann"] = vol_ann
    if (md_queue_max := _env_int("LEVI_ENGINE_MD_QUEUE_MAX")) is not None:
        engine_defaults["md_queue_max"] = md_queue_max

    if engine_defaults:
        config["engine_defaults"] = engine_defaults

    symbols_to_trade = os.getenv("LEVI_SYMBOLS_TO_TRADE")
    if symbols_to_trade:
        config["symbols_to_trade"] = [
            symbol.strip()
            for symbol in symbols_to_trade.split(",")
            if symbol.strip()
        ]

    ai: dict[str, Any] = {}
    ensemble: dict[str, Any] = {}
    if (w_lgbm := _env_float("LEVI_AI_ENSEMBLE_W_LGBM")) is not None:
        ensemble["w_lgbm"] = w_lgbm
    if (w_tft := _env_float("LEVI_AI_ENSEMBLE_W_TFT")) is not None:
        ensemble["w_tft"] = w_tft
    if (w_sent := _env_float("LEVI_AI_ENSEMBLE_W_SENT")) is not None:
        ensemble["w_sent"] = w_sent
    if (threshold := _env_float("LEVI_AI_ENSEMBLE_THRESHOLD")) is not None:
        ensemble["threshold"] = threshold
    if ensemble:
        ai["ensemble"] = ensemble

    sentiment: dict[str, Any] = {}
    if (provider := _env_str("LEVI_AI_SENTIMENT_PROVIDER")) is not None:
        sentiment["provider"] = provider
    if (rpm := _env_int("LEVI_AI_SENTIMENT_RPM")) is not None:
        sentiment["rpm"] = rpm
    if (ttl := _env_int("LEVI_AI_SENTIMENT_TTL")) is not None:
        sentiment["ttl"] = ttl
    if sentiment:
        ai["sentiment"] = sentiment

    onchain: dict[str, Any] = {}
    if (provider := _env_str("LEVI_AI_ONCHAIN_PROVIDER")) is not None:
        onchain["provider"] = provider
    if (ttl := _env_int("LEVI_AI_ONCHAIN_TTL")) is not None:
        onchain["ttl"] = ttl
    if onchain:
        ai["onchain"] = onchain

    if ai:
        config["ai"] = ai

    return config


def load_config() -> dict:
    """
    Load application configuration.

    Order of precedence (last wins):
    1) Defaults in code
    2) YAML config file (LEVI_CONFIG_PATH or configs/*.yml)
    3) Environment variable overrides
    """
    defaults = {
        "engine_defaults": {
            "cycle_interval": 1.0,  # seconds
            "equity_base": 10000.0,  # base equity for risk calc
            "vol_ann": 0.6,  # default annual volatility
            "md_queue_max": 256,  # market data queue size
        },
        "symbols_to_trade": [
            "BTC/USDT",  # ccxt format
            "ETH/USDT",
            "SOL/USDT",
        ],
        "symbols": {
            # Symbol-specific overrides
            "BTCUSDT": {
                "cycle_interval": 0.5,  # faster for BTC
                "equity_base": 10000.0,
                "vol_ann": 0.8,  # BTC typically higher vol
            },
        },
        "ai": {
            "ensemble": {
                "w_lgbm": 0.5,
                "w_tft": 0.3,
                "w_sent": 0.2,
                "threshold": 0.55,
            },
            "sentiment": {
                "provider": "gemma",
                "rpm": 60,  # requests per minute
                "ttl": 900,  # cache TTL (15 min)
            },
            "onchain": {
                "provider": "mock",  # TODO: dune, nansen
                "ttl": 300,  # cache TTL (5 min)
            },
        },
    }

    config = deepcopy(defaults)

    config_path = _discover_config_path()
    if config_path:
        config = _deep_merge(config, _load_yaml_config(config_path))

    env_config = _load_env_config()
    if env_config:
        config = _deep_merge(config, env_config)

    return config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of engine manager.
    """
    # Startup
    print("🚀 Starting LeviBot Engine Manager...")

    config = load_config()
    manager = init_engine_manager(config)

    symbols = config.get("symbols_to_trade", [])
    await manager.start_all(symbols)

    print("✅ LeviBot Engine Manager ready")

    yield

    # Shutdown
    print("🛑 Shutting down LeviBot Engine Manager...")
    await manager.stop_all()
    print("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="LeviBot Engine API",
    description="Multi-symbol trading engine orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Panel dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(engines_router)
app.include_router(backtest_router)
app.include_router(risk_router)
app.include_router(metrics_router)
app.include_router(live_router)
app.include_router(stream_router)

# AI & Analytics routers
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(ops_router)
app.include_router(signal_log_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    try:
        manager = get_engine_manager()
        summary = manager.get_summary()
        return {
            "status": "ok",
            "service": "levibot-engine",
            "engines": summary,
        }
    except RuntimeError:
        return {
            "status": "initializing",
            "service": "levibot-engine",
        }


@app.get("/health")
async def health():
    """Kubernetes-style health check."""
    return {"status": "healthy"}
