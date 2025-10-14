from __future__ import annotations

import os
import time
from dataclasses import dataclass

import ccxt

from ..app import config as app_cfg
from ..exec.sizing import RiskParams, size_with_pulse
from ..infra.logger import JsonlEventLogger
from .precision import MarketMeta, passes_min_notional, quantize_amount, quantize_price


@dataclass
class OrderResult:
    id: str
    status: str
    price: float | None = None


class ExchangeRouter:
    def __init__(self, exchange: str = "bybit", testnet: bool = True) -> None:
        self.exchange_name = exchange
        self.testnet = testnet
        self.client = self._make_client(exchange, testnet)
        self.logger = JsonlEventLogger()
        # Load markets for precision/lot sizing helpers
        try:
            self.client.load_markets()
        except Exception:
            pass

    def _make_client(self, exchange: str, testnet: bool):
        if exchange == "bybit":
            api_key = os.getenv("LEVI_ONUR_BYBIT_KEY") or os.getenv("BYBIT_API_KEY", "")
            api_secret = os.getenv("LEVI_ONUR_BYBIT_SECRET") or os.getenv(
                "BYBIT_API_SECRET", ""
            )
            options = {"adjustForTimeDifference": True}
            if testnet:
                options["urls"] = {
                    "api": {
                        "public": "https://api-testnet.bybit.com",
                        "private": "https://api-testnet.bybit.com",
                    }
                }
            # Avoid private fetch_currencies during load_markets
            options.update({"defaultType": "swap", "fetchCurrencies": False})
            client = ccxt.bybit(
                {"apiKey": api_key, "secret": api_secret, "options": options}
            )
            client.set_sandbox_mode(testnet)
            return client
        if exchange == "binance":
            api_key = os.getenv("LEVI_ONUR_BINANCE_KEY") or os.getenv(
                "BINANCE_API_KEY", ""
            )
            api_secret = os.getenv("LEVI_ONUR_BINANCE_SECRET") or os.getenv(
                "BINANCE_API_SECRET", ""
            )
            client = ccxt.binance(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "options": {"defaultType": "future"},
                }
            )
            if testnet:
                # Override futures testnet endpoints
                try:
                    client.urls["api"][
                        "fapiPublic"
                    ] = "https://testnet.binancefuture.com/fapi/v1"
                    client.urls["api"][
                        "fapiPrivate"
                    ] = "https://testnet.binancefuture.com/fapi/v1"
                    client.urls["api"][
                        "fapiPrivateV2"
                    ] = "https://testnet.binancefuture.com/fapi/v2"
                except Exception:
                    pass
            client.set_sandbox_mode(testnet)
            return client
        raise ValueError(f"Unsupported exchange {exchange}")

    def norm_ccxt_symbol(self, sym: str) -> str:
        ex = self.client
        if ex.id == "bybit":
            base, quote = sym[:-4], sym[-4:]
            return f"{base}/{quote}:USDT"
        if ex.id == "binance":
            base, quote = sym[:-4], sym[-4:]
            return f"{base}/{quote}"
        return sym

    def _norm_order_inputs(
        self, symbol: str, side: str, qty: float, price: float
    ) -> tuple[float, float]:
        markets = getattr(self.client, "markets", None)
        if not markets or symbol not in markets:
            # No markets info available; fallback to raw
            return qty, price
        meta = MarketMeta(markets[symbol])
        qp = quantize_price(price, meta)
        qa = quantize_amount(qty, meta)
        try:
            if not passes_min_notional(qp, qa, meta):
                return qty, price
        except Exception:
            return qty, price
        return qa, qp

    def place_oco(
        self, symbol: str, side: str, amount: float, entry: float, tp: float, sl: float
    ) -> OrderResult:
        # Software OCO: place entry (post-only preferred), then arm TP/SL peers
        qa, qp = self._norm_order_inputs(symbol, side, amount, entry)
        params = {"timeInForce": "PO"}
        try:
            entry_order = self.client.create_order(
                symbol, "limit", side, qa, qp, params
            )
        except ccxt.InvalidOrder:
            # fallback to simple TWAP of 3 parts
            part = qa / 3
            entry_order = None
            for _ in range(3):
                entry_order = self.client.create_order(symbol, "limit", side, part, qp)
                time.sleep(1.0)
        pos_side = "long" if side.lower() == "buy" else "short"
        hedge_side = "sell" if pos_side == "long" else "buy"
        tp_order = self.client.create_order(
            symbol, "limit", hedge_side, qa, tp, {"reduceOnly": True}
        )
        sl_order = self.client.create_order(
            symbol, "stop", hedge_side, qa, None, {"stopPrice": sl, "reduceOnly": True}
        )
        self.logger.write(
            "OCO_ARMED", {"symbol": symbol, "tp": tp, "sl": sl, "qty": amount}
        )
        return OrderResult(
            id=str(entry_order.get("id") if entry_order else "entry_twap"),
            status="placed",
            price=entry,
        )

    # Example entry helper: open using sizing with pulse
    def open_with_sizing(
        self,
        ccxt_symbol: str,
        side: str,
        entry: float,
        tp: float,
        sl: float,
        mark: float,
        pulse_factor: float,
        risk_cfg: dict,
    ) -> dict:
        markets = getattr(self.client, "markets", None) or {}
        meta = MarketMeta(markets.get(ccxt_symbol, {}))
        rp = RiskParams(
            equity_usd=float(risk_cfg.get("equity_usd", 1000.0)),
            risk_per_trade=float(risk_cfg.get("risk_per_trade_pct", 0.5)) / 100.0,
            max_leverage=float(risk_cfg.get("max_leverage", 2)),
            max_pos_notional_pct=(
                float(risk_cfg.get("max_pos_notional_pct")) / 100.0
                if risk_cfg.get("max_pos_notional_pct") is not None
                else None
            ),
            max_pos_usd=(
                float(risk_cfg.get("max_pos_usd"))
                if risk_cfg.get("max_pos_usd") is not None
                else None
            ),
            hard_cap=float(
                app_cfg.load_features_config()
                .get("telegram", {})
                .get("evaluation", {})
                .get("pulse", {})
                .get("hard_cap", 1.5)
            ),
        )
        sizing = size_with_pulse(
            ccxt_symbol.replace("/", "").replace(":USDT", ""),
            side,
            entry,
            sl,
            None,
            pulse_factor,
            rp,
            meta,
            mark,
        )
        qty = max(1e-9, float(sizing.get("qty", 0.0)))
        # Place entry and OCO
        order = self.place_oco(ccxt_symbol, side, qty, entry, tp, sl)
        return {"order": order.__dict__, "sizing": sizing}

    def cancel_all(self, symbol: str) -> None:
        # Placeholder cancel implementation
        try:
            self.client.cancel_all_orders(symbol)
        except Exception:
            pass
        return None
