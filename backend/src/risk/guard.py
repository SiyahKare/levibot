from __future__ import annotations

import time
from ..infra.metrics import levibot_risk_used_ratio
from ..infra.logger import JsonlEventLogger


class KillSwitch:
    def __init__(self, max_daily_loss_pct: float):
        self.max_dd_pct = max_daily_loss_pct
        self.day = time.strftime("%Y-%m-%d")
        self.realized_pnl = 0.0
        self.equity_start = None
        self.tripped = False
        self.logger = JsonlEventLogger()

    def reset_if_new_day(self) -> None:
        today = time.strftime("%Y-%m-%d")
        if today != self.day:
            self.day = today
            self.realized_pnl = 0.0
            self.tripped = False

    def feed_equity_start(self, equity: float) -> None:
        if self.equity_start is None:
            self.equity_start = equity

    def feed_realized(self, pnl_delta: float, user: str) -> None:
        self.reset_if_new_day()
        self.realized_pnl += pnl_delta
        used = 0.0
        if self.equity_start:
            used = max(0.0, -self.realized_pnl) / (self.equity_start * (self.max_dd_pct / 100.0))
        levibot_risk_used_ratio.labels(user=user).set(min(1.0, used))
        if used >= 1.0 and not self.tripped:
            self.tripped = True
            self.logger.write("KILL_SWITCH", {"reason": "daily_dd", "used": used})

    def pre_trade_check(self) -> None:
        self.reset_if_new_day()
        if self.tripped:
            raise RuntimeError("KillSwitch: daily drawdown reached")


KS_REGISTRY: dict[str, KillSwitch] = {}


def get_ks(user: str, max_dd_pct: float) -> KillSwitch:
    ks = KS_REGISTRY.get(user)
    if not ks:
        ks = KillSwitch(max_dd_pct)
        KS_REGISTRY[user] = ks
    return ks




