from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Body
from .schemas import ServiceStatus, StartRequest, StopRequest, SetLeverageRequest, ConfigSnapshot
from .state import STATE
from . import config as cfg
from ..infra.logger import log_event
from ..infra.metrics import (
    render_latest,
    levibot_equity,
    levibot_open_positions,
    levibot_http_requests_total,
    levibot_http_request_latency_seconds,
)
from .schedule import schedule_jobs
from .admin import router as admin_router
from dotenv import load_dotenv
from pathlib import Path
from .reports import router as reports_router
from .exec_test import router as exec_test_router
from .exec_algo import router as exec_algo_router
from fastapi.responses import Response
import os
import time
import requests
from fastapi.middleware.cors import CORSMiddleware
from .ai_twap_dca_api import router as ai_twap_dca_router
from .twap_rule_api import router as twap_rule_router
from .perp_breakout_api import router as perp_breakout_router
from .l2_farm_api import router as l2_router
from .telegram_api import router as tg_router
from .config_api import router as config_router
from ..exec.paper import place_paper_order
from ..exec.paper_ccxt import place_cex_paper_order
from ..exec.types import PaperOrderRequest, PaperOrderResult
from ..core.risk import RiskEngine, RiskConfig, list_policies, get_policy_name, set_policy_name, current_policy
from ..signals.scorer import score_signal
from ..signals.symbols import parse_symbol, to_cex_symbol
from ..signals.fe import parse_features
from ..ml.ds_tools import append_label
from ..ingest.trust import adjust_conf
from ..infra.sec import require_api_key_and_ratelimit
from ..mev.quote import quote_symbol, tri_opportunity
from ..nft.floor import floor_price
from ..l2.yields import list_yields

_risk_api = RiskEngine(RiskConfig())

# In-memory config snapshot to allow lightweight runtime updates for smoke tests
CONFIG_CACHE = {
    "users": cfg.load_users_config(),
    "risk": cfg.load_risk_config(),
    "symbols": cfg.load_symbols_config(),
    "features": cfg.load_features_config(),
    "model": cfg.load_model_config(),
}


app = FastAPI(title="LeviBot API", version="0.1.0")

# CORS (panel geliştirme ve dış istemciler için yapılandırılabilir)
_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware: API key + Rate limit
app.middleware("http")(require_api_key_and_ratelimit())

app.include_router(reports_router)
app.include_router(exec_test_router)
app.include_router(exec_algo_router)
app.include_router(ai_twap_dca_router)
app.include_router(twap_rule_router)
app.include_router(perp_breakout_router)
app.include_router(l2_router)
app.include_router(config_router)
app.include_router(admin_router)
app.include_router(tg_router)


# HTTP request metrics middleware (Prometheus)
@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    endpoint = request.url.path
    status = str(getattr(response, "status_code", "unknown"))
    try:
        levibot_http_requests_total.labels(request.method, endpoint, status).inc()
        levibot_http_request_latency_seconds.labels(endpoint).observe(elapsed)
    except Exception:
        pass
    return response


@app.get("/status", response_model=ServiceStatus)
def get_status() -> ServiceStatus:
    status = ServiceStatus(
        running=STATE.running,
        started_at=STATE.started_at,
        open_positions=STATE.open_positions,
        equity=STATE.equity,
        daily_dd_pct=STATE.daily_dd_pct,
    )
    log_event("HEARTBEAT", {"running": status.running, "open": status.open_positions})
    if status.equity is not None:
        levibot_equity.labels(user="onur").set(status.equity)
    levibot_open_positions.labels(symbol="ALL", user="onur").set(status.open_positions)
    return status


@app.post("/start", response_model=ServiceStatus)
def start_bot(req: StartRequest) -> ServiceStatus:
    STATE.start()
    log_event("SYSTEM", {"action": "START"})
    return get_status()


@app.post("/stop", response_model=ServiceStatus)
def stop_bot(req: StopRequest) -> ServiceStatus:
    STATE.stop()
    log_event("SYSTEM", {"action": "STOP", "reason": req.reason})
    return get_status()


@app.get("/config", response_model=ConfigSnapshot)
def get_config() -> ConfigSnapshot:
    return ConfigSnapshot(
        users=CONFIG_CACHE["users"],
        risk=CONFIG_CACHE["risk"],
        symbols=CONFIG_CACHE["symbols"],
        features=CONFIG_CACHE["features"],
        model=CONFIG_CACHE["model"],
    )


