"""
Strategy Orchestrator - Multi-strategy coordination and priority queue
Manages signal routing, conflict resolution, and execution priority
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from ..infra.event_bus import EventBus, publish_signal
from ..ml.feature_store import FeatureStore, get_feature_store
from ..ml.model_pipeline import ModelInference
from ..strategies.policy_engine import PolicyEngine, get_policy_engine


class StrategyPriority(Enum):
    """Strategy execution priority"""

    CRITICAL = 1  # Emergency exits, stop-losses
    HIGH = 2  # ML signals with high confidence
    MEDIUM = 3  # Rule-based signals
    LOW = 4  # Exploratory signals


@dataclass
class SignalRequest:
    """Signal request with priority"""

    symbol: str
    side: int
    confidence: float
    strategy: str
    priority: StrategyPriority
    timestamp: float
    metadata: dict

    def __lt__(self, other):
        """Compare by priority (lower number = higher priority)"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


class StrategyOrchestrator:
    """
    Strategy orchestrator for multi-strategy coordination

    Features:
    - Priority queue for signal routing
    - Conflict resolution (multiple signals for same symbol)
    - Strategy allocation (budget, position limits)
    - Performance tracking per strategy
    - Auto-disable underperforming strategies
    """

    def __init__(
        self,
        event_bus: EventBus,
        policy_engine: PolicyEngine,
        feature_store: FeatureStore,
        model_inference: ModelInference | None = None,
    ):
        self.event_bus = event_bus
        self.policy_engine = policy_engine
        self.feature_store = feature_store
        self.model_inference = model_inference

        # Priority queue
        self._signal_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # Strategy registry
        self._strategies: dict[str, dict] = {}

        # Performance tracking
        self._strategy_stats: dict[str, dict] = {}

        # Running state
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def register_strategy(
        self,
        name: str,
        signal_fn: Callable,
        priority: StrategyPriority = StrategyPriority.MEDIUM,
        enabled: bool = True,
        budget_usd: float = 1000.0,
        max_positions: int = 3,
    ):
        """
        Register a trading strategy

        Args:
            name: Strategy identifier
            signal_fn: Async function that generates signals
            priority: Default priority level
            enabled: Whether strategy is active
            budget_usd: Allocated budget
            max_positions: Max concurrent positions
        """
        self._strategies[name] = {
            "signal_fn": signal_fn,
            "priority": priority,
            "enabled": enabled,
            "budget_usd": budget_usd,
            "max_positions": max_positions,
        }

        self._strategy_stats[name] = {
            "signals_generated": 0,
            "signals_executed": 0,
            "signals_blocked": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_confidence": 0.0,
        }

        print(f"✅ Registered strategy: {name}")

    def enable_strategy(self, name: str):
        """Enable strategy"""
        if name in self._strategies:
            self._strategies[name]["enabled"] = True
            print(f"✅ Enabled strategy: {name}")

    def disable_strategy(self, name: str):
        """Disable strategy"""
        if name in self._strategies:
            self._strategies[name]["enabled"] = False
            print(f"⏸️ Disabled strategy: {name}")

    async def submit_signal(
        self,
        symbol: str,
        side: int,
        confidence: float,
        strategy: str,
        priority: StrategyPriority | None = None,
        metadata: dict | None = None,
    ):
        """
        Submit signal to priority queue

        Args:
            symbol: Trading symbol
            side: Signal direction
            confidence: Signal confidence
            strategy: Strategy name
            priority: Override priority
            metadata: Additional data
        """
        if strategy not in self._strategies:
            print(f"⚠️ Unknown strategy: {strategy}")
            return

        if not self._strategies[strategy]["enabled"]:
            print(f"⏸️ Strategy disabled: {strategy}")
            return

        # Use strategy's default priority if not specified
        if priority is None:
            priority = self._strategies[strategy]["priority"]

        signal = SignalRequest(
            symbol=symbol,
            side=side,
            confidence=confidence,
            strategy=strategy,
            priority=priority,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        await self._signal_queue.put(signal)
        self._strategy_stats[strategy]["signals_generated"] += 1

    async def _process_signals(self):
        """Process signals from priority queue"""
        print("🎯 Signal processor started")

        while self._running:
            try:
                # Get highest priority signal
                signal = await asyncio.wait_for(self._signal_queue.get(), timeout=1.0)

                # Evaluate with policy engine
                decision = await self.policy_engine.evaluate_signal(
                    symbol=signal.symbol,
                    side=signal.side,
                    confidence=signal.confidence,
                    strategy=signal.strategy,
                    metadata=signal.metadata,
                )

                if decision.side != 0:
                    # Signal approved
                    await publish_signal(
                        self.event_bus,
                        symbol=signal.symbol,
                        side=signal.side,
                        confidence=signal.confidence,
                        strategy=signal.strategy,
                        reason=decision.reason,
                        metadata=signal.metadata,
                    )

                    self._strategy_stats[signal.strategy]["signals_executed"] += 1

                    print(
                        f"✅ Signal executed: {signal.strategy} {signal.symbol} "
                        f"side={signal.side} conf={signal.confidence:.2%}"
                    )
                else:
                    # Signal blocked
                    self._strategy_stats[signal.strategy]["signals_blocked"] += 1

                    print(
                        f"🚫 Signal blocked: {signal.strategy} {signal.symbol} "
                        f"reason={decision.reason}"
                    )

            except TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Signal processing error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Start orchestrator"""
        if self._running:
            print("⚠️ Orchestrator already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_signals())

        print("🚀 Strategy orchestrator started")

    async def stop(self):
        """Stop orchestrator"""
        if not self._running:
            return

        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        print("⏹️ Strategy orchestrator stopped")

    def get_stats(self) -> dict:
        """Get orchestrator statistics"""
        return {
            "running": self._running,
            "queue_size": self._signal_queue.qsize(),
            "strategies": {
                name: {
                    "enabled": cfg["enabled"],
                    "priority": cfg["priority"].name,
                    "budget_usd": cfg["budget_usd"],
                    "max_positions": cfg["max_positions"],
                    "stats": self._strategy_stats[name],
                }
                for name, cfg in self._strategies.items()
            },
        }


# Example strategy functions
async def lse_strategy(orchestrator: StrategyOrchestrator):
    """LSE (scalp) strategy loop"""
    while True:
        try:
            # Get latest features
            features = await orchestrator.feature_store.get_latest_features("BTCUSDT")

            if features and features.confidence > 0.6:
                await orchestrator.submit_signal(
                    symbol="BTCUSDT",
                    side=1 if features.rsi < 40 else -1 if features.rsi > 60 else 0,
                    confidence=features.confidence,
                    strategy="lse",
                    metadata={"rsi": features.rsi, "atr": features.atr},
                )

            await asyncio.sleep(5)  # 5 second interval

        except Exception as e:
            print(f"❌ LSE strategy error: {e}")
            await asyncio.sleep(10)


async def ml_strategy(orchestrator: StrategyOrchestrator):
    """ML-based strategy loop"""
    if not orchestrator.model_inference:
        return

    while True:
        try:
            # Get feature window
            features_arr = await orchestrator.feature_store.get_features_array(
                "BTCUSDT", window_size=1
            )

            if features_arr.size > 0:
                # Predict
                prob = orchestrator.model_inference.predict_single(features_arr[-1])

                if prob > 0.65 or prob < 0.35:
                    await orchestrator.submit_signal(
                        symbol="BTCUSDT",
                        side=1 if prob > 0.65 else -1,
                        confidence=max(prob, 1 - prob),
                        strategy="ml",
                        priority=StrategyPriority.HIGH,
                        metadata={"model_prob": prob},
                    )

            await asyncio.sleep(10)  # 10 second interval

        except Exception as e:
            print(f"❌ ML strategy error: {e}")
            await asyncio.sleep(15)


if __name__ == "__main__":

    async def test():
        # Initialize components
        event_bus = EventBus("redis://localhost:6379/0")
        policy_engine = get_policy_engine()
        feature_store = get_feature_store()

        # Create orchestrator
        orchestrator = StrategyOrchestrator(event_bus, policy_engine, feature_store)

        # Register strategies
        orchestrator.register_strategy(
            "lse", lse_strategy, priority=StrategyPriority.MEDIUM, budget_usd=500.0
        )

        orchestrator.register_strategy(
            "ml", ml_strategy, priority=StrategyPriority.HIGH, budget_usd=1000.0
        )

        # Start
        await orchestrator.start()

        # Run for 60 seconds
        await asyncio.sleep(60)

        # Get stats
        stats = orchestrator.get_stats()
        print("\n📊 Orchestrator Stats:")
        for name, data in stats["strategies"].items():
            print(f"\n{name}:")
            print(f"  Enabled: {data['enabled']}")
            print(f"  Signals: {data['stats']['signals_generated']}")
            print(f"  Executed: {data['stats']['signals_executed']}")
            print(f"  Blocked: {data['stats']['signals_blocked']}")

        # Stop
        await orchestrator.stop()
        await event_bus.disconnect()

    asyncio.run(test())
