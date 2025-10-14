# 🔥 Epic-1: Multi-Engine Stabilization — Implementation Guide

**Sprint:** S9 — Gemma Fusion  
**Epic ID:** E1  
**Owner:** @siyahkare  
**Status:** 🚧 IN PROGRESS  
**Estimated:** 32 hours  
**Priority:** 🔴 CRITICAL

---

## 🎯 Epic Hedefi

LeviBot'u **tek-symbol bot**'tan **multi-symbol orchestrator**'a dönüştürmek.

**Başarı Kriterleri:**

- ✅ 10-15 sembol paralel ve bağımsız çalışıyor
- ✅ Engine crash'leri otomatik recover ediliyor (<10s)
- ✅ Her engine'in sağlığı real-time izleniyor
- ✅ Symbol bazlı log separation
- ✅ Uptime ≥99%

---

## 🏗️ Mimari Kararlar

### 1. Process Model: **asyncio** vs **multiprocessing**

**Karar:** 🎯 **Hybrid yaklaşım kullan**

```python
# Ana orchestrator: asyncio (I/O-bound tasks için ideal)
# Her engine: independent asyncio event loop
# Monitoring: ayrı thread (psutil checks)

┌─────────────────────────────────────────┐
│    Main Process (Orchestrator)          │
│    ├─ asyncio event loop                │
│    ├─ Health monitor thread             │
│    └─ FastAPI server (uvicorn)          │
└─────────────────────────────────────────┘
              │
      ┌───────┼───────┬───────┐
      │       │       │       │
┌─────▼─┐ ┌───▼──┐ ┌──▼───┐ ┌▼─────┐
│Engine1│ │Engine2│ │Engine3│ │...   │
│BTCUSDT│ │ETHUSDT│ │SOLUSDT│ │15x   │
└───────┘ └───────┘ └───────┘ └──────┘
```

**Neden asyncio?**

- ✅ I/O-bound tasks (API calls, websocket) için ideal
- ✅ macOS'ta multiprocessing sorunları yok
- ✅ Resource efficient (15 engine için 15 thread vs 15 process)
- ✅ Shared state kolay (Redis yine kullanılabilir ama zorunlu değil)

**Trade-off:**

- ⚠️ CPU-bound tasks (ML inference) için multiprocessing daha iyi
- **Çözüm:** ML inference'ı ayrı process pool'da çalıştır (concurrent.futures.ProcessPoolExecutor)

---

## 📁 Dosya Yapısı

```
backend/
├── src/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── manager.py              # Ana orchestrator
│   │   ├── engine.py               # Tek engine sınıfı
│   │   ├── registry.py             # Engine state tracking
│   │   ├── health_monitor.py       # Health check loop
│   │   └── recovery.py             # Crash recovery logic
│   ├── app/
│   │   └── routers/
│   │       └── engines.py          # FastAPI /engines/* endpoints
│   └── infra/
│       └── logger.py               # Symbol-specific logging
├── data/
│   ├── engine_registry.json        # Engine state persistence
│   └── logs/
│       ├── engine-BTCUSDT-20251014.jsonl
│       ├── engine-ETHUSDT-20251014.jsonl
│       └── orchestrator-20251014.jsonl
└── tests/
    ├── test_engine.py              # Unit tests
    └── test_engine_manager.py      # Integration tests
```

---

## 💻 Task 1.1: Engine Core Class

### File: `backend/src/engine/engine.py`

