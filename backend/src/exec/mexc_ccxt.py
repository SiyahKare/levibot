"""
MEXC Exchange Adapter (CCXT-based)

Spot trading via MEXC API with full risk, rate-limiting, and metrics integration.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import ccxt  # type: ignore
except ImportError:
    ccxt = None

from ..core.risk import RiskConfig, RiskEngine, clamp_notional, derive_sl_tp
from ..infra.logger import log_event

# from ..infra.metrics import levibot_exec_orders_total  # TODO: Add this metric
from .types import PaperOrderResult

# Global risk engine instance
_risk = RiskEngine(RiskConfig())


class MexcExecutor:
    """
    MEXC Spot executor using CCXT.

    Features:
    - Market/limit order placement
    - Precision & min notional handling
    - Rate limiting via CCXT throttle
    - Metrics & event logging
    - TP/SL derivation from FE hints
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        sandbox: bool = False,
        recv_window_ms: int = 5000,
        rate_limit_ms: int = 50,
    ):
        if ccxt is None:
            raise ImportError("ccxt not installed - run: pip install ccxt")

        self.exchange_name = "mexc"
        self.client = ccxt.mexc(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {"recvWindow": recv_window_ms},
                "timeout": 15000,
            }
        )

        # MEXC spot sandbox support is limited; use with caution
        if sandbox:
            try:
                self.client.set_sandbox_mode(True)
                log_event(
                    "MEXC_SANDBOX_ENABLED",
                    {"warning": "MEXC sandbox may have limited support"},
                )
            except Exception as e:
                log_event("MEXC_SANDBOX_FAILED", {"error": str(e)})

        # Custom throttle (ccxt ms between requests)
        self.client.rateLimit = rate_limit_ms
        self.markets: dict[str, Any] | None = None

        log_event(
            "MEXC_INIT",
            {
                "sandbox": sandbox,
                "recv_window_ms": recv_window_ms,
                "rate_limit_ms": rate_limit_ms,
            },
        )

    def load_markets(self) -> dict[str, Any]:
        """Load and cache market metadata."""
        if self.markets is None:
            try:
                self.markets = self.client.load_markets()
                log_event("MEXC_MARKETS_LOADED", {"count": len(self.markets)})
            except Exception as e:
                log_event("MEXC_MARKETS_FAILED", {"error": str(e)})
                raise
        return self.markets

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format.

        Examples:
        - "BTCUSDT" -> "BTC/USDT"
        - "BTC/USDT" -> "BTC/USDT"
        """
        markets = self.load_markets()
        s = symbol.upper()

        # Already normalized
        if s in markets:
            return s

        # Try common patterns
        if s.endswith("USDT") and "/" not in s:
            guess = s[:-4] + "/USDT"
            if guess in markets:
                return guess

        if s.endswith("USDC") and "/" not in s:
            guess = s[:-4] + "/USDC"
            if guess in markets:
                return guess

        raise ValueError(
            f"Unknown symbol for MEXC: {symbol}. Available: {list(markets.keys())[:10]}..."
        )

    def get_market_info(self, symbol: str) -> dict[str, Any]:
        """Get market metadata (precision, limits, etc.)"""
        norm_sym = self.normalize_symbol(symbol)
        markets = self.load_markets()
        return markets[norm_sym]

    def fetch_ticker_price(self, symbol: str) -> float:
        """Fetch current market price."""
        norm_sym = self.normalize_symbol(symbol)
        try:
            ticker = self.client.fetch_ticker(norm_sym)
            # Try different price fields
            for key in ("last", "close", "bid", "ask"):
                price = ticker.get(key)
                if isinstance(price, int | float) and price > 0:
                    return float(price)
            raise ValueError(f"No valid price in ticker: {ticker}")
        except Exception as e:
            log_event("MEXC_TICKER_FAILED", {"symbol": symbol, "error": str(e)})
            raise

    def clamp_quantity(self, symbol: str, quantity: float) -> float:
        """Clamp quantity to market precision and min/max limits."""
        market = self.get_market_info(symbol)
        limits = market.get("limits", {})
        precision = market.get("precision", {})

        # Apply min/max limits
        min_amt = limits.get("amount", {}).get("min", 0)
        max_amt = limits.get("amount", {}).get("max", float("inf"))
        qty = max(min_amt, min(quantity, max_amt))

        # Apply precision (step size)
        prec_amt = precision.get("amount")
        if prec_amt is not None:
            step = 10 ** (-prec_amt)
            qty = (int(qty / step)) * step

        return max(qty, min_amt)  # Ensure not below minimum

    def place_market_order(
        self,
        symbol: str,
        side: str,  # "buy" | "sell"
        notional_usd: float,
        trace_id: str | None = None,
        fe: dict | None = None,
    ) -> PaperOrderResult:
        """
        Place market order with risk checks, TP/SL derivation, and metrics.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT" or "BTC/USDT")
            side: "buy" or "sell"
            notional_usd: Order size in USD
            trace_id: Optional trace ID for logging
            fe: Optional frontend hints (tp, sl)

        Returns:
            PaperOrderResult with execution details
        """
        try:
            norm_sym = self.normalize_symbol(symbol)
            base_sym = symbol.replace("/", "")

            # Notional clamp
            notional = clamp_notional(notional_usd)

            # Risk check: cooldown + max notional
            ok, reason = _risk.allow(base_sym, notional)
            if not ok:
                log_event(
                    "ORDER_BLOCKED",
                    {
                        "reason": reason,
                        "symbol": norm_sym,
                        "side": side,
                        "notional": notional,
                    },
                    symbol=base_sym,
                    trace_id=trace_id,
                )
                # levibot_exec_orders_total.labels(exchange="mexc", status="blocked", type="market").inc()
                return PaperOrderResult(
                    ok=False,
                    symbol=norm_sym,
                    side=side,
                    qty=0.0,
                    price=0.0,
                    filled=False,
                    pnl_usd=0.0,
                )

            # Fetch current price
            price = self.fetch_ticker_price(symbol)

            # Calculate quantity
            raw_qty = notional / price
            quantity = self.clamp_quantity(symbol, raw_qty)

            log_event(
                "ORDER_NEW",
                {
                    "exchange": "mexc",
                    "symbol": norm_sym,
                    "side": side,
                    "qty": quantity,
                    "price": price,
                    "notional": notional,
                },
                symbol=base_sym,
                trace_id=trace_id,
            )

            # Place order via CCXT
            order = self.client.create_order(
                symbol=norm_sym,
                type="market",
                side=side.lower(),
                amount=quantity,
            )

            filled_qty = float(order.get("filled", quantity))
            avg_price = float(order.get("average", price))

            log_event(
                "ORDER_FILLED",
                {
                    "exchange": "mexc",
                    "symbol": norm_sym,
                    "side": side,
                    "qty": filled_qty,
                    "price": avg_price,
                    "order_id": order.get("id"),
                },
                symbol=base_sym,
                trace_id=trace_id,
            )

            # TP/SL derivation
            tp_hint = (fe or {}).get("tp")
            sl_hint = (fe or {}).get("sl")

            # Estimate ATR from price (1% for now; could enhance with real ATR)
            atr = abs(avg_price * 0.01)
            sl, tp, meta = derive_sl_tp(side, avg_price, atr, tp_hint, sl_hint)

            log_event(
                "RISK_SLTP",
                {
                    "sl": sl,
                    "tp": tp,
                    "atr": meta.get("atr"),
                    "policy": meta.get("policy"),
                    "source": meta.get("source"),
                },
                symbol=base_sym,
                trace_id=trace_id,
            )

            # Record risk cooldown
            _risk.record(base_sym)

            # Metrics
            # levibot_exec_orders_total.labels(exchange="mexc", status="ok", type="market").inc()

            return PaperOrderResult(
                ok=True,
                symbol=norm_sym,
                side=side,
                qty=filled_qty,
                price=avg_price,
                filled=True,
                pnl_usd=0.0,  # Real PnL tracking would require position management
            )

        except Exception as e:
            log_event(
                "ORDER_ERROR",
                {"exchange": "mexc", "symbol": symbol, "side": side, "error": str(e)},
                symbol=symbol.replace("/", ""),
                trace_id=trace_id,
            )
            # levibot_exec_orders_total.labels(exchange="mexc", status="error", type="market").inc()

            return PaperOrderResult(
                ok=False,
                symbol=symbol,
                side=side,
                qty=0.0,
                price=0.0,
                filled=False,
                pnl_usd=0.0,
            )

    def get_balance(self) -> dict[str, Any]:
        """Fetch account balance."""
        try:
            balance = self.client.fetch_balance()
            return {"ok": True, "balance": balance}
        except Exception as e:
            log_event("MEXC_BALANCE_FAILED", {"error": str(e)})
            return {"ok": False, "error": str(e)}

    def health_check(self) -> dict[str, Any]:
        """Health check: load markets and verify API connectivity."""
        try:
            markets = self.load_markets()
            return {"ok": True, "exchange": "mexc", "markets_count": len(markets)}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def create_mexc_executor() -> MexcExecutor | None:
    """
    Factory function to create MEXC executor from environment variables.

    Required ENV:
    - MEXC_API_KEY
    - MEXC_API_SECRET

    Optional ENV:
    - MEXC_ENABLE (default: true)
    - MEXC_SANDBOX (default: false)
    - MEXC_RECV_WINDOW_MS (default: 5000)
    - MEXC_RATE_LIMIT_MS (default: 50)
    """
    if os.getenv("MEXC_ENABLE", "true").lower() != "true":
        return None

    api_key = os.getenv("MEXC_API_KEY", "")
    api_secret = os.getenv("MEXC_API_SECRET", "")

    if not api_key or not api_secret:
        log_event(
            "MEXC_CONFIG_MISSING",
            {"warning": "MEXC_API_KEY or MEXC_API_SECRET not set"},
        )
        return None

    try:
        return MexcExecutor(
            api_key=api_key,
            api_secret=api_secret,
            sandbox=os.getenv("MEXC_SANDBOX", "false").lower() == "true",
            recv_window_ms=int(os.getenv("MEXC_RECV_WINDOW_MS", "5000")),
            rate_limit_ms=int(os.getenv("MEXC_RATE_LIMIT_MS", "50")),
        )
    except Exception as e:
        log_event("MEXC_INIT_FAILED", {"error": str(e)})
        return None
