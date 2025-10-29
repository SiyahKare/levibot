import logging

from fastapi import APIRouter, Response

from .routes import signals_run
from .schemas import SignalRunRequest

adapter = APIRouter()
log = logging.getLogger(__name__)


@adapter.post("/backtest/run")
def backtest_run_legacy(req: SignalRunRequest, response: Response):
    response.headers["X-Deprecated"] = "true"
    response.headers["X-Note"] = "Use /signals/run ; DEPRECATE in 2 sprints"
    log.warning("DEPRECATE %s -> %s", "/backtest/run", "/signals/run")
    return signals_run(req)


# Legacy mapping örnekleri
DEPRECATE_AT = "2025-11-30"
LEGACY = {
    "/backtest/run": "/signals/run",
    "/exec/test-order": "/exec/dry-run",
    "/strategy/perp_breakout": "/signals/run",
}