```python
"""
Single trading engine for one symbol.
Each engine runs independently in its own asyncio task.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EngineStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    CRASHED = "crashed"
    STOPPING = "stopping"

class TradingEngine:
    """
    Independent trading engine for a single symbol.

    Responsibilities:
    - Market data subscription (websocket)
    - Signal generation (ML model inference)
    - Order execution (paper or live)
    - PnL tracking
    - State persistence
    """

    def __init__(
        self,
        symbol: str,
        config: Dict[str, Any],
        logger: Any,  # Symbol-specific logger
    ):
        self.symbol = symbol
        self.config = config
        self.logger = logger

        self.status = EngineStatus.STOPPED
        self.start_time: Optional[float] = None
        self.last_heartbeat: Optional[float] = None
        self.error_count = 0
        self.last_error: Optional[str] = None

        # Trading state
        self.position: Optional[float] = None  # Current position size
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.trade_count: int = 0

        # Internal
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._ws_connection = None

    async def start(self) -> None:
        """Start the engine (non-blocking)."""
        if self.status != EngineStatus.STOPPED:
            raise RuntimeError(f"Engine {self.symbol} already running")

        self.status = EngineStatus.STARTING
        self.start_time = time.time()
        self.logger.info(f"Starting engine for {self.symbol}")

        # Spawn main task
        self._task = asyncio.create_task(self._run())

    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the engine gracefully."""
        if self.status == EngineStatus.STOPPED:
            return

        self.status = EngineStatus.STOPPING
        self.logger.info(f"Stopping engine for {self.symbol}")

        self._stop_event.set()

        # Wait for task to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                self.logger.warning(f"Engine {self.symbol} stop timeout, cancelling")
                self._task.cancel()

        self.status = EngineStatus.STOPPED
        self.logger.info(f"Engine {self.symbol} stopped")

    async def _run(self) -> None:
        """Main engine loop."""
        try:
            self.status = EngineStatus.RUNNING

            # Initialize components
            await self._connect_market_data()
            await self._load_state()

            # Main loop
            while not self._stop_event.is_set():
                try:
                    # Heartbeat
                    self.last_heartbeat = time.time()

                    # Trading cycle
                    await self._trading_cycle()

                    # Sleep interval (configurable)
                    await asyncio.sleep(self.config.get("cycle_interval", 1.0))

                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.logger.error(f"Error in trading cycle: {e}", exc_info=True)

                    # Exponential backoff
                    backoff = min(2 ** self.error_count, 60)
                    await asyncio.sleep(backoff)

        except Exception as e:
            self.status = EngineStatus.CRASHED
            self.last_error = str(e)
            self.logger.error(f"Engine {self.symbol} crashed: {e}", exc_info=True)

        finally:
            await self._cleanup()

    async def _trading_cycle(self) -> None:
        """One iteration of the trading logic."""
        # 1. Get latest market data
        market_data = await self._get_market_data()

        # 2. Generate signal (ML inference)
        signal = await self._generate_signal(market_data)

        # 3. Risk check
        if not self._check_risk(signal):
            return

        # 4. Execute order (if signal present)
        if signal:
            await self._execute_order(signal)

        # 5. Update state
        await self._update_state()

    async def _connect_market_data(self) -> None:
        """Connect to market data source (websocket)."""
        # TODO: Implement websocket connection
        self.logger.info(f"Connecting to market data for {self.symbol}")
        pass

    async def _get_market_data(self) -> Dict[str, Any]:
        """Get latest market data."""
        # TODO: Implement
        return {}

    async def _generate_signal(self, market_data: Dict) -> Optional[Dict]:
        """Generate trading signal using ML model."""
        # TODO: Implement ML inference
        # This should call ensemble_predictor.py
        return None

    def _check_risk(self, signal: Optional[Dict]) -> bool:
        """Check if signal passes risk filters."""
        # TODO: Implement risk checks
        return True

    async def _execute_order(self, signal: Dict) -> None:
        """Execute order based on signal."""
        # TODO: Implement order execution
        self.trade_count += 1

    async def _load_state(self) -> None:
        """Load persisted state from disk/redis."""
        # TODO: Implement
        pass

    async def _update_state(self) -> None:
        """Update and persist state."""
        # TODO: Implement
        pass

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._ws_connection:
            await self._ws_connection.close()

    def get_health(self) -> Dict[str, Any]:
        """Get engine health metrics."""
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "symbol": self.symbol,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "last_heartbeat": self.last_heartbeat,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "position": self.position,
            "daily_pnl": self.daily_pnl,
            "total_pnl": self.total_pnl,
            "trade_count": self.trade_count,
        }
```

**Checklist:**

- [ ] Engine class skeleton oluştur
- [ ] Status enum (STOPPED, RUNNING, CRASHED, etc.)
- [ ] Start/stop lifecycle methods
- [ ] Main trading cycle loop
- [ ] Health metrics getter
- [ ] Error handling & backoff
- [ ] State persistence (save/load)

---

## 💻 Task 1.2: Engine Manager (Orchestrator)

### File: `backend/src/engine/manager.py`

```python
"""
Engine manager orchestrates multiple trading engines.
Responsibilities:
- Spawn/kill engines
- Monitor health
- Crash recovery
- State persistence
"""

import asyncio
from typing import Dict, List, Optional
from .engine import TradingEngine, EngineStatus
from .registry import EngineRegistry
from .health_monitor import HealthMonitor
from .recovery import RecoveryPolicy

class EngineManager:
    """
    Manages multiple trading engines.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.engines: Dict[str, TradingEngine] = {}
        self.registry = EngineRegistry()
        self.health_monitor = HealthMonitor(self)
        self.recovery_policy = RecoveryPolicy()

        self._monitor_task: Optional[asyncio.Task] = None

    async def start_all(self, symbols: List[str]) -> None:
        """Start engines for all symbols."""
        for symbol in symbols:
            await self.start_engine(symbol)

        # Start health monitor
        self._monitor_task = asyncio.create_task(
            self.health_monitor.run()
        )

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

    async def stop_engine(self, symbol: str, timeout: float = 10.0) -> None:
        """Stop a single engine."""
        if symbol not in self.engines:
            raise ValueError(f"Engine {symbol} not found")

        engine = self.engines[symbol]
        await engine.stop(timeout)

        # Unregister
        await self.registry.unregister(symbol)
        del self.engines[symbol]

    async def stop_all(self, timeout: float = 10.0) -> None:
        """Stop all engines."""
        # Stop health monitor
        if self._monitor_task:
            self._monitor_task.cancel()

        # Stop all engines concurrently
        await asyncio.gather(
            *[self.stop_engine(symbol, timeout) for symbol in list(self.engines.keys())],
            return_exceptions=True
        )

    async def restart_engine(self, symbol: str) -> None:
        """Restart a crashed engine."""
        if symbol in self.engines:
            await self.stop_engine(symbol, timeout=5.0)

        # Wait a bit before restart
        await asyncio.sleep(1.0)

        await self.start_engine(symbol)

    def get_engine_status(self, symbol: str) -> Optional[Dict]:
        """Get status of a single engine."""
        if symbol not in self.engines:
            return None

        return self.engines[symbol].get_health()

    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get status of all engines."""
        return {
            symbol: engine.get_health()
            for symbol, engine in self.engines.items()
        }

    def get_summary(self) -> Dict:
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

    def _load_engine_config(self, symbol: str) -> Dict:
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


# Singleton instance
_manager: Optional[EngineManager] = None

def get_engine_manager() -> EngineManager:
    """Get global engine manager instance."""
    global _manager
    if _manager is None:
        raise RuntimeError("Engine manager not initialized")
    return _manager

def init_engine_manager(config: Dict) -> EngineManager:
    """Initialize global engine manager."""
    global _manager
    _manager = EngineManager(config)
    return _manager
```

**Checklist:**

- [ ] EngineManager class skeleton
- [ ] start_all() / stop_all()
- [ ] start_engine() / stop_engine() / restart_engine()
- [ ] get_all_statuses() / get_summary()
- [ ] Config loading per symbol
- [ ] Singleton pattern (global instance)

---

## 💻 Task 1.3: Health Monitor

### File: `backend/src/engine/health_monitor.py`

```python
"""
Health monitor watches all engines and triggers recovery.
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

    def __init__(self, manager: 'EngineManager'):
        self.manager = manager
        self.check_interval = 30.0  # seconds
        self.heartbeat_timeout = 60.0  # seconds

    async def run(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._check_all_engines()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health monitor error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_engines(self) -> None:
        """Check health of all engines."""
        now = time.time()

        for symbol, engine in self.manager.engines.items():
            health = engine.get_health()

            # Check 1: Status crashed
            if health["status"] == "crashed":
                await self._handle_crash(symbol, health)

            # Check 2: Heartbeat timeout
            elif health["last_heartbeat"]:
                age = now - health["last_heartbeat"]
                if age > self.heartbeat_timeout:
                    await self._handle_timeout(symbol, health)

            # Check 3: Too many errors
            elif health["error_count"] > 10:
                await self._handle_error_spike(symbol, health)

    async def _handle_crash(self, symbol: str, health: Dict) -> None:
        """Handle crashed engine."""
        print(f"⚠️ Engine {symbol} crashed: {health['last_error']}")

        # Check if recovery allowed
        if self.manager.recovery_policy.should_recover(symbol):
            print(f"🔄 Attempting recovery for {symbol}")
            await self.manager.restart_engine(symbol)
        else:
            print(f"❌ Max recovery attempts reached for {symbol}")
            # Send alert (Telegram, Slack, etc.)

    async def _handle_timeout(self, symbol: str, health: Dict) -> None:
        """Handle heartbeat timeout."""
        print(f"⚠️ Engine {symbol} heartbeat timeout")

        # Force restart
        await self.manager.restart_engine(symbol)

    async def _handle_error_spike(self, symbol: str, health: Dict) -> None:
        """Handle error spike."""
        print(f"⚠️ Engine {symbol} error spike: {health['error_count']}")

        # Restart and reset error count
        await self.manager.restart_engine(symbol)
```

**Checklist:**

- [ ] HealthMonitor class
- [ ] run() loop (30s interval)
- [ ] Check crashed engines
- [ ] Check heartbeat timeout
- [ ] Check error spike
- [ ] Trigger recovery (call manager.restart_engine)

---

## 💻 Task 1.4: Recovery Policy

### File: `backend/src/engine/recovery.py`

```python
"""
Recovery policy determines when/how to recover crashed engines.
"""

import time
from typing import Dict

class RecoveryPolicy:
    """
    Determines recovery behavior for crashed engines.

    Rules:
    - Max 5 restarts per engine per hour
    - Exponential backoff between restarts
    """

    def __init__(self):
        # Track restart attempts: {symbol: [timestamp, timestamp, ...]}
        self.restart_history: Dict[str, list] = {}
        self.max_restarts_per_hour = 5
        self.backoff_base = 60  # seconds

    def should_recover(self, symbol: str) -> bool:
        """Check if engine should be recovered."""
        now = time.time()
        one_hour_ago = now - 3600

        # Get restart history for this symbol
        if symbol not in self.restart_history:
            self.restart_history[symbol] = []

        # Filter out old restarts
        recent_restarts = [
            ts for ts in self.restart_history[symbol]
            if ts > one_hour_ago
        ]
        self.restart_history[symbol] = recent_restarts

        # Check limit
        if len(recent_restarts) >= self.max_restarts_per_hour:
            return False

        # Check backoff
        if recent_restarts:
            last_restart = recent_restarts[-1]
            attempts = len(recent_restarts)
            min_wait = self.backoff_base * (2 ** (attempts - 1))

            if now - last_restart < min_wait:
                return False

        # Record this restart
        self.restart_history[symbol].append(now)
        return True

    def reset(self, symbol: str) -> None:
        """Reset restart history for a symbol."""
        if symbol in self.restart_history:
            del self.restart_history[symbol]
```

**Checklist:**

- [ ] RecoveryPolicy class
- [ ] should_recover() logic
- [ ] Max 5 restarts/hour per engine
- [ ] Exponential backoff
- [ ] Restart history tracking

---

## 💻 Task 1.5: Engine Registry (State Persistence)

### File: `backend/src/engine/registry.py`

```python
"""
Engine registry tracks engine state and persists to disk.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Optional

class EngineRegistry:
    """
    Tracks engine state and persists to JSON.
    """

    def __init__(self, registry_path: str = "backend/data/engine_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.state: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()

        # Load existing state
        self._load()

    def _load(self) -> None:
        """Load registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self.state = json.load(f)

    def _save(self) -> None:
        """Save registry to disk."""
        with open(self.registry_path, "w") as f:
            json.dump(self.state, f, indent=2)

    async def register(self, symbol: str, health: Dict) -> None:
        """Register a new engine."""
        async with self._lock:
            self.state[symbol] = {
                "symbol": symbol,
                "status": health["status"],
                "registered_at": health.get("start_time"),
                **health
            }
            self._save()

    async def unregister(self, symbol: str) -> None:
        """Unregister an engine."""
        async with self._lock:
            if symbol in self.state:
                del self.state[symbol]
                self._save()

    async def update(self, symbol: str, health: Dict) -> None:
        """Update engine state."""
        async with self._lock:
            if symbol in self.state:
                self.state[symbol].update(health)
                self._save()

    def get(self, symbol: str) -> Optional[Dict]:
        """Get engine state."""
        return self.state.get(symbol)

    def get_all(self) -> Dict[str, Dict]:
        """Get all engine states."""
        return self.state.copy()
```

**Checklist:**

- [ ] EngineRegistry class
- [ ] Load/save JSON
- [ ] register() / unregister() / update()
- [ ] Thread-safe (async lock)
- [ ] Auto-create data directory

---

## 💻 Task 1.6: FastAPI Endpoints

### File: `backend/src/app/routers/engines.py`

```python
"""
FastAPI endpoints for engine management.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from ...engine.manager import get_engine_manager

router = APIRouter(prefix="/engines", tags=["engines"])

@router.get("/status")
async def get_all_engine_status() -> Dict:
    """
    Get status of all engines.

    Returns:
    {
      "total": 12,
      "running": 11,
      "crashed": 1,
      "engines": [...]
    }
    """
    manager = get_engine_manager()
    return manager.get_summary()

@router.get("/status/{symbol}")
async def get_engine_status(symbol: str) -> Dict:
    """Get status of a single engine."""
    manager = get_engine_manager()
    status = manager.get_engine_status(symbol)

    if status is None:
        raise HTTPException(404, f"Engine {symbol} not found")

    return status

@router.post("/start/{symbol}")
async def start_engine(symbol: str) -> Dict:
    """Start an engine."""
    manager = get_engine_manager()

    try:
        await manager.start_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "started"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/stop/{symbol}")
async def stop_engine(symbol: str) -> Dict:
    """Stop an engine."""
    manager = get_engine_manager()

    try:
        await manager.stop_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "stopped"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/restart/{symbol}")
async def restart_engine(symbol: str) -> Dict:
    """Restart an engine."""
    manager = get_engine_manager()

    try:
        await manager.restart_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "restarted"}
    except Exception as e:
        raise HTTPException(500, str(e))
```

**Checklist:**

- [ ] GET /engines/status (all engines)
- [ ] GET /engines/status/{symbol} (single)
- [ ] POST /engines/start/{symbol}
- [ ] POST /engines/stop/{symbol}
- [ ] POST /engines/restart/{symbol}

---

## 💻 Task 1.7: Symbol-Specific Logging

### File: `backend/src/infra/logger.py` (enhance existing)

```python
"""
Symbol-specific logging.
"""

import logging
from pathlib import Path
from datetime import datetime

def get_engine_logger(symbol: str) -> logging.Logger:
    """
    Get a logger for a specific symbol.

    Logs to: backend/data/logs/engine-{symbol}-{date}.jsonl
    """
    log_dir = Path("backend/data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"engine-{symbol}-{date_str}.jsonl"

    logger = logging.getLogger(f"engine.{symbol}")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
        )
        logger.addHandler(handler)

    return logger
```

**Checklist:**

- [ ] get_engine_logger(symbol) function
- [ ] Log to `engine-{symbol}-{date}.jsonl`
- [ ] JSON format
- [ ] Daily rotation (implicit via date in filename)

---

## 🧪 Testing Strategy

### Unit Tests: `backend/tests/test_engine.py`

```python
import pytest
import asyncio
from backend.src.engine.engine import TradingEngine, EngineStatus

@pytest.mark.asyncio
async def test_engine_lifecycle():
    """Test engine start/stop lifecycle."""
    config = {"cycle_interval": 0.1}
    logger = logging.getLogger("test")

    engine = TradingEngine("TESTUSDT", config, logger)

    # Initially stopped
    assert engine.status == EngineStatus.STOPPED

    # Start
    await engine.start()
    await asyncio.sleep(0.2)
    assert engine.status == EngineStatus.RUNNING

    # Stop
    await engine.stop()
    assert engine.status == EngineStatus.STOPPED

@pytest.mark.asyncio
async def test_engine_health():
    """Test health metrics."""
    engine = TradingEngine("TESTUSDT", {}, logging.getLogger("test"))
    await engine.start()
    await asyncio.sleep(0.5)

    health = engine.get_health()
    assert health["symbol"] == "TESTUSDT"
    assert health["status"] == "running"
    assert health["uptime_seconds"] > 0

    await engine.stop()
```

### Integration Tests: `backend/tests/test_engine_manager.py`

```python
@pytest.mark.asyncio
async def test_manager_multi_engine():
    """Test manager with multiple engines."""
    config = {"engine_defaults": {"cycle_interval": 0.1}}
    manager = EngineManager(config)

    await manager.start_all(["BTC/USDT", "ETH/USDT", "SOL/USDT"])

    await asyncio.sleep(1.0)

    summary = manager.get_summary()
    assert summary["total"] == 3
    assert summary["running"] == 3

    await manager.stop_all()

@pytest.mark.asyncio
async def test_crash_recovery():
    """Test automatic crash recovery."""
    manager = EngineManager({})
    await manager.start_engine("TEST/USDT")

    # Simulate crash
    manager.engines["TEST/USDT"].status = EngineStatus.CRASHED

    # Health monitor should detect and restart
    await asyncio.sleep(35)  # Wait for monitor cycle

    status = manager.get_engine_status("TEST/USDT")
    assert status["status"] == "running"

    await manager.stop_all()
```

**Checklist:**

- [ ] test_engine_lifecycle (start/stop)
- [ ] test_engine_health (metrics)
- [ ] test_manager_multi_engine (3+ engines)
- [ ] test_crash_recovery (auto-restart)
- [ ] test_recovery_policy (max restarts)

---

## 📊 Success Metrics

| Metrik                 | Hedef  | Test Yöntemi                          |
| ---------------------- | ------ | ------------------------------------- |
| **Engine uptime**      | ≥99%   | 24h soak test, 15 engines             |
| **Crash recovery**     | <10s   | Simulate crash, measure restart time  |
| **Concurrent engines** | 15+    | Start 15 engines, check CPU/memory    |
| **API latency**        | <100ms | Load test /engines/status (100 req/s) |
| **Log separation**     | 100%   | Verify 15 separate log files          |

---

## 🔄 Integration with Existing Code

### 1. Main App Startup

```python
# backend/src/app/main.py

from contextlib import asynccontextmanager
from .engine.manager import init_engine_manager, get_engine_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config = load_config()  # Your existing config
    manager = init_engine_manager(config)

    # Start all engines
    symbols = config.get("symbols_to_trade", ["BTCUSDT", "ETHUSDT"])
    await manager.start_all(symbols)

    yield

    # Shutdown
    await manager.stop_all()

app = FastAPI(lifespan=lifespan)
```

### 2. Router Registration

```python
# backend/src/app/main.py

from .routers.engines import router as engines_router

app.include_router(engines_router)
```

---

## 🚀 Implementation Order

**Week 1 (14-18 Ekim):**

| Day | Tasks                             | Hours |
| --- | --------------------------------- | ----- |
| Mon | Task 1.1 (Engine class skeleton)  | 4h    |
| Mon | Task 1.2 (Manager class skeleton) | 4h    |
| Tue | Task 1.3 (Health monitor)         | 4h    |
| Tue | Task 1.4 (Recovery policy)        | 2h    |
| Wed | Task 1.5 (Registry)               | 2h    |
| Wed | Task 1.6 (FastAPI endpoints)      | 4h    |
| Thu | Task 1.7 (Logging)                | 2h    |
| Thu | Integration testing               | 4h    |
| Fri | End-to-end test (15 engines)      | 4h    |
| Fri | Bug fixes & polish                | 2h    |

**Total:** 32 hours

---

## 🎯 Definition of Done

Epic-1 tamamlanmış sayılır eğer:

- [ ] `engine.py`, `manager.py`, `health_monitor.py`, `recovery.py`, `registry.py` complete
- [ ] FastAPI endpoints çalışıyor (`/engines/status`, etc.)
- [ ] Symbol-specific logging aktif
- [ ] Unit tests ≥80% coverage
- [ ] Integration tests passing (15 engines)
- [ ] 24h soak test başarılı (≥99% uptime)
- [ ] Documentation complete (bu dosya + docstrings)
- [ ] Code review tamamlandı
- [ ] Merged to `develop` branch

---

## 🔗 Referanslar

- [S9_GEMMA_FUSION_PLAN.md](./S9_GEMMA_FUSION_PLAN.md) - Ana sprint planı
- [S9_TASKS.yaml](./S9_TASKS.yaml) - Görev listesi
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Sistem mimarisi

---

**Hazırlayan:** @siyahkare  
**Tarih:** 13 Ekim 2025  
**Epic:** E1 — Multi-Engine Stabilization  
**Sprint:** S9 — Gemma Fusion

---

**🔥 Şimdi kod yazmaya başlayabiliriz!**
