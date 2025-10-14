"""
FastAPI main application with engine manager integration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..engine.manager import get_engine_manager, init_engine_manager
from .routers.engines import router as engines_router
from .routers.metrics import router as metrics_router
from .routers.risk import router as risk_router


def load_config() -> dict:
    """
    Load application configuration.

    TODO: Implement proper config loading from:
    - Environment variables
    - YAML config files
    - Command-line arguments
    """
    return {
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

# Register routers
app.include_router(engines_router)
app.include_router(risk_router)
app.include_router(metrics_router)


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
