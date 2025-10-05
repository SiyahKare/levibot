from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

registry = CollectorRegistry()

levibot_equity = Gauge('levibot_equity', 'Equity USD', ['user'], registry=registry)
levibot_daily_pnl = Gauge('levibot_daily_pnl', 'Daily PnL USD', ['user'], registry=registry)
levibot_risk_used_ratio = Gauge('levibot_risk_used_ratio', 'Risk used ratio', ['user'], registry=registry)
levibot_open_positions = Gauge('levibot_open_positions', 'Open positions', ['symbol','user'], registry=registry)
levibot_orders_total = Counter('levibot_orders_total', 'Orders by status', ['status'], registry=registry)
levibot_signal_long_prob = Gauge('levibot_signal_long_prob', 'Long probability', ['symbol'], registry=registry)
levibot_killswitch_triggers_total = Counter('levibot_killswitch_triggers_total', 'Kill switch triggers', ['type'], registry=registry)

# HTTP metrics (shared registry)
levibot_http_requests_total = Counter('levibot_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'], registry=registry)
levibot_http_request_latency_seconds = Histogram('levibot_http_request_latency_seconds', 'HTTP request latency', ['endpoint'], registry=registry)

# Event metrics
levibot_events_total = Counter('levibot_events_total', 'Total events appended to JSONL', ['event_type'], registry=registry)

# Telegram ingest health
TG_RECONNECTS_TOTAL = Counter('levibot_tg_reconnects_total', 'Total Telegram reconnect attempts', registry=registry)
TG_LAST_MESSAGE_TS = Gauge('levibot_tg_last_message_ts', 'Unix ts of last ingested Telegram message', registry=registry)
TG_LAST_SCORE_OK_TS = Gauge('levibot_tg_last_score_ok_ts', 'Unix ts of last successful score/route call', registry=registry)

# Build info
levibot_build_info = Gauge('levibot_build_info', 'Build information', ['version', 'git_sha', 'branch'], registry=registry)


def inc_event(event_type: str) -> None:
    """Increment event counter; silent fail if metric unavailable."""
    try:
        levibot_events_total.labels(event_type).inc()
    except Exception:
        pass


def render_latest() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST


