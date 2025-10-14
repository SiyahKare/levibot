"""
Engine manager orchestrates multiple trading engines.
"""

import asyncio

from .engine import TradingEngine
from .health_monitor import HealthMonitor
from .recovery import RecoveryPolicy
from .registry import EngineRegistry


class EngineManager:
    """
    Manages multiple trading engines.
    
    Responsibilities:
    - Spawn/kill engines
    - Monitor health
    - Crash recovery
    - State persistence
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.engines: dict[str, TradingEngine] = {}
        
        # Components
        self.registry = EngineRegistry()
        self.recovery_policy = RecoveryPolicy()
        self.health_monitor = HealthMonitor(self)
        
        self._monitor_task: asyncio.Task | None = None
    
    async def start_all(self, symbols: list[str]) -> None:
        """Start engines for all symbols."""
        print(f"🚀 Starting {len(symbols)} engines...")
        
        for symbol in symbols:
            try:
                await self.start_engine(symbol)
            except Exception as e:
                print(f"❌ Failed to start engine {symbol}: {e}")
        
        # Start health monitor
        self._monitor_task = asyncio.create_task(self.health_monitor.run())
        
        print(f"✅ Started {len(self.engines)}/{len(symbols)} engines")
    
    async def start_engine(self, symbol: str) -> None:
        """Start a single engine."""
        if symbol in self.engines:
            raise ValueError(f"Engine {symbol} already exists")
        
        # Load config for this symbol
        engine_config = self._load_engine_config(symbol)
        
        # Create logger
        logger = self._create_logger(symbol)
        
        # Create and start engine
        engine = TradingEngine(symbol, engine_config, logger)
        self.engines[symbol] = engine
        
        await engine.start()
        
        # Register in registry
        await self.registry.register(symbol, engine.get_health())
        
        print(f"✅ Engine {symbol} started")
    
    async def stop_engine(self, symbol: str, timeout: float = 10.0) -> None:
        """Stop a single engine."""
        if symbol not in self.engines:
            print(f"⚠️ Engine {symbol} not found")
            return
        
        engine = self.engines[symbol]
        await engine.stop(timeout)
        
        # Unregister
        await self.registry.unregister(symbol)
        del self.engines[symbol]
        
        print(f"🛑 Engine {symbol} stopped")
    
    async def stop_all(self, timeout: float = 10.0) -> None:
        """Stop all engines."""
        print(f"🛑 Stopping {len(self.engines)} engines...")
        
        # Stop health monitor
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all engines concurrently
        await asyncio.gather(
            *[self.stop_engine(symbol, timeout) for symbol in list(self.engines.keys())],
            return_exceptions=True
        )
        
        print("✅ All engines stopped")
    
    async def restart_engine(self, symbol: str) -> None:
        """Restart a crashed engine."""
        print(f"🔄 Restarting engine {symbol}...")
        
        # Stop if running
        if symbol in self.engines:
            await self.stop_engine(symbol, timeout=5.0)
        
        # Wait a bit before restart
        await asyncio.sleep(1.0)
        
        # Start
        await self.start_engine(symbol)
    
    def get_engine_status(self, symbol: str) -> dict | None:
        """Get status of a single engine."""
        engine = self.engines.get(symbol)
        return engine.get_health() if engine else None
    
    def get_all_statuses(self) -> dict[str, dict]:
        """Get status of all engines."""
        return {
            symbol: engine.get_health()
            for symbol, engine in self.engines.items()
        }
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        statuses = self.get_all_statuses()
        
        total = len(statuses)
        running = sum(1 for s in statuses.values() if s["status"] == "running")
        crashed = sum(1 for s in statuses.values() if s["status"] == "crashed")
        stopped = sum(1 for s in statuses.values() if s["status"] == "stopped")
        
        return {
            "total": total,
            "running": running,
            "crashed": crashed,
            "stopped": stopped,
            "engines": list(statuses.values())
        }
    
    def _load_engine_config(self, symbol: str) -> dict:
        """Load config for a specific symbol."""
        # Default config
        base_config = self.config.get("engine_defaults", {})
        
        # Symbol-specific overrides
        symbol_config = self.config.get("symbols", {}).get(symbol, {})
        
        return {**base_config, **symbol_config}
    
    def _create_logger(self, symbol: str):
        """Create symbol-specific logger."""
        from ..infra.logger import get_engine_logger
        return get_engine_logger(symbol)


# ========== Singleton Instance ==========

_manager: EngineManager | None = None


def init_engine_manager(config: dict) -> EngineManager:
    """Initialize global engine manager."""
    global _manager
    _manager = EngineManager(config)
    return _manager


def get_engine_manager() -> EngineManager:
    """Get global engine manager instance."""
    if _manager is None:
        raise RuntimeError("Engine manager not initialized. Call init_engine_manager() first.")
    return _manager

