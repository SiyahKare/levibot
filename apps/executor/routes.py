import os
import time

from fastapi import APIRouter, HTTPException

from pkgs.backtest import compute_metrics
from pkgs.core.io import load_df
from pkgs.signals import STRATEGIES

from .chain import build_mock_data, send_tx
from .main import limiter
from .risk import evaluate_and_filter, request_context
from .schemas import (
    DryRunRequest,
    DryRunResponse,
    Fill,
    Metric,
    SignalRunRequest,
    SignalRunResponse,
    SubmitRequest,
    SubmitResponse,
)
from .telemetry import LAT, REQS

router = APIRouter()


@limiter.limit("30/minute")
@router.post("/signals/run", response_model=SignalRunResponse)
def signals_run(req: SignalRunRequest):
    t0 = time.time()
    route = "/signals/run"
    try:
        # Set request context for logging
        request_context.set(getattr(req, "state", {}).get("rid", ""))

        try:
            df = load_df()
        except Exception as e:
            raise HTTPException(500, f"data load error: {e}")

        if req.strategy not in STRATEGIES:
            raise HTTPException(400, f"unknown strategy: {req.strategy}")

        # Strategy-specific parameter validation
        from .schemas import PARAM_SCHEMAS

        Schema = PARAM_SCHEMAS[req.strategy]
        try:
            params = Schema(**req.params)  # yanlış alan gelirse 422
        except Exception as e:
            raise HTTPException(422, f"Invalid parameters for {req.strategy}: {e}")

        equity, raw_orders = STRATEGIES[req.strategy](df, **params.dict())

        # Risk filtresi - dict'leri Order objelerine çevir
        from .schemas import Order

        order_objects = [Order(**o) for o in raw_orders]
        orders, veto_logs = evaluate_and_filter(order_objects)
        m = compute_metrics(equity, orders)
        metrics = Metric(sharpe=m["sharpe"], max_dd=m["max_dd"], win_rate=m["win_rate"])
        resp = SignalRunResponse(
            equity_curve=list(map(float, equity)), orders=orders, metrics=metrics
        )
        return resp
    finally:
        LAT.labels(route).observe(time.time() - t0)
        REQS.labels(route).inc()


@limiter.limit("10/minute")
@router.post("/exec/dry-run", response_model=DryRunResponse)
def exec_dry_run(req: DryRunRequest):
    fills = [Fill(pair=o.pair, side=o.side, qty=o.qty, price=100.0) for o in req.orders]
    pnl = sum((1 if f.side == "SELL" else -1) * 0.5 for f in fills)
    logs = [f"slippage={req.slippage_bps}bps; n_orders={len(req.orders)}"]
    return DryRunResponse(fills=fills, pnl=pnl, logs=logs)


@limiter.limit("5/minute")
@router.post("/exec/submit", response_model=SubmitResponse)
def exec_submit(req: SubmitRequest):
    if not req.orders:
        raise HTTPException(400, "orders boş")

    # Security: Allowlist kontrolü
    ALLOWED_TARGETS = {"SAFE", "ROUTER", "VAULT"}  # Gelecekte genişletilebilir
    if req.network not in ALLOWED_TARGETS:
        raise HTTPException(400, f"network {req.network} not allowed")

    safe = os.getenv("SAFE_ADDRESS")
    pk = os.getenv("SESSION_PK")
    if not (safe and pk):
        return SubmitResponse(tx_hash="0xMOCK", safe_tx_url=None)

    data = build_mock_data([o.dict() for o in req.orders])
    tx_hash = send_tx(pk, safe, data, 0)

    # Audit trail: orders hash + request ID
    import hashlib

    orders_hash = hashlib.sha256(str(req.orders).encode()).hexdigest()[:16]

    return SubmitResponse(
        tx_hash=tx_hash,
        safe_tx_url=None,
        orders_hash=orders_hash,
        request_id=getattr(req, "state", {}).get("rid", ""),
    )