@app.post("/config/reload", response_model=ConfigSnapshot)
def reload_config() -> ConfigSnapshot:
    CONFIG_CACHE.update({
        "users": cfg.load_users_config(),
        "risk": cfg.load_risk_config(),
        "symbols": cfg.load_symbols_config(),
        "features": cfg.load_features_config(),
        "model": cfg.load_model_config(),
    })
    return get_config()


@app.put("/config")
def update_config(payload: dict) -> dict:
    # Minimal merge for smoke run: treat payload as risk global overrides if keys match
    risk = CONFIG_CACHE.get("risk", {})
    # support both flat and nested under 'global'
    if "global" in risk:
        risk_global = risk["global"]
    else:
        risk_global = risk
    for k, v in payload.items():
        risk_global[k] = v
    if "global" in risk:
        risk["global"] = risk_global
    else:
        risk = risk_global
    CONFIG_CACHE["risk"] = risk
    log_event("CONFIG_UPDATE", {"risk_overrides": payload})
    return {"ok": True, "risk": CONFIG_CACHE["risk"]}


@app.get("/metrics/prom")
def prometheus_metrics():
    data, content_type = render_latest()
    return Response(content=data, media_type=content_type)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "service": "levibot", "version": "0.1.0"}


@app.get("/livez")
def livez() -> dict:
    return {"ok": True}


@app.get("/readyz")
def readyz() -> dict:
    eth_http = os.getenv("ETH_HTTP") or os.getenv("ETH_HTTP_URL")
    ok_rpc, err = False, None
    if eth_http:
        try:
            payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            r = requests.post(eth_http, json=payload, timeout=2)
            ok_rpc = (r.status_code == 200 and "result" in r.json())
        except Exception as e:
            err = str(e)
    return {"ok": bool(ok_rpc) if eth_http else True, "eth_http": bool(eth_http), "error": err}


@app.post("/ops/archive")
def ops_archive(day: str | None = None) -> dict:
    """Manuel günlük arşivleme ve GC tetikleyici."""
    import datetime as dt
    from ..infra.archive import archive_day, gc_local
    d = day or dt.date.today().isoformat()
    try:
        url = archive_day(d)
        gc_local(30)
        return {"ok": True, "archived": d, "s3": url}
    except Exception as e:
        return {"ok": False, "archived": d, "error": str(e)}


@app.get("/ops/s3/check")
def ops_s3_check() -> dict:
    """S3 kimlik bilgisi var mı, temel healthcheck."""
    keys = {
        "AWS_ACCESS_KEY_ID": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "AWS_SECRET_ACCESS_KEY": bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
        "AWS_REGION": os.getenv("AWS_REGION"),
        "S3_LOG_BUCKET": os.getenv("S3_LOG_BUCKET"),
    }
    ok = keys["AWS_ACCESS_KEY_ID"] and keys["AWS_SECRET_ACCESS_KEY"] and bool(keys["AWS_REGION"]) and bool(keys["S3_LOG_BUCKET"]) 
    return {"ok": bool(ok), "env": keys}


@app.post("/risk/leverage")
def set_leverage(req: SetLeverageRequest) -> dict:
    STATE.user_leverage[req.user_id] = req.leverage
    return {"ok": True, "user_id": req.user_id, "leverage": req.leverage}


@app.get("/metrics")
def get_metrics() -> dict:
    return {
        "running": STATE.running,
        "open_positions": STATE.open_positions,
        "daily_dd_pct": STATE.daily_dd_pct,
    }


@app.on_event("startup")
def _startup_jobs() -> None:
    try:
        # Load root .env
        load_dotenv(Path(__file__).resolve().parents[3] / ".env")
        schedule_jobs()
    except Exception:
        pass


@app.post("/paper/order", response_model=dict)
def paper_order(
    symbol: str = "ETHUSDT",
    side: str = "buy",
    notional_usd: float = 25.0,
    price: float | None = None,
    trace_id: str | None = None,
) -> dict:
    side_norm = side.lower()
    if side_norm not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="invalid side")
    req = PaperOrderRequest(
        symbol=symbol,
        side=side_norm,  # type: ignore[arg-type]
        notional_usd=notional_usd,
        price=price,
        trace_id=trace_id,
    )
    res: PaperOrderResult = place_paper_order(req)
    return {
        "ok": res.ok,
        "symbol": res.symbol,
        "side": res.side,
        "qty": res.qty,
        "price": res.price,
        "pnl_usd": res.pnl_usd,
    }


