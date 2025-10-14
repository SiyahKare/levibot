"""
Health monitor for trading engines.
"""

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import EngineManager


class HealthMonitor:
    """
    Periodically checks engine health and triggers recovery.
    """

    def __init__(
        self,
        manager: "EngineManager",
        check_interval: float = 30.0,
        heartbeat_timeout: float = 60.0,
    ):
        self.manager = manager
        self.check_interval = check_interval
        self.heartbeat_timeout = heartbeat_timeout

    async def run(self) -> None:
        """Main monitoring loop."""
        print(f"🏥 Health monitor started (interval={self.check_interval}s)")

        while True:
            try:
                await self._check_all_engines()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                print("🏥 Health monitor stopped")
                break
            except Exception as e:
                print(f"⚠️ Health monitor error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_engines(self) -> None:
        """Check health of all engines."""
        now = time.time()

        for symbol, engine in self.manager.engines.items():
            try:
                health = engine.get_health()

                # Check 1: Status crashed
                if health["status"] == "crashed":
                    await self._handle_crash(symbol, health)

                # Check 2: Heartbeat timeout
                elif health["last_heartbeat"]:
                    heartbeat_age = now - health["last_heartbeat"]
                    if heartbeat_age > self.heartbeat_timeout:
                        await self._handle_timeout(symbol, health, heartbeat_age)

                # Check 3: Too many errors
                elif health["error_count"] > 10:
                    await self._handle_error_spike(symbol, health)

            except Exception as e:
                print(f"⚠️ Error checking {symbol}: {e}")

    async def _handle_crash(self, symbol: str, health: dict) -> None:
        """Handle crashed engine."""
        print(f"💥 Engine {symbol} crashed: {health.get('last_error', 'unknown')}")

        # Check if recovery allowed
        if self.manager.recovery_policy.should_recover(symbol):
            print(f"🔄 Attempting recovery for {symbol}")
            try:
                await self.manager.restart_engine(symbol)
                print(f"✅ Recovery successful for {symbol}")
            except Exception as e:
                print(f"❌ Recovery failed for {symbol}: {e}")
        else:
            print(f"❌ Max recovery attempts reached for {symbol}")
            # TODO: Send alert (Telegram, Slack, etc.)

    async def _handle_timeout(
        self, symbol: str, health: dict, heartbeat_age: float
    ) -> None:
        """Handle heartbeat timeout."""
        print(f"💔 Engine {symbol} heartbeat timeout ({int(heartbeat_age)}s)")

        try:
            await self.manager.restart_engine(symbol)
            print(f"✅ Restarted {symbol} after timeout")
        except Exception as e:
            print(f"❌ Failed to restart {symbol}: {e}")

    async def _handle_error_spike(self, symbol: str, health: dict) -> None:
        """Handle error spike."""
        error_count = health["error_count"]
        print(f"⚠️ Engine {symbol} error spike: {error_count} errors")

        try:
            await self.manager.restart_engine(symbol)
            print(f"✅ Restarted {symbol} after error spike")
        except Exception as e:
            print(f"❌ Failed to restart {symbol}: {e}")
