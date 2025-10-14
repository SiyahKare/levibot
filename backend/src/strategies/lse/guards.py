"""
LSE Guards Module
Pre-trade validation filters
"""

from dataclasses import dataclass


@dataclass
class GuardResult:
    """Guard check result"""

    passed: bool
    reason: str = ""


class TradingGuards:
    """
    Pre-trade guard checks
    All guards must pass for trade execution
    """

    def __init__(self, config: dict):
        self.min_vol_bps = config.get("min_vol_bps", 5)
        self.max_spread_bps = config.get("max_spread_bps", 1)
        self.max_latency_ms = config.get("max_latency_ms", 120)
        self.max_daily_dd = config.get("max_daily_dd", 0.02)
        self.max_open_trades = config.get("max_open_trades", 1)

    def check_volatility(self, vol_bps: float) -> GuardResult:
        """Check if volatility is sufficient"""
        if vol_bps < self.min_vol_bps:
            return GuardResult(
                passed=False, reason=f"Vol too low: {vol_bps:.2f} < {self.min_vol_bps}"
            )
        return GuardResult(passed=True)

    def check_spread(self, spread_bps: float) -> GuardResult:
        """Check if spread is acceptable"""
        if spread_bps > self.max_spread_bps:
            return GuardResult(
                passed=False,
                reason=f"Spread too wide: {spread_bps:.2f} > {self.max_spread_bps}",
            )
        return GuardResult(passed=True)

    def check_latency(self, latency_ms: float) -> GuardResult:
        """Check if latency is acceptable"""
        if latency_ms > self.max_latency_ms:
            return GuardResult(
                passed=False,
                reason=f"Latency too high: {latency_ms:.1f} > {self.max_latency_ms}",
            )
        return GuardResult(passed=True)

    def check_drawdown(self, current_dd: float) -> GuardResult:
        """Check if daily drawdown is within limit"""
        if current_dd < -self.max_daily_dd:
            return GuardResult(
                passed=False,
                reason=f"DD limit: {current_dd:.2%} < -{self.max_daily_dd:.2%}",
            )
        return GuardResult(passed=True)

    def check_position_limit(self, open_count: int) -> GuardResult:
        """Check if max open trades limit is reached"""
        if open_count >= self.max_open_trades:
            return GuardResult(
                passed=False,
                reason=f"Max positions: {open_count} >= {self.max_open_trades}",
            )
        return GuardResult(passed=True)

    def check_all(
        self,
        vol_bps: float,
        spread_bps: float,
        latency_ms: float,
        current_dd: float,
        open_count: int,
    ) -> GuardResult:
        """
        Run all guard checks
        Returns first failure or success if all pass
        """
        checks = [
            self.check_volatility(vol_bps),
            self.check_spread(spread_bps),
            self.check_latency(latency_ms),
            self.check_drawdown(current_dd),
            self.check_position_limit(open_count),
        ]

        for result in checks:
            if not result.passed:
                return result

        return GuardResult(passed=True, reason="All guards passed")

    def status(
        self,
        vol_bps: float,
        spread_bps: float,
        latency_ms: float,
        current_dd: float,
        open_count: int,
    ) -> dict:
        """
        Get detailed status of all guards (for UI display)
        """
        return {
            "vol_ok": self.check_volatility(vol_bps).passed,
            "spread_ok": self.check_spread(spread_bps).passed,
            "latency_ok": self.check_latency(latency_ms).passed,
            "risk_ok": (
                self.check_drawdown(current_dd).passed
                and self.check_position_limit(open_count).passed
            ),
        }
