"""
Policy Engine - Risk management, cooldown, and signal filtering
Enterprise-grade guardrails for production trading
"""

import time
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as aioredis


class PolicyDecision(Enum):
    """Policy decision types"""

    ALLOW = "allow"
    BLOCK = "block"
    THROTTLE = "throttle"
    REDUCE = "reduce"


@dataclass
class SignalDecision:
    """Signal decision with policy metadata"""

    symbol: str
    side: int  # 1=long, -1=short, 0=flat
    confidence: float
    strategy: str
    decision: PolicyDecision
    reason: str
    metadata: dict


@dataclass
class RiskLimits:
    """Risk limit configuration"""

    # Per-trade limits
    max_position_size_usd: float = 1000.0
    max_leverage: float = 3.0
    min_confidence: float = 0.55

    # Daily limits
    max_daily_trades: int = 50
    max_daily_loss_usd: float = 500.0
    max_daily_dd_pct: float = 0.03  # 3%

    # Cooldown
    cooldown_after_loss_sec: int = 300  # 5 minutes
    cooldown_after_sl_sec: int = 600  # 10 minutes
    min_time_between_trades_sec: int = 30

    # Exposure
    max_total_exposure_pct: float = 0.5  # 50% of equity
    max_correlated_exposure_pct: float = 0.3  # 30% in correlated assets

    # Filters
    max_spread_bps: float = 20.0
    min_volume_24h_usd: float = 1_000_000.0
    max_slippage_bps: float = 10.0


