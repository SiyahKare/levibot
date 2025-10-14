"""Order execution with risk checks, kill switch, and Prometheus metrics."""

from __future__ import annotations

import asyncio
from typing import Any

from ..risk.manager import RiskManager
from .mexc_orders import MexcOrders
from .portfolio import Portfolio


class OrderExecutor:
    """
    Order executor with integrated risk checks and kill switch.

    Features:
        - Risk pre-checks before order placement
        - Manual and automatic kill switch
        - Exposure limit enforcement
        - Prometheus metrics tracking
        - Global stop integration
    """

    def __init__(
        self,
        risk: RiskManager,
        broker: MexcOrders,
        portfolio: Portfolio,
        kill_threshold_usd: float = 0.0,
    ):
        """
        Initialize order executor.

        Args:
            risk: RiskManager instance
            broker: MexcOrders adapter
            portfolio: Portfolio state manager
            kill_threshold_usd: Max position notional (0 = disabled)
        """
        self.risk = risk
        self.broker = broker
        self.portfolio = portfolio
        self.kill_on = False
        self.kill_threshold_usd = kill_threshold_usd

    async def maybe_kill(self, reason: str) -> bool:
        """
        Check kill switch conditions.

        Args:
            reason: Kill reason for logging

        Returns:
            True if kill switch is engaged
        """
        if self.kill_on:
            # TODO: Prometheus metric
            # kill_switch_flag.labels(reason).set(1)
            return True

        # Auto-kill: global stop triggered
        if self.risk.is_global_stop():
            self.kill_on = True
            # TODO: kill_switch_flag.labels("global_stop").set(1)
            return True

        return False

    async def execute_signal(
        self, symbol: str, side: str, qty: float, last_px: float
    ) -> dict[str, Any]:
        """
        Execute trading signal with risk checks.

        Flow:
            1. Check kill switch
            2. Check exposure limits
            3. Check risk manager constraints
            4. Place order via broker

        Args:
            symbol: Trading symbol
            side: "BUY" or "SELL"
            qty: Order quantity
            last_px: Current market price

        Returns:
            Execution result dict with keys: ok, reason, orderId (if ok=True)
        """
        # Kill switch check
        if await self.maybe_kill("manual_or_auto"):
            return {"ok": False, "reason": "kill_switch"}

        # Exposure limit check
        if self.kill_threshold_usd > 0:
            exposure = self.portfolio.exposure_notional(symbol, last_px)
            if exposure > self.kill_threshold_usd:
                self.kill_on = True
                # TODO: kill_switch_flag.labels("exposure_limit").set(1)
                return {"ok": False, "reason": "exposure_limit"}

        # Risk manager check
        if not self.risk.can_open_new_position(symbol):
            return {"ok": False, "reason": "risk_block"}

        # Place order
        try:
            resp = await self.broker.place_order(symbol, side, qty)
            # TODO: orders_total.labels("NEW", symbol, side).inc()
            return resp
        except Exception as e:
            # TODO: orders_total.labels("ERROR", symbol, side).inc()
            return {"ok": False, "reason": "exception", "error": str(e)}

    def engage_kill_switch(self, reason: str = "manual"):
        """
        Manually engage kill switch.

        Args:
            reason: Reason for engagement
        """
        self.kill_on = True
        # TODO: kill_switch_flag.labels(reason).set(1)

    def disengage_kill_switch(self):
        """Manually disengage kill switch."""
        self.kill_on = False
        # TODO: kill_switch_flag.labels("reset").set(0)

