"""
Prometheus Metrics - Production observability
Comprehensive metrics for trading performance and system health
"""
import time
from functools import wraps

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# ============================================
# Trading Metrics
# ============================================

# Signals
signals_generated_total = Counter(
    "levibot_signals_generated_total",
    "Total signals generated",
    ["strategy", "symbol"]
)

signals_executed_total = Counter(
    "levibot_signals_executed_total",
    "Total signals executed",
    ["strategy", "symbol", "side"]
)

signals_blocked_total = Counter(
    "levibot_signals_blocked_total",
    "Total signals blocked by policy",
    ["strategy", "symbol", "reason"]
)

# Orders
orders_submitted_total = Counter(
    "levibot_orders_submitted_total",
    "Total orders submitted",
    ["symbol", "side", "order_type"]
)

orders_filled_total = Counter(
    "levibot_orders_filled_total",
    "Total orders filled",
    ["symbol", "side"]
)

orders_rejected_total = Counter(
    "levibot_orders_rejected_total",
    "Total orders rejected",
    ["symbol", "reason"]
)

# Trades
trades_total = Counter(
    "levibot_trades_total",
    "Total trades completed",
    ["strategy", "symbol", "outcome"]
)

trade_pnl_usd = Histogram(
    "levibot_trade_pnl_usd",
    "Trade PnL in USD",
    ["strategy", "symbol"],
    buckets=[-500, -100, -50, -10, 0, 10, 50, 100, 500]
)

trade_duration_seconds = Histogram(
    "levibot_trade_duration_seconds",
    "Trade duration in seconds",
    ["strategy", "symbol"],
    buckets=[30, 60, 300, 600, 1800, 3600, 7200, 14400]
)

# Portfolio
portfolio_equity_usd = Gauge(
    "levibot_portfolio_equity_usd",
    "Current portfolio equity in USD"
)

portfolio_cash_usd = Gauge(
    "levibot_portfolio_cash_usd",
    "Current cash balance in USD"
)

portfolio_unrealized_pnl_usd = Gauge(
    "levibot_portfolio_unrealized_pnl_usd",
    "Unrealized PnL in USD"
)

portfolio_realized_pnl_usd = Gauge(
    "levibot_portfolio_realized_pnl_usd",
    "Realized PnL in USD"
)

portfolio_exposure_pct = Gauge(
    "levibot_portfolio_exposure_pct",
    "Portfolio exposure as percentage of equity"
)

portfolio_num_positions = Gauge(
    "levibot_portfolio_num_positions",
    "Number of open positions"
)

portfolio_daily_pnl_usd = Gauge(
    "levibot_portfolio_daily_pnl_usd",
    "Daily PnL in USD"
)

portfolio_daily_return_pct = Gauge(
    "levibot_portfolio_daily_return_pct",
    "Daily return percentage"
)

portfolio_drawdown_pct = Gauge(
    "levibot_portfolio_drawdown_pct",
    "Current drawdown percentage"
)

# ============================================
# System Metrics
# ============================================

# Event Bus
event_bus_messages_published = Counter(
    "levibot_event_bus_messages_published",
    "Messages published to event bus",
    ["stream"]
)

event_bus_messages_consumed = Counter(
    "levibot_event_bus_messages_consumed",
    "Messages consumed from event bus",
    ["stream", "consumer"]
)

event_bus_processing_errors = Counter(
    "levibot_event_bus_processing_errors",
    "Event processing errors",
    ["stream", "error_type"]
)

# Feature Store
feature_store_cache_hits = Counter(
    "levibot_feature_store_cache_hits",
    "Feature store cache hits",
    ["symbol"]
)

feature_store_cache_misses = Counter(
    "levibot_feature_store_cache_misses",
    "Feature store cache misses",
    ["symbol"]
)

feature_store_freshness_seconds = Gauge(
    "levibot_feature_store_freshness_seconds",
    "Age of latest features in seconds",
    ["symbol"]
)

# Policy Engine
policy_evaluations_total = Counter(
    "levibot_policy_evaluations_total",
    "Total policy evaluations",
    ["decision"]
)

policy_cooldown_active = Gauge(
    "levibot_policy_cooldown_active",
    "Whether cooldown is active",
    ["symbol"]
)

policy_kill_switch_active = Gauge(
    "levibot_policy_kill_switch_active",
    "Whether kill switch is active"
)

policy_daily_trades_count = Gauge(
    "levibot_policy_daily_trades_count",
    "Number of trades today"
)

policy_daily_loss_limit_remaining_usd = Gauge(
    "levibot_policy_daily_loss_limit_remaining_usd",
    "Remaining daily loss limit in USD"
)