class PolicyEngine:
    """
    Policy engine for signal filtering and risk management

    Features:
    - Confidence threshold filtering
    - Cooldown management (per-symbol and global)
    - Daily loss limits
    - Position size limits
    - Exposure management
    - Circuit breaker integration
    """

    def __init__(self, redis_url: str, limits: RiskLimits | None = None):
        self.redis_url = redis_url
        self.limits = limits or RiskLimits()
        self._client: aioredis.Redis | None = None

        # In-memory state (backed by Redis)
        self._daily_trades = 0
        self._daily_pnl = 0.0
        self._equity = 10000.0  # Initial equity
        self._positions: dict[str, float] = {}  # symbol -> position_size_usd
        self._kill_switch_active = False

    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self._load_state()

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    async def _load_state(self):
        """Load state from Redis"""
        if not self._client:
            return

        # Load daily stats
        self._daily_trades = int(await self._client.get("policy:daily_trades") or 0)
        self._daily_pnl = float(await self._client.get("policy:daily_pnl") or 0.0)
        self._equity = float(await self._client.get("policy:equity") or 10000.0)

        # Load kill switch state
        self._kill_switch_active = bool(
            await self._client.get("policy:kill_switch") == "1"
        )

    async def _save_state(self):
        """Save state to Redis"""
        if not self._client:
            return

        await self._client.set("policy:daily_trades", self._daily_trades)
        await self._client.set("policy:daily_pnl", self._daily_pnl)
        await self._client.set("policy:equity", self._equity)

    async def evaluate_signal(
        self,
        symbol: str,
        side: int,
        confidence: float,
        strategy: str,
        metadata: dict | None = None,
    ) -> SignalDecision:
        """
        Evaluate signal against policy rules

        Args:
            symbol: Trading symbol
            side: Signal direction (1=long, -1=short, 0=flat)
            confidence: Signal confidence (0-1)
            strategy: Strategy name
            metadata: Additional signal metadata

        Returns:
            SignalDecision with policy verdict
        """
        await self.connect()
        metadata = metadata or {}

        # Kill switch check (highest priority)
        if self._kill_switch_active:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason="kill_switch_active",
                metadata=metadata,
            )

        # Confidence filter
        if confidence < self.limits.min_confidence:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"low_confidence ({confidence:.3f} < {self.limits.min_confidence})",
                metadata=metadata,
            )

        # Daily trade limit
        if self._daily_trades >= self.limits.max_daily_trades:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"daily_trade_limit ({self._daily_trades}/{self.limits.max_daily_trades})",
                metadata=metadata,
            )

        # Daily loss limit
        if self._daily_pnl < -self.limits.max_daily_loss_usd:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"daily_loss_limit (${self._daily_pnl:.2f})",
                metadata=metadata,
            )

        # Daily drawdown limit
        daily_dd_pct = abs(self._daily_pnl) / self._equity if self._equity > 0 else 0
        if daily_dd_pct > self.limits.max_daily_dd_pct:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"daily_dd_limit ({daily_dd_pct:.2%} > {self.limits.max_daily_dd_pct:.2%})",
                metadata=metadata,
            )

        # Cooldown check (per-symbol)
        cooldown_key = f"policy:cooldown:{symbol}"
        cooldown_until = await self._client.get(cooldown_key)
        if cooldown_until:
            remaining = float(cooldown_until) - time.time()
            if remaining > 0:
                return SignalDecision(
                    symbol=symbol,
                    side=0,
                    confidence=confidence,
                    strategy=strategy,
                    decision=PolicyDecision.BLOCK,
                    reason=f"cooldown ({remaining:.0f}s remaining)",
                    metadata=metadata,
                )

        # Global cooldown (time between any trades)
        global_cooldown_key = "policy:cooldown:global"
        global_cooldown = await self._client.get(global_cooldown_key)
        if global_cooldown:
            remaining = float(global_cooldown) - time.time()
            if remaining > 0:
                return SignalDecision(
                    symbol=symbol,
                    side=0,
                    confidence=confidence,
                    strategy=strategy,
                    decision=PolicyDecision.THROTTLE,
                    reason=f"global_cooldown ({remaining:.0f}s)",
                    metadata=metadata,
                )

        # Exposure check
        total_exposure = sum(abs(pos) for pos in self._positions.values())
        exposure_pct = total_exposure / self._equity if self._equity > 0 else 0

        if exposure_pct > self.limits.max_total_exposure_pct:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"max_exposure ({exposure_pct:.1%} > {self.limits.max_total_exposure_pct:.1%})",
                metadata=metadata,
            )

        # Spread filter
        spread_bps = metadata.get("spread_bps", 0)
        if spread_bps > self.limits.max_spread_bps:
            return SignalDecision(
                symbol=symbol,
                side=0,
                confidence=confidence,
                strategy=strategy,
                decision=PolicyDecision.BLOCK,
                reason=f"wide_spread ({spread_bps:.1f} > {self.limits.max_spread_bps:.1f} bps)",
                metadata=metadata,
            )

        # All checks passed
        return SignalDecision(
            symbol=symbol,
            side=side,
            confidence=confidence,
            strategy=strategy,
            decision=PolicyDecision.ALLOW,
            reason="all_checks_passed",
            metadata=metadata,
        )

    async def record_trade(self, symbol: str, pnl: float, hit_sl: bool = False):
        """
        Record trade execution and update state

        Args:
            symbol: Trading symbol
            pnl: Trade PnL (USD)
            hit_sl: Whether stop-loss was hit
        """
        await self.connect()

        # Update daily stats
        self._daily_trades += 1
        self._daily_pnl += pnl
        await self._save_state()

        # Set cooldown
        cooldown_duration = (
            self.limits.cooldown_after_sl_sec
            if hit_sl
            else (
                self.limits.cooldown_after_loss_sec
                if pnl < 0
                else self.limits.min_time_between_trades_sec
            )
        )

        cooldown_until = time.time() + cooldown_duration
        await self._client.set(
            f"policy:cooldown:{symbol}", cooldown_until, ex=cooldown_duration
        )

        # Set global cooldown
        await self._client.set(
            "policy:cooldown:global",
            time.time() + self.limits.min_time_between_trades_sec,
            ex=self.limits.min_time_between_trades_sec,
        )

    async def update_position(self, symbol: str, position_size_usd: float):
        """Update position tracking"""
        self._positions[symbol] = position_size_usd

        if position_size_usd == 0 and symbol in self._positions:
            del self._positions[symbol]

    async def update_equity(self, equity: float):
        """Update equity tracking"""
        self._equity = equity
        await self._save_state()

    async def reset_daily_stats(self):
        """Reset daily statistics (called at EOD)"""
        await self.connect()

        self._daily_trades = 0
        self._daily_pnl = 0.0
        await self._save_state()

        print("✅ Daily stats reset")

    async def activate_kill_switch(self, reason: str = "manual"):
        """
        Activate kill switch (block all new trades)

        Args:
            reason: Reason for activation
        """
        await self.connect()

        self._kill_switch_active = True
        await self._client.set("policy:kill_switch", "1")
        await self._client.set("policy:kill_switch_reason", reason)

        print(f"🚨 KILL SWITCH ACTIVATED: {reason}")

    async def deactivate_kill_switch(self):
        """Deactivate kill switch"""
        await self.connect()

        self._kill_switch_active = False
        await self._client.set("policy:kill_switch", "0")

        print("✅ Kill switch deactivated")

    async def get_status(self) -> dict:
        """Get policy engine status"""
        await self.connect()

        total_exposure = sum(abs(pos) for pos in self._positions.values())
        exposure_pct = total_exposure / self._equity if self._equity > 0 else 0
        daily_dd_pct = abs(self._daily_pnl) / self._equity if self._equity > 0 else 0

        return {
            "kill_switch": self._kill_switch_active,
            "equity": self._equity,
            "daily_trades": self._daily_trades,
            "daily_pnl": self._daily_pnl,
            "daily_dd_pct": daily_dd_pct,
            "exposure_usd": total_exposure,
            "exposure_pct": exposure_pct,
            "num_positions": len(self._positions),
            "positions": self._positions.copy(),
            "limits": {
                "max_daily_trades": self.limits.max_daily_trades,
                "max_daily_loss": self.limits.max_daily_loss_usd,
                "max_daily_dd_pct": self.limits.max_daily_dd_pct,
                "max_exposure_pct": self.limits.max_total_exposure_pct,
            },
        }


# Singleton instance
_engine: PolicyEngine | None = None


def get_policy_engine(
    redis_url: str = "redis://localhost:6379/0", limits: RiskLimits | None = None
) -> PolicyEngine:
    """Get global policy engine instance"""
    global _engine
    if _engine is None:
        _engine = PolicyEngine(redis_url, limits)
    return _engine


if __name__ == "__main__":
    import asyncio

    async def test():
        engine = get_policy_engine()

        # Test signal evaluation
        decision = await engine.evaluate_signal(
            symbol="BTCUSDT",
            side=1,
            confidence=0.65,
            strategy="lse",
            metadata={"spread_bps": 2.5},
        )

        print(f"📊 Decision: {decision.decision.value}")
        print(f"   Reason: {decision.reason}")
        print(f"   Side: {decision.side}")

        # Get status
        status = await engine.get_status()
        print("\n📈 Status:")
        print(f"   Equity: ${status['equity']:.2f}")
        print(
            f"   Daily trades: {status['daily_trades']}/{status['limits']['max_daily_trades']}"
        )
        print(f"   Daily PnL: ${status['daily_pnl']:.2f}")
        print(f"   Exposure: {status['exposure_pct']:.1%}")

        await engine.disconnect()

    asyncio.run(test())