@app.post("/exec/cex/paper-order", response_model=dict)
def cex_paper_order(
    exchange: str = "binance",
    symbol: str = "ETH/USDT",
    side: str = "buy",
    notional_usd: float = 25.0,
    price: float | None = None,
    trace_id: str | None = None,
) -> dict:
    res = place_cex_paper_order(exchange, symbol, side, notional_usd, price=price, trace_id=trace_id)
    return {
        "ok": res.ok,
        "exchange": exchange,
        "symbol": res.symbol,
        "side": res.side,
        "qty": res.qty,
        "price": res.price,
        "pnl_usd": res.pnl_usd,
    }


@app.post("/risk/preview", response_model=dict)
def risk_preview(side: str = "buy", price: float = 100.0, atr: float | None = None) -> dict:
    sl, tp = _risk_api.sl_tp(side, price, atr)
    return {"sl": sl, "tp": tp, "basis": "atr" if atr else "fallback"}


@app.get("/risk/policy", response_model=dict)
def risk_policy_get() -> dict:
    pol = current_policy()
    return {
        "ok": True,
        "current": pol.name,
        "choices": list_policies(),
        "multipliers": {"sl": pol.atr_mult_sl, "tp": pol.atr_mult_tp},
        "cooldown_sec": pol.cooldown_sec,
    }


