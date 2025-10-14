"""
Engine registry for state persistence.
"""

import asyncio
import json
from pathlib import Path


class EngineRegistry:
    """
    Tracks engine state and persists to JSON.
    
    Thread-safe via async lock.
    """
    
    def __init__(self, registry_path: str = "data/engine_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.state: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        
        # Load existing state
        self._load()
    
    def _load(self) -> None:
        """Load registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    self.state = json.load(f)
                print(f"✅ Loaded engine registry: {len(self.state)} engines")
            except Exception as e:
                print(f"⚠️ Error loading registry: {e}")
                self.state = {}
    
    def _save(self) -> None:
        """Save registry to disk."""
        try:
            with open(self.registry_path, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving registry: {e}")
    
    async def register(self, symbol: str, health: dict) -> None:
        """Register a new engine."""
        async with self._lock:
            self.state[symbol] = {
                "symbol": symbol,
                "registered_at": health.get("start_time"),
                **health,
            }
            self._save()
    
    async def unregister(self, symbol: str) -> None:
        """Unregister an engine."""
        async with self._lock:
            if symbol in self.state:
                del self.state[symbol]
                self._save()
    
    async def update(self, symbol: str, health: dict) -> None:
        """Update engine state."""
        async with self._lock:
            if symbol in self.state:
                self.state[symbol].update(health)
                self._save()
    
    def get(self, symbol: str) -> dict | None:
        """Get engine state."""
        return self.state.get(symbol)
    
    def get_all(self) -> dict[str, dict]:
        """Get all engine states."""
        return dict(self.state)