# ML Model
ml_inference_latency_seconds = Histogram(
    "levibot_ml_inference_latency_seconds",
    "ML model inference latency",
    ["model_version"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

ml_predictions_total = Counter(
    "levibot_ml_predictions_total",
    "Total ML predictions",
    ["model_version", "prediction_class"]
)

ml_model_confidence = Histogram(
    "levibot_ml_model_confidence",
    "ML model confidence scores",
    ["model_version"],
    buckets=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
)

# Market Data
market_data_ticks_received = Counter(
    "levibot_market_data_ticks_received",
    "Market data ticks received",
    ["symbol", "source"]
)

market_data_latency_ms = Histogram(
    "levibot_market_data_latency_ms",
    "Market data latency in milliseconds",
    ["symbol", "source"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000]
)

market_data_outliers_filtered = Counter(
    "levibot_market_data_outliers_filtered",
    "Market data outliers filtered",
    ["symbol", "reason"]
)

# ============================================
# Build Info
# ============================================

build_info = Info(
    "levibot_build",
    "Build information"
)


# ============================================
# Helper Functions
# ============================================

def track_signal_generated(strategy: str, symbol: str):
    """Track signal generation"""
    signals_generated_total.labels(strategy=strategy, symbol=symbol).inc()


def track_signal_executed(strategy: str, symbol: str, side: int):
    """Track signal execution"""
    side_label = "long" if side > 0 else "short" if side < 0 else "flat"
    signals_executed_total.labels(
        strategy=strategy,
        symbol=symbol,
        side=side_label
    ).inc()


def track_signal_blocked(strategy: str, symbol: str, reason: str):
    """Track signal blocked by policy"""
    signals_blocked_total.labels(
        strategy=strategy,
        symbol=symbol,
        reason=reason
    ).inc()


def track_trade_completed(
    strategy: str,
    symbol: str,
    pnl: float,
    duration_seconds: float,
    outcome: str
):
    """Track completed trade"""
    trades_total.labels(
        strategy=strategy,
        symbol=symbol,
        outcome=outcome
    ).inc()
    
    trade_pnl_usd.labels(strategy=strategy, symbol=symbol).observe(pnl)
    trade_duration_seconds.labels(strategy=strategy, symbol=symbol).observe(duration_seconds)


def update_portfolio_metrics(
    equity: float,
    cash: float,
    unrealized_pnl: float,
    realized_pnl: float,
    exposure_pct: float,
    num_positions: int,
    daily_pnl: float,
    daily_return_pct: float,
    drawdown_pct: float
):
    """Update portfolio metrics"""
    portfolio_equity_usd.set(equity)
    portfolio_cash_usd.set(cash)
    portfolio_unrealized_pnl_usd.set(unrealized_pnl)
    portfolio_realized_pnl_usd.set(realized_pnl)
    portfolio_exposure_pct.set(exposure_pct)
    portfolio_num_positions.set(num_positions)
    portfolio_daily_pnl_usd.set(daily_pnl)
    portfolio_daily_return_pct.set(daily_return_pct)
    portfolio_drawdown_pct.set(drawdown_pct)


def track_ml_inference(model_version: str, confidence: float, prediction: int):
    """Track ML model inference"""
    start = time.time()
    
    # Track prediction
    prediction_class = "positive" if prediction > 0 else "negative"
    ml_predictions_total.labels(
        model_version=model_version,
        prediction_class=prediction_class
    ).inc()
    
    # Track confidence
    ml_model_confidence.labels(model_version=model_version).observe(confidence)
    
    # Track latency
    latency = time.time() - start
    ml_inference_latency_seconds.labels(model_version=model_version).observe(latency)


def update_policy_metrics(
    kill_switch_active: bool,
    daily_trades: int,
    daily_loss_limit_remaining: float
):
    """Update policy engine metrics"""
    policy_kill_switch_active.set(1 if kill_switch_active else 0)
    policy_daily_trades_count.set(daily_trades)
    policy_daily_loss_limit_remaining_usd.set(daily_loss_limit_remaining)


# Decorator for tracking function latency
def track_latency(metric: Histogram):
    """Decorator to track function latency"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                metric.observe(time.time() - start)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                metric.observe(time.time() - start)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(REGISTRY)


def set_build_info(version: str, commit: str, branch: str):
    """Set build information"""
    build_info.info({
        "version": version,
        "commit": commit,
        "branch": branch
    })


if __name__ == "__main__":
    # Example usage
    set_build_info("1.0.0", "abc123", "main")
    
    # Track some metrics
    track_signal_generated("lse", "BTCUSDT")
    track_signal_executed("lse", "BTCUSDT", 1)
    track_trade_completed("lse", "BTCUSDT", 15.5, 120, "win")
    
    update_portfolio_metrics(
        equity=10150.0,
        cash=5000.0,
        unrealized_pnl=50.0,
        realized_pnl=150.0,
        exposure_pct=0.45,
        num_positions=3,
        daily_pnl=150.0,
        daily_return_pct=1.5,
        drawdown_pct=0.5
    )
    
    # Get metrics
    metrics_output = get_metrics()
    print(metrics_output.decode('utf-8'))
