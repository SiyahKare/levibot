from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskDecision:
    allow: bool
    reason: Optional[str] = None
    size_usd: Optional[float] = None
    leverage: Optional[int] = None


class RiskEngine:
    def __init__(self, equity_usd: float, risk_config: dict) -> None:
        self.equity_usd = equity_usd
        self.cfg = risk_config.get("global", {})

    def check_daily_dd(self, dd_pct: float) -> RiskDecision:
        if self.cfg.get("kill_switch_on_dd", True) and dd_pct >= self.cfg.get("daily_drawdown_stop_pct", 0.03):
            return RiskDecision(allow=False, reason="daily_dd_stop")
        return RiskDecision(allow=True)

    def position_size_by_atr(self, atr: float, price: float) -> float:
        risk_perc = float(self.cfg.get("risk_per_trade_pct", 0.005))
        risk_usd = self.equity_usd * risk_perc
        stop_mult = float(self.cfg.get("atr_sl_mult", 2.5))
        stop_usd = atr * stop_mult
        if stop_usd <= 0:
            return 0.0
        qty = risk_usd / stop_usd
        notional = qty * price
        max_lev = float(self.cfg.get("max_leverage", 5))
        max_notional = self.equity_usd * max_lev
        return float(min(notional, max_notional))


