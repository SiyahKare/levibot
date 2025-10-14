"""
Prometheus metrics for LeviBot.
"""

from prometheus_client import Counter, Gauge, Histogram

# ========== Engine Lifecycle ==========

engine_uptime = Gauge(
    "levi_engine_uptime_seconds",
    "Engine uptime in seconds",
    ["symbol"]
)

engine_heartbeat = Gauge(
    "levi_engine_last_heartbeat",
    "Last heartbeat timestamp (epoch)",
    ["symbol"]
)

engine_errors = Counter(
    "levi_engine_errors_total",
    "Total engine cycle errors",
    ["symbol"]
)

engine_status = Gauge(
    "levi_engine_status",
    "Engine status: 0=stopped, 1=running, 2=crashed",
    ["symbol"]
)


# ========== Inference / Signals ==========

inference_latency = Histogram(
    "levi_inference_latency_seconds",
    "ML inference latency in seconds",
    ["symbol"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

signal_prob = Gauge(
    "levi_signal_prob_up",
    "Ensemble probability of price increase (0-1)",
    ["symbol"]
)

signal_conf = Gauge(
    "levi_signal_confidence",
    "Ensemble confidence score (0-1)",
    ["symbol"]
)

signals_total = Counter(
    "levi_signals_total",
    "Total signals produced",
    ["symbol", "side"]  # side: long/short/flat
)


# ========== Risk / Portfolio ==========

equity_now = Gauge(
    "levi_equity_now",
    "Current total equity"
)

realized_today_pct = Gauge(
    "levi_realized_today_pct",
    "Realized PnL today as percentage"
)

positions_open = Gauge(
    "levi_positions_open",
    "Number of open positions"
)

global_stop = Gauge(
    "levi_global_stop",
    "Global stop loss active: 1=active, 0=inactive"
)


# ========== Export Functions ==========

def export_engine_health(symbol: str, health: dict) -> None:
    """
    Export engine health metrics.
    
    Args:
        symbol: Trading symbol
        health: Health dictionary from engine.get_health()
    """
    engine_uptime.labels(symbol).set(health.get("uptime_seconds", 0))
    
    heartbeat = health.get("last_heartbeat")
    if heartbeat:
        engine_heartbeat.labels(symbol).set(heartbeat)
    
    # Status mapping: stopped=0, running=1, crashed=2
    status_str = health.get("status", "stopped")
    status_val = 1 if status_str == "running" else (2 if status_str == "crashed" else 0)
    engine_status.labels(symbol).set(status_val)


def export_signal(symbol: str, prob_up: float, confidence: float, side: str) -> None:
    """
    Export signal metrics.
    
    Args:
        symbol: Trading symbol
        prob_up: Probability of price increase (0-1)
        confidence: Model confidence (0-1)
        side: Signal side (long/short/flat)
    """
    signal_prob.labels(symbol).set(prob_up)
    signal_conf.labels(symbol).set(confidence)
    signals_total.labels(symbol, side).inc()


def export_risk(book_summary: dict) -> None:
    """
    Export risk management metrics.
    
    Args:
        book_summary: Summary dictionary from risk.summary()
    """
    equity_now.set(book_summary.get("equity_now", 0.0))
    realized_today_pct.set(book_summary.get("realized_today_pct", 0.0))
    positions_open.set(book_summary.get("positions_open", 0))
    
    is_stopped = 1 if book_summary.get("global_stop") else 0
    global_stop.set(is_stopped)