@app.put("/risk/policy", response_model=dict)
def risk_policy_put(payload: dict = Body(...)) -> dict:
    name = (payload.get("name") or "").strip().lower()
    try:
        newname = set_policy_name(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    pol = current_policy()
    log_event("RISK_POLICY_CHANGED", {"name": newname, "sl_mult": pol.atr_mult_sl, "tp_mult": pol.atr_mult_tp, "cooldown_sec": pol.cooldown_sec})
    return {"ok": True, "current": newname}


@app.post("/signals/score", response_model=dict)
def signals_score(text: str) -> dict:
    res = score_signal(text)
    log_event("SIGNAL_SCORED", {"text": text[:160], **res})
    return res


@app.post("/signals/ingest-and-score", response_model=dict)
def signals_ingest_and_score(text: str, source: str = "telegram", channel: str | None = None) -> dict:
    # 1) ingest log
    log_event("SIGNAL_INGEST", {"source": source, "channel": channel, "text": text[:300]})

    # 2) score + channel trust adjust
    res = score_signal(text)  # {"label","confidence","reasons"}
    raw_conf = float(res.get("confidence", 0.0))
    conf = adjust_conf(channel or "", raw_conf)
    res["confidence_raw"] = raw_conf
    res["confidence"] = conf
    res.setdefault("reasons", []).append(f"trust:{channel or '-'}")
    label = res.get("label", "NO-TRADE")

    # 3) feature engineering
    fe = parse_features(text)
    # reasons'a kısa özet
    brief = []
    if fe.get("tp") is not None: brief.append(f"tp:{fe['tp']}")
    if fe.get("sl") is not None: brief.append(f"sl:{fe['sl']}")
    if fe.get("size") is not None: brief.append(f"size:{fe['size']}")
    if fe.get("symbols"): brief.append(f"symbols:{len(fe['symbols'])}")
    if brief: res["reasons"].append("fe:" + ",".join(brief))

    log_event("SIGNAL_SCORED", {"source": source, "channel": channel, "text": text[:300], **res, "fe": fe})

    # 4) guards
    enabled = os.getenv("AUTO_ROUTE_ENABLED", "false").lower() == "true"
    dry_run = os.getenv("AUTO_ROUTE_DRY_RUN", "true").lower() == "true"
    min_conf = float(os.getenv("AUTO_ROUTE_MIN_CONF", "0.75"))
    exchange = os.getenv("AUTO_ROUTE_EXCH", "binance")

    # 5) eligibility
    eligible = enabled and label in ("BUY", "SELL") and conf >= min_conf

    route_info = {
        "eligible": eligible,
        "enabled": enabled,
        "dry_run": dry_run,
        "min_conf": min_conf,
        "exchange": exchange,
        "channel": channel,
        "confidence_adj": conf,
        "symbols": fe.get("symbols", []),
    }

    if not eligible:
        log_event(
            "AUTO_ROUTE_SKIPPED",
            {**route_info, "reason": "guard_or_threshold", "label": label},
        )
        return {"ok": True, "routed": False, "score": res, "route": route_info, "fe": fe}

    # 6) semboller: varsa FE'den; yoksa eski parser
    symbols = fe.get("symbols") or []
    if not symbols:
        raw = parse_symbol(text)  # eski fallback
        if raw: symbols = [to_cex_symbol(raw)]

    if not symbols:
        log_event(
            "AUTO_ROUTE_SKIPPED",
            {**route_info, "reason": "symbol_parse_failed"},
        )
        return {"ok": True, "routed": False, "score": res, "route": route_info, "fe": fe}

    # 7) size/notional
    default_notional = float(os.getenv("AUTO_ROUTE_DEFAULT_NOTIONAL", "25"))
    notional = float(fe["size"]) if fe.get("size") else default_notional

    # 8) çoklu sembol – her biri için ayrı yürüt
    routed_any = False
    orders = []
    side = "buy" if label == "BUY" else "sell"
    for cex_symbol in symbols:
        if dry_run:
            log_event("AUTO_ROUTE_DRYRUN", {
                "exchange": exchange, "symbol": cex_symbol, "side": side,
                "conf": conf, "tp": fe.get("tp"), "sl": fe.get("sl"), "notional": notional
            })
            continue
        out = place_cex_paper_order(exchange, cex_symbol, side, notional_usd=notional, trace_id=None, fe=fe)
        routed_any = routed_any or bool(out.ok)
        log_event("AUTO_ROUTE_EXECUTED", {
            "exchange": exchange, "symbol": cex_symbol, "side": side, "conf": conf,
            "tp": fe.get("tp"), "sl": fe.get("sl"), "notional": notional,
            "result": {"ok": out.ok, "qty": out.qty, "price": out.price}
        })
        orders.append({"exchange": exchange, "symbol": cex_symbol, "side": side, "qty": out.qty, "price": out.price})

    return {"ok": True, "routed": routed_any, "score": res, "route": route_info, "orders": orders, "fe": fe}


@app.post("/ml/dataset/append", response_model=dict)
def ml_dataset_append(payload: dict) -> dict:
    """Append labeled example to dataset for retraining."""
    text = (payload.get("text") or "").strip()
    label = (payload.get("label") or "").strip().upper()
    if not text or label not in {"BUY", "SELL", "NO-TRADE"}:
        return {"ok": False, "error": "invalid input"}
    append_label(text, label)
    log_event("DS_APPEND", {"label": label, "len": len(text)})
    return {"ok": True}


@app.get("/dex/quote", response_model=dict)
async def dex_quote(sell: str = "ETH", buy: str = "USDC", amount: float = 0.1, chain: str | None = None):
    ch = (chain or os.getenv("DEX_DEFAULT_CHAIN","ethereum")).lower()
    j = await quote_symbol(ch, sell, buy, amount)
    log_event("DEX_QUOTE", {"chain": ch, "sell": sell, "buy": buy, "amount": amount, **j})
    return j


@app.get("/mev/tri-scan", response_model=dict)
async def mev_tri_scan(a: str = "ETH", b: str = "USDC", c: str = "WBTC", amount: float = 0.1, chain: str | None = None):
    ch = (chain or os.getenv("DEX_DEFAULT_CHAIN","ethereum")).lower()
    qa = await quote_symbol(ch, a, b, amount)
    qb = await quote_symbol(ch, b, c, 1.0)     # normalize
    qc = await quote_symbol(ch, c, a, 1.0)
    if not (qa.get("ok") and qb.get("ok") and qc.get("ok")):
        return {"ok": False, "error": "quote failed"}
    edge = tri_opportunity(qa["price"], qb["price"], qc["price"])
    log_event("MEV_TRI", {"chain": ch, "route": f"{a}->{b}->{c}->{a}", "edge": edge})
    return {"ok": True, "route": [a,b,c,a], "edge": edge, "legs": {"ab": qa, "bc": qb, "ca": qc}}


@app.get("/nft/floor", response_model=dict)
async def nft_floor(collection: str):
    out = await floor_price(collection)
    log_event("NFT_FLOOR", {"collection": collection, **out})
    return out


@app.get("/nft/snipe/plan", response_model=dict)
async def nft_snipe_plan(collection: str, budget_usd: float = 200.0, discount_pct: float = 10.0):
    fl = await floor_price(collection)
    if not fl.get("ok"):
        return fl
    target = None
    if fl.get("floor"):
        target = max(0.0, float(fl["floor"]) * (1.0 - discount_pct/100.0))
    plan = {"target_usd": target, "budget_usd": budget_usd, "discount_pct": discount_pct}
    log_event("NFT_SNIPE_PLAN", {"collection": collection, **plan})
    return {"ok": True, "collection": collection, **plan, "floor": fl.get("floor")}


@app.get("/l2/yields", response_model=dict)
def l2_yields():
    j = list_yields()
    log_event("L2_YIELDS", {"count": sum(len(c.get('protocols',[])) for c in j.get('chains',[]))})
    return j

